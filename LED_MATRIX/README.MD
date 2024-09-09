# Automated Python Scripts on Login

This repository contains two Python scripts, `IO_Info.py` and `Temp_and_IP.py`, that are designed to run at user login using systemd. The scripts are located in `/home/$USER/scripts/fw16/`.

## Prerequisites

Make sure Python3 is installed on your system. You can install it using:

```bash
sudo apt-get install python3
```

## Setting Up the Scripts to Run on User Login

To configure the scripts to run in the background during user login, follow these steps to create user-specific systemd service files.

### 1. Create the `io_info.service` for `IO_Info.py`

Run the following command to create the user service file:

```bash
mkdir -p /.config/systemd/user
nano /.config/systemd/user/io_info.service
```

Add the following content to the file:

```ini
[Unit]
Description=Run IO Info Script at login
After=default.target

[Service]
ExecStart=/usr/bin/python3 /home/$USER/scripts/fw16/IO_Info.py
WorkingDirectory=/home/$USER/scripts/fw16/
Restart=always

[Install]
WantedBy=default.target
```

### 2. Create the `temp_and_ip.service` for `Temp_and_IP.py`

Run the following command to create the service file:

```bash
nano /.config/systemd/user/temp_and_ip.service
```

Add the following content to the file:

```ini
[Unit]
Description=Run Temp and IP Script 30 seconds after login and when network services are up
After=network-online.target default.target
Wants=network-online.target

[Service]
Type=idle
ExecStartPre=/bin/sleep 30
ExecStart=/usr/bin/python3 /home/cyberlab/scripts/fw16/Temp_and_IP.py
WorkingDirectory=/home/cyberlab/scripts/fw16/
Restart=always

[Install]
WantedBy=default.target
```

### 3. Enable and Start the User Services

To enable the services so they run at login, use the following commands:

```bash
systemctl --user enable io_info.service
systemctl --user enable temp_and_ip.service
```

To start the services immediately, use:

```bash
systemctl --user start io_info.service
systemctl --user start temp_and_ip.service
```

### 4. Enable Lingering (Optional)

If you want these services to start even after boot without logging in, enable lingering for the user:

```bash
sudo loginctl enable-linger $USER
