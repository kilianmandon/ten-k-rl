#!/bin/bash

apt update

git clone https://github.com/kilianmandon/ten-k-rl.git
cd ten-k-rl
chmod +x setup_and_build.sh
./setup_and_build.sh

screen -dmS fastapi run tenthousand_server.py
echo "Done!"