import argparse
import os
from huggingface_hub import snapshot_download

def download_model(model_id: str, local_dir: str = "models"):
    """Download an SLM from Hugging Face for local execution."""
    print(f"DOWNLOAD: Downloading {model_id} to {local_dir}...")
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    
    snapshot_download(repo_id=model_id, local_dir=local_dir)
    print("DONE: Download complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download SLM models for local execution.")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct", help="Hugging Face Model ID")
    parser.add_argument("--dir", type=str, default="src/models/weights", help="Local directory to store weights")
    
    args = parser.parse_args()
    download_model(args.model, args.dir)
