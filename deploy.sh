#!/usr/bin/env bash
set -euo pipefail

#===================CONFIG====================
SERVICE_NAME="barghman-bot"
USER=$(whoami)
PROJECT_DIR=$(pwd)
PYTHON_BIN=$(command -v python3 || true)

if [[ -z "$PYTHON_BIN" ]]; then 
	echo "Python is not installed. Please install it first"
	exit 1
fi
#=============================================


#============SYSTEM DEPENDENCIES==============
echo "[*] Installing system dependencies..."
sudo apt update
sudo apt install -y python3-venv python3-dev pkg-config libsystemd-dev build-essential redis-server

#=============================================


#==========VIRTUALENV & REQUIREMENTS==========
if [[ ! -d "$PROJECT_DIR/venv" ]]; then
	echo "[*] Creating virtual environment..."
	"$PYTHON_BIN" -m venv "$PROJECT_DIR/venv"
fi

echo "[*] Installing python dependencies..."
"$PROJECT_DIR/venv/bin/pip" install --upgrade pip wheel
"$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
#=============================================


#==================ENV FILE===================
ENV_FILE="$PROJECT_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then	
	echo "[*] Creating .env file..."
	cat > "$ENV_FILE" <<EOF
BLACKOUT_API_TOKEN=YourApiToken
TELEGRAM_BOT_TOKEN=YourTelegramBotToken
PROXY_URL=http://127.0.0.1:12334
EOF

	echo "[*] .env created at $ENV_FILE"
else
	echo "[*] .env already exists, skipping."
fi
#=============================================


#=================LOG FOLDER==================
if [[ ! -d "/var/log/$SERVICE_NAME" ]]; then
	echo "[*] Creating a log folder at '/var/log/$SERVICE_NAME'..."
	sudo mkdir -p /var/log/$SERVICE_NAME
	sudo chown $USER:$USER /var/log/$SERVICE_NAME
fi
#=============================================


#==============DJANGO-MIGRATION===============
echo "[*] Running Django migrations..."
"$PROJECT_DIR/venv/bin/python" manage.py migrate --noinput
#=============================================


#==================CRON JOBS==================
sudo tee /etc/cron.d/$SERVICE_NAME > /dev/null <<EOF
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

#check_outages
0 */1 * * * $USER $PROJECT_DIR/venv/bin/python $PROJECT_DIR/manage.py check_outages >> /var/log/$SERVICE_NAME/Barghman_redis_update.log 2>&1

#send_near_outages
5 0 * * * $USER $PROJECT_DIR/venv/bin/python $PROJECT_DIR/manage.py send_near_outages >> /var/log/$SERVICE_NAME/Barghman_auto_reports.log 2>&1
EOF
#=============================================


#===============SYSTEMD-SERVICE===============
echo "[*] Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=BarghMan Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python telegram_bot/bot.py
Restart=always
RestartSec=5
RuntimeMaxSec=6h

StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

WatchdogSec=30
Type=notify
NotifyAccess=all

[Install]
WantedBy=multi-user.target
EOF
#=============================================


#===========ENABLE-&-START-SERVICE============
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME
sudo systemctl enable redis-server
sudo systemctl start redis-server
#=============================================
echo "[✓] Deployment complete. Service '$SERVICE_NAME' is running."