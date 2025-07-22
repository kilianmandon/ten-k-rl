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

# 3. Create environment from YAML
ENV_NAME=$(head -n 1 environment.yml | cut -d ' ' -f2)

if conda env list | grep -q "$ENV_NAME"; then
  echo "Conda environment '$ENV_NAME' already exists."
else
  echo "Creating conda environment '$ENV_NAME' from environment.yml..."
  conda env create -f environment.yml
fi

# 4. Activate environment
conda activate "$ENV_NAME"

# 5. Build frontend
echo "Installing frontend dependencies and building Vite app..."
cd dice-ui
npm install
npm run build