#!/bin/sh
#
# Install RSS Download Manager as a systemd service
#

SERVICE="rssdldmng"
FILE="$SERVICE.service"
INSTALLPATH="/etc/systemd/system"

rm -rf $FILE
/bin/cat <<EOM >$FILE
[Unit]
Description=RSS Downloader Service
After=multi-user.target

[Service]
Restart=always
RestartSec=10
Type=simple
ExecStart=$(which rssdldmng)
User=$USER
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
EOM

sudo systemctl stop $SERVICE
sudo cp $FILE $INSTALLPATH
rm -rf $FILE

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE
sudo systemctl start $SERVICE
