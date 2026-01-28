#!/bin/bash

set -e  # exit on error

echo "🔧 Updating system..."
sudo apt update && sudo apt upgrade -y

# -----------------------------
# Basic dependencies
# -----------------------------
sudo apt install -y \
  curl \
  wget \
  gnupg \
  lsb-release \
  ca-certificates \
  software-properties-common

# -----------------------------
# VS CODE
# -----------------------------
echo "📝 Installing VS Code..."
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
rm microsoft.gpg
sudo apt update
sudo apt install -y code

# -----------------------------
# POSTMAN
# -----------------------------
echo "📬 Installing Postman..."
sudo snap install postman

# -----------------------------
# BRAVE
# -----------------------------
echo "🦁 Installing Brave..."
sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
  https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] \
  https://brave-browser-apt-release.s3.brave.com/ stable main" | \
  sudo tee /etc/apt/sources.list.d/brave-browser-release.list

sudo apt update
sudo apt install -y brave-browser

# -----------------------------
# DONE
# -----------------------------
echo ""
echo "✅ Dev setup complete!"
echo "🚀 VS Code, Postman, and Brave are installed"
