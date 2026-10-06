import streamlit as st
import requests
from PIL import Image
import cv2
import numpy as np

st.title("CCTV Threat Detection Fusion Layer")

uploaded_file = st.file_uploader("Upload a video/frame", type=["mp4","avi","png","jpg","jpeg"])

if uploaded_file:
    if uploaded_file.type.startswith("video"):
        st.video(uploaded_file)
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Frame", width=600)

    if st.button("Run Detection"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        import os
        api_url = os.environ.get("API_URL", "http://localhost:8000/predict")
        response = requests.post(api_url, files=files)

        try:
            result = response.json()
        except Exception:
            st.error("API did not return valid JSON. Check FastAPI logs for details.")
            st.stop()

        decision = result.get("fusion_decision", "Unknown")
        weapon_boxes = result.get("weapon_boxes", [])

        st.subheader("Fusion Results")
        
        # If it's an image and we have boxes, draw them
        if weapon_boxes and not uploaded_file.type.startswith("video"):
            # Ensure file pointer is at the start
            uploaded_file.seek(0)
            image_cv = np.array(Image.open(uploaded_file).convert("RGB"))
            
            for box in weapon_boxes:
                x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
                conf = box['conf']
                class_name = box.get('class_name', 'Weapon').capitalize()
                
                # Draw red rectangle for weapon, green for person
                color = (0, 255, 0) if class_name.lower() == 'person' else (255, 0, 0)
                
                cv2.rectangle(image_cv, (x1, y1), (x2, y2), color, 2)
                cv2.putText(image_cv, f"{class_name}: {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                            
            st.image(image_cv, caption="Detections on Frame", width=600)
            
        st.write("Weapon Confidence:", result["weapon_conf"])
        st.progress(int(result["weapon_conf"] * 100))
        st.write("Violence Confidence:", result["violence_conf"])
        st.progress(int(result["violence_conf"] * 100))
        st.write("Anomaly Score:", result["anomaly_score"])
        st.progress(int(result["anomaly_score"] * 100))

        # Color-coded badge
        if "Safe" in decision:
            st.success(f"{decision}")
        elif "Warning" in decision:
            st.warning(f"{decision}")
        else:
            st.error(f"{decision}")
