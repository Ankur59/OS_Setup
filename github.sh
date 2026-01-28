#!/bin/bash

set -e

echo "🔧 Installing Git and SSH client..."
sudo apt update
sudo apt install -y git openssh-client

# -----------------------------
# Git configuration
# -----------------------------
read -p "Enter your Git username: " GIT_NAME
read -p "Enter your Git email: " GIT_EMAIL

git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"

echo "✅ Git configured"

# -----------------------------
# SSH key generation
# -----------------------------
SSH_KEY_PATH="$HOME/.ssh/id_ed25519"

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ -f "$SSH_KEY_PATH" ]; then
  echo "⚠️ SSH key already exists at $SSH_KEY_PATH"
else
  echo "🔐 Generating SSH key..."
  ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f "$SSH_KEY_PATH" -N ""
fi

# -----------------------------
# Start ssh-agent and add key
# -----------------------------
eval "$(ssh-agent -s)"
ssh-add "$SSH_KEY_PATH"

# -----------------------------
# Show public key
# -----------------------------
echo ""
echo "📌 COPY THIS SSH PUBLIC KEY:"
echo "--------------------------------------------------"
cat "$SSH_KEY_PATH.pub"
echo "--------------------------------------------------"
echo ""
echo "👉 Add it to:"
echo "GitHub → Settings → SSH and GPG keys → New SSH key"

# -----------------------------
# Test GitHub connection
# -----------------------------
echo ""
read -p "Press ENTER AFTER adding the key to GitHub..."

ssh -T git@github.com || true

echo ""
echo "✅ GitHub SSH authentication is ready"
echo "🚀 You can now access private repositories without passwords"
