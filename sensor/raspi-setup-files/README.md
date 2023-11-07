# Configuration

## Raspberry Pi Setup (`raspi-setup-files/`)

- Use **Raspberry Pi Imager** (https://www.raspberrypi.com/software/) to flash the **Raspberry Pi OS 64-Bit** on the SD card.
- In settings set hostname, set ssh key access, configure, maintainence wifi, timezone.
- Prepare the RaspberryPi setup files by filling in some of the template/example files

```
📁 boot-files/

    📁 midcost-init-files/

        📁 hermes/
            📄 .env.example
            📄 config.template.json
            📄 hostname_to_mqtt_id.template.json
```

The `raspi-setup-files/` should contain the following files:

```
📁 boot-files/

    📄 config.txt

    📁 midcost-init-files/

        📄 initialize_root.py
        📄 initialize_pi.py
        📄 run_node_tests.py

        📁 hermes/
            📄 .env
            📄 config.json
            📄 hermes-cli.template.sh
            📄 hostname_to_mqtt_id.json

        📁 system/
            📄 .bashrc
            📄 crontab
```
- Copy all files from the `raspi-setup-files/` on the SD card (boot). The files should end up in `/boot/firmware`.
- Eject the SD card and insert it into the RaspberryPi.
- Connect to the RaspberryPi via SSH.

```bash
# test network connection
ping -c 3 www.google.com

#install python3.9
sudo wget https://www.python.org/ftp/python/3.9.17/Python-3.9.17.tgz
sudo tar xzf Python-3.9.17.tgz
cd /home/pi/Python-3.9.17
sudo ./configure --enable-optimizations
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

## Set up LTE Hat

### Configure modem

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

## Install Driver 

```bash
# download and install driver
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


## How the Raspi's run this code

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


