#!/usr/bin/env bash

# Install Boiler Alert System

# Needs to run as root to perform the installation.
if [ $EUID -ne 0 ]; then
		echo "This setup tool is required to run as root"
		exit
fi

INSTALL_DIR=/usr/local/boilerswitch
UPGRADE=FALSE
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE=/etc/boilerswitch.yaml
SERVICE_FILE=/etc/systemd/system/boilerswitch.service
RSYSLOG_FILE=/etc/rsyslog.d/16-boilerswitch.conf
LOGROTATE_FILE=/etc/logrotate.d/boilerswitch
if [ ! -d $INSTALL_DIR ]; then
	echo "Creating Folder: $INSTALL_DIR"
	mkdir "$INSTALL_DIR"
fi

echo Installing application....
cp "${SCRIPT_DIR}"/bin/*.py $INSTALL_DIR

if [ ! -f $CONFIG_FILE ]; then
    echo "Copying boilerswitch.yaml config file"
    cp "${SCRIPT_DIR}"${CONFIG_FILE}.template $CONFIG_FILE
else
    echo "Copying boilerswitch.yaml config file as ${CONFIG_FILE}.upgrade"
    cp "${SCRIPT_DIR}"${CONFIG_FILE}.template ${CONFIG_FILE}.upgrade
    UPGRADE=TRUE
fi

echo "Copying boilerswitch service file"
cp --backup "${SCRIPT_DIR}"$SERVICE_FILE $SERVICE_FILE

echo "Copying boilerswitch logrotate file"
cp --backup "${SCRIPT_DIR}"$LOGROTATE_FILE $LOGROTATE_FILE

echo "Copying boilerswitch rsyslog file"
cp --backup "${SCRIPT_DIR}"$RSYSLOG_FILE $RSYSLOG_FILE

echo "Making files executable"
chmod +x "${INSTALL_DIR}"/*.py
echo

echo "Enabling and Starting boilerswitch service"
systemctl restart rsyslog

systemctl daemon-reload
systemctl enable boilerswitch
systemctl start boilerswitch

if [ $UPGRADE = FALSE ]; then
    echo "Installation Complete"
    echo "Please configure $CONFIG_FILE"
else
    echo "Upgrade Complete"
fi

