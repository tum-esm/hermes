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

TODO: describe how to set up the LTE hat

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

1. Merge the changes into the `main` branch via a PR on GitHub to let the CI run all tests
1. Tag the commit as `v0.1.0-beta.3` (or whatever the new version is)
1. Create a release on GitHub with the same tag (`v0.1.0-beta.3`)
1. Follow the description structure from https://github.com/tum-esm/hermes/releases/tag/v0.1.0-beta.1

**Now, you can send new configs with that release number to the server:**

The configs sent to the server should contain everything except for the `revision field`. The respective sensors will receive the new config and download the tagged release from GitHub.

<br/>

## How the Raspi's run this code

The sensor code is at `~/Documents/hermes/0.1.0-beta.3`. Only the sensor directory of this repository is stored on the Pi. The _crontab_ contains a line that starts the version currently active every 2 minutes. The CLI will only start the automation if it is not already running.

```cron
# start automation (if not already running)
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
