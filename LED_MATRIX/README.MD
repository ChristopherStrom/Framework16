# Automated Python Scripts on Boot

This repository contains two Python scripts, `IO_Info.py` and `Temp_and_IP.py`, that are designed to run in the background at boot using systemd. The scripts are located in `/home/$USER/scripts/fw16/`.

## Prerequisites

Make sure Python3 is installed on your system. You can install it using:

```bash
sudo apt-get install python3
```

## Setting Up the Scripts to Run on Boot

To configure the scripts to run in the background during boot, you need to create two systemd service files.

### 1. Create the `io_info.service` file

Run the following command to create the service file:

```bash
sudo nano /etc/systemd/system/io_info.service
```

Add the following content to the file:

```ini
[Unit]
Description=Run IO Info Script at boot
After=graphical.target

[Service]
ExecStart=/usr/bin/python3 /home/$USER/scripts/fw16/IO_Info.py
Environment="DISPLAY=:0"
Environment="XDG_RUNTIME_DIR=/run/user/1000"
WorkingDirectory=/home/$USER/scripts/fw16/
Restart=always
User=$USER

[Install]
WantedBy=multi-user.target
```

### 2. Create the `temp_and_ip.service` file

Run the following command to create the service file:

```bash
sudo nano /etc/systemd/system/temp_and_ip.service
```

Add the following content to the file:

```ini
[Unit]
Description=Run Temp and IP Script at boot
After=graphical.target

[Service]
ExecStart=/usr/bin/python3 /home/$USER/scripts/fw16/Temp_and_IP.py
WorkingDirectory=/home/$USER/scripts/fw16/
Restart=always
User=$USER

[Install]
WantedBy=multi-user.target
```

## Enable and Start the Services

Once you’ve created both service files, enable them to start at boot by running:

```bash
sudo systemctl enable io_info.service
sudo systemctl enable temp_and_ip.service
```

If you want to start them immediately without rebooting, use:

```bash
sudo systemctl start io_info.service
sudo systemctl start temp_and_ip.service
```

### Verifying Service Status

To verify if the services are running correctly, use the following command:

```bash
sudo systemctl status io_info.service
sudo systemctl status temp_and_ip.service
```

If the services are running successfully, you will see their status as "active (running)".
