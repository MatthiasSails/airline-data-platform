#!/bin/bash
set -e

echo "Pulling latest..."
cd ~/airline-data-platform && git pull

echo "Installing systemd units..."
sudo cp deployment/systemd/pipeline.service /etc/systemd/system/
sudo cp deployment/systemd/pipeline.timer /etc/systemd/system/

echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl enable pipeline.timer
sudo systemctl restart pipeline.timer

echo "Done!"
systemctl status pipeline.timer
