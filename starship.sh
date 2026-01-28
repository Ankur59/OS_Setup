#!/bin/bash

set -e

echo "✨ Setting up Starship prompt (full setup)..."

# -----------------------------
# Install Nerd Font (JetBrainsMono)
# -----------------------------
echo "🔤 Installing JetBrainsMono Nerd Font..."

FONT_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONT_DIR"

cd /tmp

wget -q https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip

unzip -o JetBrainsMono.zip -d JetBrainsMono

cp JetBrainsMono/*.ttf "$FONT_DIR"

fc-cache -fv

# -----------------------------
# Install Starship
# -----------------------------
echo "🚀 Installing Starship..."

curl -sS https://starship.rs/install.sh | sh -s -- -y

# -----------------------------
# Restore starship.toml
# -----------------------------
echo "🌟 Restoring starship config..."

mkdir -p "$HOME/.config"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/starship.toml" ]; then
  cp "$SCRIPT_DIR/starship.toml" "$HOME/.config/starship.toml"
else
  echo "⚠️ starship.toml not found"
fi

# -----------------------------
# Enable Starship (bash)
# -----------------------------
if ! grep -q 'starship init bash' "$HOME/.bashrc"; then
  echo '' >> "$HOME/.bashrc"
  echo '# Starship prompt' >> "$HOME/.bashrc"
  echo 'eval "$(starship init bash)"' >> "$HOME/.bashrc"
fi

# -----------------------------
# Final notes
# -----------------------------
echo ""
echo "✅ Starship fully set up"
echo "📝 Set your terminal font to: JetBrainsMono Nerd Font"
echo "🔁 Restart terminal to apply changes"
