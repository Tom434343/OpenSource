#!/bin/bash
# Installation Terminal Capture : raccourci bureau + wrapper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "Installation Terminal Capture"
echo ""

# Verifier les dependances
if ! command -v zenity &>/dev/null; then
    echo "zenity requis : sudo apt install zenity"
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

if ! command -v claude &>/dev/null; then
    echo "Claude Code requis : https://claude.ai/code"
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

# Rendre executable
chmod +x "$SCRIPT_DIR/lancer-session.sh"

# Creer projets.conf si absent
if [ ! -f "$SCRIPT_DIR/projets.conf" ]; then
    cp "$SCRIPT_DIR/projets.conf.example" "$SCRIPT_DIR/projets.conf"
    echo "projets.conf cree depuis l'exemple — editez-le avec vos projets."
fi

# Wrapper sans espace dans le chemin (compatibilite .desktop)
WRAPPER="$HOME/tc-launch.sh"
cat > "$WRAPPER" << EOF
#!/bin/bash
cd "$SCRIPT_DIR" && bash lancer-session.sh
EOF
chmod +x "$WRAPPER"

# Raccourci bureau
DESKTOP_FILE="$HOME/Bureau/terminal-capture.desktop"
[ ! -d "$HOME/Bureau" ] && DESKTOP_FILE="$HOME/Desktop/terminal-capture.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Terminal Capture
Comment=Session Claude Code par projet avec export Markdown
Exec=gnome-terminal -- bash $WRAPPER
Icon=utilities-terminal
Hidden=false
Terminal=false
EOF

chmod +x "$DESKTOP_FILE" 2>/dev/null

echo ""
echo "Installation terminee :"
echo "  Wrapper    : $WRAPPER"
echo "  Raccourci  : $DESKTOP_FILE"
echo "  Config     : $SCRIPT_DIR/projets.conf"
echo ""
echo "→ Editez projets.conf avec vos projets, puis double-cliquez sur le raccourci."
echo ""

read -p "Appuyez sur Entree pour fermer..." dummy
