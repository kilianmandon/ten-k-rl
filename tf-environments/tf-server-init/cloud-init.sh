#!/bin/bash

apt update

apt install git-lfs
git lfs install
git clone https://github.com/kilianmandon/ten-k-rl.git
cd ten-k-rl
chmod +x setup_and_build.sh
./setup_and_build.sh

eval "$($HOME/miniforge/bin/conda shell.bash hook)"
conda activate tenthousand-env
screen -dmS fastapi run tenthousand_server.py
echo "Ten-K Server Running!"