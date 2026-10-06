import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import io
import cv2
from ultralytics import YOLO
import tempfile
import os
from download_models import download_models

# Ensure models are present before startup
download_models()

app = FastAPI()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Robust path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load Weapons detection model (YOLOv8 trained on weapon detection cctv v3 dataset.v1-weapon_detection_in_cctv.yolov8 from roboflow)
weapon_model = YOLO(os.path.join(BASE_DIR, "models/weapon-detection-model-mark2.pt"))

# OR

# Load Weapons detection model (YOLOv8 trained on simuletic weapon detection dataset)
#weapon_model = YOLO("models/weapon-detection-model-simuletic.pt")

# Load Violence detection model (SlowFast)
violence_model = torch.hub.load('facebookresearch/pytorchvideo', 'slowfast_r50', pretrained=False)
violence_model.blocks[-1].proj = nn.Linear(violence_model.blocks[-1].proj.in_features, 3)
violence_model.load_state_dict(torch.load(os.path.join(BASE_DIR, "models/violence-detection-slowfast-model.pth"), map_location=device, weights_only=False))
violence_model.eval().to(device)

# Load I3D feature extractor for anomaly detection
i3d = torch.hub.load('facebookresearch/pytorchvideo', 'i3d_r50', pretrained=True)
i3d.blocks[-1].proj = nn.Identity()  # remove classifier head
i3d = i3d.to(device)
i3d.eval()

# Define Autoencoder for Anomaly detection
class Autoencoder(nn.Module):
    def __init__(self, input_dim=2048, hidden_dim=512):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim//2),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim//2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)

# Load Anomaly detection model (Autoencoder)
anomaly_model = Autoencoder().to(device)
anomaly_model.load_state_dict(torch.load(os.path.join(BASE_DIR, "models/anamoly-detection-model-epoch10.pth"), map_location=device, weights_only=False))
anomaly_model.eval()

# Preprocessing
transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.45,0.45,0.45], std=[0.225,0.225,0.225])
])

# For images: fake temporal dimension
def preprocess_image(contents, num_frames=8):
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    frame = transform(image)  # (3, H, W)
    clip = frame.unsqueeze(1).repeat(1, num_frames, 1, 1)  # (3, T, H, W)
    return clip.unsqueeze(0).to(device)  # (1, 3, T, H, W)

# For videos: extract frames
def extract_frames(video_bytes, ext="mp4", num_frames=16, apply_transform=True, max_dim=320):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise ValueError(f"Video file {tmp_path} could not be opened. Check codec/extension.")

        frames = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(total_frames // num_frames, 1)

        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize frame early to save memory and speed up subsequent steps
            h, w = frame.shape[:2]
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame)
            
            if apply_transform:
                frames.append(transform(pil_img))
            else:
                frames.append(pil_img)
                
            if len(frames) >= num_frames:
                break
    finally:
        cap.release()
        try:
            os.remove(tmp_path)
        except:
            pass

    if not frames:
        raise ValueError("No frames extracted from video")

    if apply_transform:
        return torch.stack(frames)  # (T, C, H, W)
    else:
        return frames  # list of PIL Images

def create_slowfast_inputs(frames, alpha=4):
    # frames: (T, C, H, W)
    fast_pathway = frames.permute(1,0,2,3)  # (C, T, H, W)
    slow_pathway = torch.index_select(frames, 0, torch.arange(0, frames.shape[0], alpha))
    slow_pathway = slow_pathway.permute(1,0,2,3)  # (C, T/alpha, H, W)
    return [slow_pathway.unsqueeze(0).to(device), fast_pathway.unsqueeze(0).to(device)]

# Inference Functions
def run_weapon_model(file_bytes):
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    results = weapon_model(image, device="cpu", imgsz=320)
    
    boxes_data = []
    weapon_confs = []
    for box in results[0].boxes:
        conf = box.conf.item()
        cls_id = int(box.cls.item())
        class_name = weapon_model.names.get(cls_id, "unknown")
        
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        boxes_data.append({
            "x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2), 
            "conf": conf,
            "class_name": class_name
        })
        
        # Only aggregate confidence if it's not a person
        if class_name != "person":
            weapon_confs.append(conf)
            
    return (max(weapon_confs) if weapon_confs else 0.0, boxes_data)

def run_weapon_model_video(frames):
    weapon_confs = []
    results = weapon_model(frames, device="cpu", imgsz=320)
    for res in results:
        for box in res.boxes:
            cls_id = int(box.cls.item())
            class_name = weapon_model.names.get(cls_id, "unknown")
            if class_name != "person":
                weapon_confs.append(box.conf.item())
    return max(weapon_confs) if weapon_confs else 0.0

def run_violence_model_video(frames):
    transformed_frames = torch.stack([transform(img) for img in frames])
    inputs = create_slowfast_inputs(transformed_frames)
    with torch.no_grad():
        logits = violence_model(inputs)
        probs = torch.softmax(logits, dim=1)
    return probs[0,1].item()

def run_anomaly_model(tensor):
    with torch.no_grad():
        features = i3d(tensor)              # (1, 2048)
        features = features.view(features.size(0), -1)
        outputs = anomaly_model(features)
        loss = torch.mean((outputs - features)**2, dim=1)
    return loss.item()

def run_anomaly_model_video(frames):
    transformed_frames = torch.stack([transform(img) for img in frames])
    clip = transformed_frames.permute(1,0,2,3).unsqueeze(0).to(device)  # (1, C, T, H, W)
    with torch.no_grad():
        features = i3d(clip)
        features = features.view(features.size(0), -1)
        outputs = anomaly_model(features)
        loss = torch.mean((outputs - features)**2, dim=1)
    return loss.item()

# Rule-based fusion
def fusion_rule(weapon_conf, violence_conf, anomaly_score,
                weapon_thresh=0.5, weapon_warning_low=0.2,
                violence_thresh=0.5, violence_warning_low=0.2,
                anomaly_thresh=0.5, anomaly_warning_low=0.2):
    if weapon_conf >= weapon_thresh:
        return "Weapon detected!"
    elif weapon_conf >= weapon_warning_low:
        return "Warning: Possible Weapon"
    elif violence_conf >= violence_thresh:
        return "Violence detected!"
    elif violence_conf >= violence_warning_low:
        return "Warning: Possible Violence"
    elif anomaly_score >= anomaly_thresh:
        return "Anomaly detected!"
    elif anomaly_score >= anomaly_warning_low:
        return "Warning: Possible Anomaly"
    else:
        return "Safe"

class FusionResponse(BaseModel):
    weapon_conf: float
    violence_conf: float
    anomaly_score: float
    fusion_decision: str
    weapon_boxes: list = []

# API Endpoint
executor = ThreadPoolExecutor(max_workers=3)

@app.post("/predict", response_model=FusionResponse)
async def predict(file: UploadFile):
    try:
        contents = await file.read()

        filename = file.filename.lower() if file.filename else "temp.mp4"
        ext = filename.split(".")[-1]

        if filename.endswith((".mp4", ".avi", ".mov")):
            loop = asyncio.get_event_loop()
            
            # Extract 16 frames once
            frames = await loop.run_in_executor(
                executor, extract_frames, contents, ext, 16, False
            )
            
            # Run inference concurrently
            weapon_task = loop.run_in_executor(executor, run_weapon_model_video, frames)
            violence_task = loop.run_in_executor(executor, run_violence_model_video, frames)
            anomaly_task = loop.run_in_executor(executor, run_anomaly_model_video, frames)
            
            weapon_conf, violence_conf, anomaly_score = await asyncio.gather(
                weapon_task, violence_task, anomaly_task
            )
            weapon_boxes = [] # Currently video returns a single max conf over frames
        else:
            tensor = preprocess_image(contents)
            weapon_conf, weapon_boxes = run_weapon_model(contents)
            violence_conf = 0.0
            anomaly_score = run_anomaly_model(tensor)


        decision = fusion_rule(weapon_conf, violence_conf, anomaly_score)

        return FusionResponse(
            weapon_conf=weapon_conf,
            violence_conf=violence_conf,
            anomaly_score=anomaly_score,
            fusion_decision=decision,
            weapon_boxes=weapon_boxes
        )
    except Exception as e:
        return FusionResponse(
            weapon_conf=0.0,
            violence_conf=0.0,
            anomaly_score=0.0,
            fusion_decision=f"Error: {str(e)}",
            weapon_boxes=[]
        )
