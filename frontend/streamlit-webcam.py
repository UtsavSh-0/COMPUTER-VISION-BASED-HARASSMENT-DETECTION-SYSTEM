import streamlit as st
import cv2
import requests
from PIL import Image
import io
import os
import av
import threading
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration

st.set_page_config(page_title="Real Time Threat Detection", layout="wide")
st.title("Live Webcam Threat Detection")
st.write("This app captures live webcam feed and sends frames to the fusion layer API for threat detection.")
st.write("Click 'START' to start the webcam, and ALLOW camera access when prompted by the browser.")

@st.cache_resource
def get_ice_servers():
    # Use Twilio's TURN server to allow WebRTC streams over Cloudflare (which blocks UDP.
    try:
        from twilio.rest import Client
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        if account_sid and auth_token:
            client = Client(account_sid, auth_token)
            token = client.tokens.create()
            return token.ice_servers
    except Exception as e:
        print("Twilio TURN server error:", e)
        
    return [{"urls": ["stun:stun.l.google.com:19302"]}]

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": get_ice_servers()}
)

class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.frame_skip = 5
        self.frame_count = 0
        self.latest_boxes = []
        self.api_thread = None
        self.result_container = {"result": None, "error": False, "new_data": False}
        self.api_url = os.environ.get("API_URL", "http://localhost:8000/predict")

    def fetch_api(self, file_bytes):
        try:
            files = {"file": ("frame.jpg", file_bytes, "image/jpeg")}
            response = requests.post(self.api_url, files=files, timeout=2.0)
            if response.status_code == 200:
                self.result_container["result"] = response.json()
                self.result_container["error"] = False
                self.result_container["new_data"] = True
        except Exception:
            self.result_container["error"] = True
            self.result_container["new_data"] = True

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        
        result = self.result_container.get("result", {})
        if result:
            self.latest_boxes = result.get("weapon_boxes", [])
            decision = result.get("fusion_decision", "Unknown")
            weapon_conf = result.get("weapon_conf", 0.0)
            violence_conf = result.get("violence_conf", 0.0)
            anomaly_score = result.get("anomaly_score", 0.0)
            
            # Draw metrics on the top left
            cv2.putText(img, f"Status: {decision}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3)
            # Adjust color based on decision
            status_color = (0, 255, 0)
            if "Warning" in decision: status_color = (0, 255, 255)
            elif "Critical" in decision or "Threat" in decision: status_color = (0, 0, 255)
            
            cv2.putText(img, f"Status: {decision}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Weapon, Violence, Anomaly confidences
            cv2.putText(img, f"Weapon Conf: {weapon_conf:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
            cv2.putText(img, f"Weapon Conf: {weapon_conf:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.putText(img, f"Violence Conf: {violence_conf:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
            cv2.putText(img, f"Violence Conf: {violence_conf:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.putText(img, f"Anomaly Score: {anomaly_score:.2f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
            cv2.putText(img, f"Anomaly Score: {anomaly_score:.2f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw bounding boxes
        for box in self.latest_boxes:
            x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
            conf = box['conf']
            class_name = box.get('class_name', 'Weapon').capitalize()
            # BGR format: green is (0, 255, 0), red is (0, 0, 255)
            color = (0, 255, 0) if class_name.lower() == 'person' else (0, 0, 255)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, f"{class_name}: {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        if self.frame_count % self.frame_skip == 0:
            if self.api_thread is None or not self.api_thread.is_alive():
                # Convert BGR to RGB for API
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG")
                file_bytes = buf.getvalue()
                
                self.api_thread = threading.Thread(target=self.fetch_api, args=(file_bytes,))
                self.api_thread.start()
                
        self.frame_count += 1
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

st.write("---")
# Provide a centered column for the webcam
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    webrtc_streamer(
        key="webcam",
        video_processor_factory=VideoProcessor,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True
    )
    
st.markdown("""
<style>
/* Optional styling to make webcam frame look better */
#root > div:nth-child(1) > div > div > div > div > section > div {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)
