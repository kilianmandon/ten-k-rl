#!/bin/bash

set -e

# 1. Install Miniforge if not present
if ! command -v conda &> /dev/null; then
  echo "Miniforge not found. Installing Miniforge..."
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh -O ~/miniforge.sh
  else
    echo "Unsupported OS for automatic Miniforge install."
    exit 1
  fi

  bash ~/miniforge.sh -b -p $HOME/miniforge
  rm ~/miniforge.sh
  export PATH="$HOME/miniforge/bin:$PATH"
fi

# 2. Initialize Conda for shell
eval "$($HOME/miniforge/bin/conda shell.bash hook)"

# Update conda
conda update -y -n base -c defaults conda

# Create environment
echo "Creating ml-env conda environment..."
conda create -y -n ml-env python=3.10 \
    numpy pillow pip -c conda-forge

# Activate environment
conda activate ml-env

# Install pip packages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install \
    transformers \
    websockets \
    opencv-python \
    accelerate \
    safetensors \
    huggingface-hub \
    tokenizers \
    requests \
    tqdm \
    packaging \
    filelock \
    pyyaml \
    regex \
    sentencepiece \
    anytree

echo "✅ Environment 'ml-env' is ready!"
echo "Environment installed" >> /root/setup.log