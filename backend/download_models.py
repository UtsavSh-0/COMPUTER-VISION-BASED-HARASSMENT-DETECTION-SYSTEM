import os
from huggingface_hub import hf_hub_download

def download_models():
    # Downloads the necessary large model files from Hugging Face Hub if they don't exist locally.
    repo_id = "rishp9/CCTV-Threat-Detection-Models"  # Updated repository name
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    
    # List of required models to download
    models = [
        "violence-detection-slowfast-model.pth",
        "anamoly-detection-model-epoch10.pth",
        "weapon-detection-model-mark2.pt"
    ]
    
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        
    print("Checking for required models...")
    for model_file in models:
        model_path = os.path.join(models_dir, model_file)
        
        # Check if file exists and is not a Git LFS pointer (very small files are likely pointers)
        is_valid = False
        if os.path.exists(model_path):
            if os.path.getsize(model_path) > 1024:  # If > 1KB, likely not a pointer
                is_valid = True
            else:
                # Check content for LFS signature
                try:
                    with open(model_path, 'r') as f:
                        content = f.read(100)
                        if "version https://git-lfs.github.com/spec/v1" not in content:
                            is_valid = True
                except:
                    # If we can't read it as text, it might be a real binary model
                    is_valid = True
        
        if not is_valid:
            print(f"Downloading {model_file} from Hugging Face Hub (existing file is missing or a placeholder)...")
            try:
                hf_hub_download(
                    repo_id=repo_id,
                    filename=model_file,
                    local_dir=models_dir,
                    local_dir_use_symlinks=False
                )
                print(f"Successfully downloaded {model_file}")
            except Exception as e:
                print(f"Error downloading {model_file}: {e}")
                print(f"Please ensure {model_file} is available at huggingface.co/{repo_id}")
        else:
            print(f"Model {model_file} already exists and appears valid.")

if __name__ == "__main__":
    download_models()
