# Sensor Software

## Installation

**Set up virtual environment and install dependencies:**

```bash
python3.9 -m venv .venv
source .venv/bin/activate
poetry install --with=dev
```

**Run tests/check static types:**

```bash
# all tests
pytest --cov=src --cov=cli tests/

# only ci tests
pytest -m "ci" --cov=src --cov=cli tests/

# only integration tests
pytest -m "integration" --cov=src --cov=cli tests/

#test static types
bash ./scripts/check_static_types.sh
```


<br/>
<br/>

## Configuration

Use the `config/config.template.json` to generate a `config/config.json`. `config.general.station_name` will be used in the logs, the MQTT communication, and the database/server to identify each station.

<br/>
<br/>

## Code location on the Raspi

On the sensor, the codebase layout will look like this:

```bash
📁 Documents
    📁 hermes
        📄 hermes-cli.sh
        📁 0.1.0
            📁 .venv
            📄 run.py
            ...
        📁 0.1.1
            📁 .venv
            📄 run.py
            ...
        ...
```

The `hermes-cli.sh` will point to the currently used version, and the bash shell has an alias `hermes-cli`.

<br/>
<br/>

## Raspberry Pi Setup (`raspi-setup-files/`)

As the operating system for the Raspis, we chose **Raspberry Pi OS 64-Bit** and used the **Raspberry Pi Imager** (https://www.raspberrypi.com/software/) to flash the SD cards.

All files in the `raspi-setup-files/` directory should be copied to a Raspberry Pi's `/boot/` directory. The setup script has to be run manually after initially connecting the Pi using the following command:

```bash
# test network connection
ping -c 3 www.google.com

# initialize the node
sudo python3 /boot/midcost-init-files/initialize_root.py
python3 /boot/midcost-init-files/initialize_pi.py

# reboot
sudo reboot

# test the initial installation
python3 /boot/midcost-init-files/run_node_tests.py

# finish installation
curl parrot.live
```

The `boot-files/` should contain the following files:

```
📁 boot-files/

    📄 config.txt

    📁 midcost-init-files/

        📄 initialize_root.py
        📄 initialize_pi.py
        📄 run_node_tests.py

        📁 baserow-ip-logger/
            📄 config.json

        📁 hermes/
            📄 .env
            📄 config.json
            📄 hermes-cli.template
            📄 hostname_to_mqtt_id.json

        📁 ssh/
            📄 authorized_keys
            📄 config.txt
            📄 id_ed25519_esm_technical_user
            📄 id_ed25519_esm_technical_user.pub
            📄 wpa_supplicant.conf

        📁 system/
            📄 .bashrc
            📄 crontab
```

<br/>
<br/>

## Manual commands

```bash
# setting the pump to max/zero rps
pigs w 19 1
pigs w 19 0

# powering the co2 sensor up/down
# serial: /dev/ttySC0, baudrate 19200, bytes 8, parity N, stopbits 1, newline \r\n
pigs w 20 1
pigs w 20 0

# powering the wind sensor up/down
# serial: /dev/ttySC1, baudrate 19200, bytes 8, parity N, stopbits 1, newline \r\n
pigs w 21 1
pigs w 21 0
```

<br/>

## Set up LTE Hat

### Install software on RaspberryPi

```bash
sudo apt-get install minicom
sudo apt-get install p7zip-full
sudo apt-get install udhcpc
```

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
AT+CGDCONT=1,"IP","[iotde.telefonica.com](http://iotde.telefonica.com/)"
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

## Release cycle

**For every new release of the sensor software, the following code changes should happen:**

1. Update the version in `pyproject.toml`
2. Update the version in `src/custom_types/config.py`:

    ```python
    class Config(pydantic.BaseModel):
        """The config.json for each sensor"""

        version: Literal["0.1.0-beta.3"]
        ...
    ```

3. Update the version in `config/config.template.json` (you can keep the revision at zero since the server will set it)
    ```json
    {
        "version": "0.1.0-beta.3",
        "revision": 0,
        ...
    }
    ```

**The release process is as follows:**

1. Merge all changes into the `main` branch
2. Check whether the GitHub CI tests were successful for this commit
3. Tag the commit as `v0.1.0-beta.3` (or whatever the new version is)
4. Create a release on GitHub with the same tag (`v0.1.0-beta.3`)
5. Follow the description structure from https://github.com/tum-esm/hermes/releases/tag/v0.1.0-beta.1

**Now, you can send new configs with that release number to the server:**

The configs sent to the server should contain everything except for the `revision field`. The respective sensors will receive the new config and download the tagged release from GitHub.

<br/>

## How the Raspi's run this code

The sensor code is at `~/Documents/hermes/0.1.0-beta.3`. Only the sensor directory of this repository is stored on the Pi. The _crontab_ contains a line that starts the version currently active every 2 minutes. The CLI will only start the automation if it is not already running.

```cron
# start automation every two minutes (if not already running)
*/2 * * * * bash /home/pi/Documents/hermes/hermes-cli.sh start > /home/pi/Documents/hermes/hermes-cli.log
```

The file `~/Documents/hermes/hermes-cli.sh` always points to the currently active version of Hermes.

```bash
#!/bin/bash

set -o errexit

/home/pi/Documents/hermes/0.1.0-beta.3/.venv/bin/python /home/pi/Documents/hermes/0.1.0-beta.3/cli/main.py $*
```

The `~/.bashrc` file contains an alias for the CLI:

```bash
alias hermes-cli="bash /home/pi/Documents/hermes/hermes-cli.sh"
```

When actively developing the code on the Raspi, you should clone this repository, change the `~/Documents/hermes/hermes-cli.sh` to point to the cloned repository, and deactivate the cronjob.

If you notice scaling issues with the automation (issues that only arise after running the software for a few days), you can add a restart every 3-4 days to the _crontab_:

```cron
# restart automation at midnight on mondays and thursdays
0 0 * * 1,4 bash /home/pi/Documents/hermes/hermes-cli.sh restart > /home/pi/Documents/hermes/hermes-cli.log
```
