# CCTV Threat Detection

![Python](https://img.shields.io/badge/python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Object%20Detection-blueviolet)
![Docker](https://img.shields.io/badge/Docker-Containerization-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

## Overview

An intelligent end-to-end computer vision pipeline designed to analyze CCTV video feeds in real-time. By combining multiple AI models, the system automatically detects potential security threats such as drawn weapons, physical violence, and unusual activities, instantly flagging dangers and presenting the alerts through an easy-to-use web interface and robust API.

---

## Examples

<div align="center">

<table>
  <tr>
    <td align="center" width="33%"><img src="Example GIFs/Weapon-example-compressed.gif" width="100%" alt="Weapon Example" /></td>
    <td align="center" width="33%"><img src="Example GIFs/Violence-example-compressed.gif" width="100%" alt="Violence Example" /></td>
    <td align="center" width="33%"><img src="Example GIFs/Safe-example-compressed.gif" width="100%" alt="Safe Example" /></td>
  </tr>
  <tr>
    <td align="center"><b>Weapon Detection Example</b></td>
    <td align="center"><b>Violence Detection Example</b></td>
    <td align="center"><b>Safe Scenario Example</b></td>
  </tr>
  <tr>
    <td align="center" colspan="3"><img src="Example GIFs/webcam-example.gif" width="90%" alt="Webcam Live Stream Detection Example" /></td>
  </tr>
  <tr>
    <td align="center" colspan="3"><b>Webcam Live Stream Detection Example</b></td>
  </tr>
</table>

</div>

### *Try out the upload image/video demo [here](https://cctvdemo.rish.click/)*

---

## Datasets & Capabilities

This project utilizes several datasets for model training and evaluation:\
1a. [Roboflow - Weapon Detection CCTV v3](https://universe.roboflow.com/weapon-detection-cctv/weapon-detection-cctv-v3-dataset) - **Weapons detection (in use)**\
1b. [Hugging Face - Simuletic/cctv-weapon-dataset](https://huggingface.co/datasets/Simuletic/cctv-weapon-dataset) - **Weapons detection (simuletic dataset) alternate model**\
2. [Kaggle - Smart-City CCTV Violence Detection Dataset (SCVD)](https://www.kaggle.com/datasets/toluwaniaremu/smartcity-cctv-violence-detection-dataset-scvd) - **Violence/fighting detection**\
3. [Kaggle - UCF Crime Dataset](https://www.kaggle.com/datasets/odins0n/ucf-crime-dataset) - **Anomaly detection** (e.g., assault, burglary, arson, etc.)

---

## Project Features

- **Spatial Object Detection (weapons/people):** Utilizes YOLOv8 to detect and track entities such as people and weapons in images.
- **Temporal Action Recognition (violence):** Employs a SlowFast model to analyze sequential motion and classify behaviors such as "violence" or "fighting".
- **Anomaly Detection:** Identifies unspecified unusual behaviors including Abuse, Arrest, Arson, Assault, Burglary, Explosion, RoadAccidents, Robbery, Shooting, Shoplifting, Stealing, and Vandalism.
- **Fusion Layer (Threat Scoring):** Features an intelligent rule based evaluation that synthesizes outputs from various detection modules into a final unified threat score.
- **FastAPI Inference Backend:** A robust, high performance API server processing images and executing simultaneous multi-model inferences.
- **Streamlit Frontend Applications:** Streamlit frontend for live stream analysis and an alternate UI to upload images and videos to see the detection in action.

---

## Project Architecture

```text
               ┌─────────────────────────────────────┐
               │      Streamlit Frontend Apps        │
               │    (Live Stream UI & Upload UI)     │
               └─────────────────┬───────────────────┘
                                 │
                                 ▼
               ┌─────────────────────────────────────┐
               │        FastAPI Inference API        │
               │ (Simultaneous multi-model inference)│
               └─────────────────┬───────────────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             ▼                   ▼                   ▼
┌──────────────────────┐ ┌───────────────┐ ┌──────────────────┐
│     YOLOv8 Object    │ │   SlowFast    │ │      Anomaly     │
│      Detection       │ │    Action     │ │     Detection    │
│  (People, Weapons)   │ │  Recognition  │ │ (Abuse, Arson,   │
│                      │ │  (Violence)   │ │  Burglary, etc.) │
└────────────┬─────────┘ └───────┬───────┘ └─────────┬────────┘
             │                   │                   │
             └───────────────────┼───────────────────┘
                                 ▼
               ┌─────────────────────────────────────┐
               │     Fusion Layer Threat Scoring     │
               │   (Rules & Ensembled Threat Score)  │
               └─────────────────┬───────────────────┘
                                 │
                                 ▼
               ┌─────────────────────────────────────┐
               │      Alert & Monitoring System      │
               │      (UI feedback, logs, APIs)      │
               └─────────────────────────────────────┘
```

## Project Structure

```bash
CCTV-Threat-Detection/
├── backend/                                # FastAPI backend
│   ├── models/                             # Pre-trained models (.pth / .pt)
│   ├── api.py                              # FastAPI backend logic
│   ├── Dockerfile                          # Backend Docker image
│   └── requirements.txt                    # Backend dependencies
├── frontend/                               # Streamlit frontend apps
│   ├── streamlit-app.py                    # UI to upload images/videos
│   ├── streamlit-webcam.py                 # Live stream analysis UI
│   ├── Dockerfile                          # Frontend Docker image
│   └── requirements.txt                    # Frontend dependencies
├── Data/                                   # Dataset directory
├── Example GIFs/                           # Example GIFs for Readme.md
├── Notebooks/                              # Jupyter Notebooks for training/dev
│   ├── Rule-Based-Threat-Detection.ipynb
│   ├── anamoly-detection-model.ipynb
│   ├── violence-detection-i3d.ipynb
│   ├── violence-detection-slowfast.ipynb
│   ├── weapon-detection-model-mark2.ipynb
│   └── weapon-detection-model-simuletic.ipynb
├── .gitattributes
├── .gitignore
├── docker-compose.yml
├── example.env
├── LICENSE
├── Readme.md
└── requirements.txt                        # Unified requirements for local dev/deployment
```

---

## Installation

### Local Installation

Clone the repo:

```bash
git clone https://github.com/rishabhpatel9/CCTV-Threat-Detection.git
cd CCTV-Threat-Detection
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Prepare environment variables:

```bash
cp example.env .env
# Edit .env with your credentials (e.g., Twilio for webcam)
```

Run FastAPI backend:

```bash
cd backend
uvicorn api:app --reload
```

Run Streamlit Webcam based frontend:

```bash
cd frontend
streamlit run streamlit-webcam.py
```

*OR*

Run Streamlit upload image/video frontend:

```bash
cd frontend
streamlit run streamlit-app.py
```

### Deployment with Docker

You can easily spin up the entire pipeline (API + Frontend UIs) using the included `docker-compose.yml` file:

**Important Data Note:** The system will automatically download the necessary machine learning model files (~143 MB) on its first run.

1. **Build and run the containers:**

   **For systems WITHOUT an NVIDIA GPU (Default - Fast & Lightweight):**
   ```bash
   docker-compose up --build
   ```
   *Note: This automatically downloads a lightweight, CPU-only version of PyTorch to save several gigabytes of disk space and download time.*

   **For systems WITH an NVIDIA GPU:**
   ```bash
   docker-compose build --build-arg USE_GPU=true
   docker-compose up -d
   ```
   *Note: This downloads the full PyTorch wheel with CUDA/cuDNN support for hardware acceleration.*

2. **Prepare Environment Variables:**
   ```bash
   cp example.env .env
   # Edit .env to set USE_GPU=true/false and add Twilio credentials
   ```

3. **Port Mapping:**
   The services will be available at:
   - **FastAPI Backend**: http://localhost:8000
   - **Streamlit Frontend (Image/Video Upload)**: http://localhost:8501
   - **Streamlit Frontend (Webcam Live Stream)**: http://localhost:8502
   
To stop the services, run:
```bash
docker-compose down
```

---

## Future Work

*Refer to [Project Expansion Roadmap](Project_Expansion_Roadmap.md) for detailed future work.*

- **Indoor & Home Security Focus**: Optimize the deployment experience for indoor and home environments. This includes building comprehensive management dashboards and real time alert systems (SMS/Push notifications) to provide a professional, user friendly security experience.
- **Violence/Fighting Detection Pipeline**: Implement YOLOv8 as a preprocessing step to detect and crop person instances from frames before feeding them into action recognition models. This will improve accuracy by focusing purely on human interactions and reducing background interference.
- **Loitering & Advanced Anomaly Detection**: Integrate object tracking (e.g., DeepSORT) with YOLOv8 to analyze person trajectories, enabling the detection of loitering and other movement-based anomalies.
- **Environmental & Vehicle Safety**: Extend detection capabilities to include vehicle classes and environmental threats like smoke or fire.
- **Restricted Zones & Tripwires**: Implement post processing logic to allow users to define virtual geofences and tripwires within the video feed, triggering alerts based on spatial violations.
- **Abandoned Object Detection**: Develop logic to identify stationary items like bags or backpacks in public spaces, flagging them as potential security risks when left unattended.

---

## Contributing

Contributions are welcome!

* Fork the repo
* Create a feature branch
* Submit a pull request