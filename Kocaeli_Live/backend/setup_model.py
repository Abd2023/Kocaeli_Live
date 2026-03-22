"""
setup_model.py — Kocaeli Live Model Auto-Downloader
=====================================================
Run this script ONCE before starting the backend server.
It downloads the required Qwen2.5-0.5B-Instruct GGUF model
from Hugging Face (approximately 490 MB) and saves it to
the backend/models/ directory.

Usage:
    python setup_model.py
"""

import os
import sys
import urllib.request

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
MODEL_FILENAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
MODELS_DIR     = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH     = os.path.join(MODELS_DIR, MODEL_FILENAME)

# Direct download URL from Hugging Face (Qwen2.5-0.5B-Instruct GGUF Q4_K_M)
HF_REPO        = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
HF_URL         = f"https://huggingface.co/{HF_REPO}/resolve/main/{MODEL_FILENAME}"

def progress_bar(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(downloaded / total_size * 100, 100)
        mb_done  = downloaded / 1_000_000
        mb_total = total_size  / 1_000_000
        bar_fill = int(percent / 2)
        bar = "█" * bar_fill + "░" * (50 - bar_fill)
        print(f"\r  [{bar}] {percent:5.1f}%  ({mb_done:.1f} / {mb_total:.1f} MB)", end="", flush=True)

def main():
    print("=" * 60)
    print("  Kocaeli Live — Model Setup")
    print("=" * 60)

    # Ensure models/ directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Skip download if model already exists
    if os.path.exists(MODEL_PATH):
        size_mb = os.path.getsize(MODEL_PATH) / 1_000_000
        print(f"\n✅ Model already present ({size_mb:.0f} MB). No download needed.")
        print(f"   Path: {MODEL_PATH}")
        return

    print(f"\n📥 Downloading: {MODEL_FILENAME}")
    print(f"   Source: {HF_URL}")
    print(f"   Target: {MODEL_PATH}")
    print(f"\n   This may take a few minutes (~490 MB). Please wait...\n")

    try:
        urllib.request.urlretrieve(HF_URL, MODEL_PATH, reporthook=progress_bar)
        print()  # newline after progress bar
        
        final_size = os.path.getsize(MODEL_PATH) / 1_000_000
        print(f"\n✅ Download complete! ({final_size:.0f} MB)")
        print(f"   Saved to: {MODEL_PATH}")
        print("\n🚀 You can now start the backend server:")
        print("   python app.py\n")

    except Exception as e:
        print(f"\n\n❌ Download failed: {e}")
        # Remove incomplete file if download failed
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
            print("   Incomplete file removed. Please try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
