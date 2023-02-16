# Sensor Software

## Installation

**Set up virtual environment and install dependencies:**

```bash
python3.10 -m venv .venv
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

Use the `config/config.template.json` to generate a `config/config.json`.
`config.general.station_name` will be used in the logs, the MQTT communication,
and the database/server to identify each station.

<br/>
<br/>

## Code location on the Raspi

On the sensor, the codebase layout will look like this:

```bash
📁 Documents
    📁 hermes
        hermes-cli.sh
        📁 0.1.0
            📁 .venv
            run.py
            ...
        📁 0.1.1
            📁 .venv
            run.py
            ...
        ...
```

The `hermes-cli.sh` will point to the currently used version and the bash shell
has an alias `hermes-cli`.

<br/>
<br/>

## Raspberry Pi Setup (`raspi-setup-files/`)

All files in the `raspi-setup-files/` directory should be copied to a Raspberry
Pi's `/boot/` directory. The setup script has to be run manually after initially
connecting the Pi using the following command:

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
            📄 hermes-cli.template.sh
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
