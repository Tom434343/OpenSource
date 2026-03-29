#!/bin/bash
# Installation : service systemd (boot) + cron quotidien

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL_USER=$(logname 2>/dev/null || echo "$SUDO_USER" || echo "$USER")
REAL_HOME=$(eval echo "~$REAL_USER")

echo ""
echo "Installation Integrity Check"
echo ""

# Verifier sudo
if [ "$EUID" -ne 0 ]; then
    echo "Usage : sudo bash install.sh"
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

# Verifier baseline
if [ ! -f "$SCRIPT_DIR/baseline/baseline-info.txt" ]; then
    echo "ERREUR : lancez d'abord baseline.sh pour creer la reference !"
    echo "  → bash $SCRIPT_DIR/baseline.sh"
    read -p "Appuyez sur Entree pour fermer..." dummy
    exit 1
fi

# Rendre les scripts executables
chmod +x "$SCRIPT_DIR/baseline.sh"
chmod +x "$SCRIPT_DIR/integrity-check.sh"

# Creer dossier logs
mkdir -p "$REAL_HOME/logs/security"
chown "$REAL_USER:$REAL_USER" "$REAL_HOME/logs/security"

# Service systemd (one-shot au boot)
cat > /etc/systemd/system/integrity-check.service << EOF
[Unit]
Description=Integrity Check — Verification systeme au boot
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$REAL_USER
ExecStartPre=/bin/sleep 60
ExecStart=/bin/bash $SCRIPT_DIR/integrity-check.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable integrity-check.service
echo "✅ Service systemd active (boot + 60s)"

# Cron quotidien 08:00
CRON_LINE="0 8 * * * $SCRIPT_DIR/integrity-check.sh >> $REAL_HOME/logs/security/integrity-cron.log 2>&1"
(crontab -u "$REAL_USER" -l 2>/dev/null | grep -v "integrity-check"; echo "$CRON_LINE") | crontab -u "$REAL_USER" -
echo "✅ Cron quotidien 08:00 installe"

echo ""
echo "Verification :"
systemctl status integrity-check.service --no-pager | head -5
echo ""
crontab -u "$REAL_USER" -l | grep integrity
echo ""

read -p "Appuyez sur Entree pour fermer..." dummy
