# Table of contents
1. [Clone existing system setup](#paragraph1)
   1. [Copy from SD Card to MacOS](#subparagraph1)
   2. [Copy From MacOS to SD Card](#subparagraph2)
2. [Initial setup](#paragraph2)
   1. [Raspberry Pi Setup](#subparagraph2)
   2. [How the Raspi's run this code](#subparagraph2)
3. [Set up LTE Hat](#paragraph3)
   1. [Configure modem](#subparagraph5)
   2. [Install Driver](#subparagraph6)

<br/>

## Clone existing system setup <a name="paragraph1"></a>


### Copy from SD Card to MacOS <a name="subparagraph1"></a>

- Set current_revision to 0
```
/home/pi/Documents/hermes/%VERSION%/config/state.json 
```

- Identify the correct volume
```
diskutil list
```

- Dismount volume
```
diskutil umount /dev/disk*
```

- Start image creation from SD Card
```
sudo dd if=/dev/disk4 of=/.../hermes-version.img bs=4M status=progress
```

<br/>

### Copy From MacOS to SD Card <a name="subparagraph2"></a>

- Identify the correct volume
```
diskutil list
```

- Dismount volume
```
diskutil umount /dev/disk*
```

- Transfer existing image to SD Card
```
sudo dd of=/dev/disk4 if=/.../hermes-version.img bs=4M status=progress
```

Insert the SD Card into the new node system. Connect to the RaspberryPi over SSH:

- Set the HERMES_MQTT_IDENTIFIER for the new node
```
/home/pi/Documents/hermes/%VERSION%/config/.env 
```

- RaspberryPi Hostname
  
```
sudo raspi-config
1 System Options / S4 Hostname
reboot
```

<br/>

## Initial setup <a name="paragraph2"></a>

```
📁 node-initialization/

    📁 hermes/
        📄 .env.example
        📄 config.template.json

    📁 raspberrypi/
        📄 .bashrc
        📄 crontab
        📄 config.txt
```

<br/>

### Raspberry Pi Setup <a name="subparagraph3"></a>



- Use **Raspberry Pi Imager** (https://www.raspberrypi.com/software/) to flash the **Raspberry Pi OS 64-Bit** on the SD card.
- In settings set hostname, set ssh key access, configure, maintainence wifi, timezone.
- Start up the RaspberryPi once with the new SD card and confirm the SSH access
- Prepare the RaspberryPi setup files by filling in some of the template/example files



```
- Copy all files from the `raspi-setup-files/` on the SD card (`bootfs`). The files should end up in `/boot/firmware`.
- Eject the SD card and insert it into the RaspberryPi.
- Connect to the RaspberryPi via SSH.

```bash
# test network connection
ping -c 3 www.google.com

#create user directories
xdg-user-dirs-update

#install python3.9
sudo wget https://www.python.org/ftp/python/3.9.16/Python-3.9.16.tgz
sudo tar xzf Python-3.9.16.tgz
cd /home/pi/Python-3.9.16
sudo ./configure --enable-optimizations --with-openssl
sudo make altinstall

# initialize the node
sudo python3 /boot/firmware/midcost-init-files/initialize_root.py
python3 /boot/firmware/midcost-init-files/initialize_pi.py

# reboot
sudo reboot

# test the initial installation
python3 /boot/firmware/midcost-init-files/run_node_tests.py

```

<br/>

### How the Raspi's run this code <a name="subparagraph4"></a>

- The sensor code is at `~/Documents/hermes/%VERSION%` 
- Note: Only the files from /sensor directory are kept on the RaspberryPi.
- The _crontab_ starts the automation every 2 minutes via the CLI
- Note: `~/Documents/hermes/hermes-cli.sh` always points to the latest version of Hermes

```bash
#!/bin/bash

set -o errexit

/home/pi/Documents/hermes/%VERSION%/.venv/bin/python /home/pi/Documents/hermes/%VERSION%/cli/main.py $*
```

The `~/.bashrc` file contains an alias for the CLI:

```bash
alias hermes-cli="bash /home/pi/Documents/hermes/hermes-cli.sh"
```

<br/>

## Set up LTE Hat <a name="paragraph3"></a>

### Configure modem <a name="subparagraph5"></a>

```bash
# open modem interface
sudo minicom -D /dev/ttyS0
# check modem functionality
AT 
# see terminal input
ATE1 
# switch to RNDIS
AT+CUSBPIDSWITCH=9001,1,1

# Wait for a possible modem restart

# set SIM APN
AT+CGDCONT=1,"IP","iotde.telefonica.com"
# set network registration to automatic
AT+COPS=0
# set LTE only
AT+CNMP=38

# Wait for a few minutes for the first dial into the mobile network
# Exit modem interface
```

```bash
# check if modem is properly setup for driver installation
sudo minicom -D /dev/ttyUSB2

# commands to check modem status
AT+CSQ # antenna signal strength
AT+CPIN?
AT+COPS? 
AT+CGREG?  
AT+CPSI? #return IMEI
```

<br/>

### Install Driver <a name="subparagraph6"></a>

```bash
# download and install driver
cd /home/pi
wget https://www.waveshare.net/w/upload/8/89/SIM8200_for_RPI.7z
7z x SIM8200_for_RPI.7z -r -o./SIM8200_for_RPI
sudo chmod 777 -R SIM8200_for_RPI
cd SIM8200_for_RPI/Goonline
make clean
make

# Set DNS
sudo ./simcom-cm &
sudo udhcpc -i wwan0
sudo route add -net 0.0.0.0 wwan0

# test connection
ping -I wwan0 www.google.de

# add lines to rc.local
sudo nano /etc/rc.local
```

```bash
sudo /home/pi/SIM8200_for_RPI/Goonline/simcom-cm &
sudo udhcpc -i wwan0
```

<br/>




