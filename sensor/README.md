# Sensor Software

## Installation

**Set up virtual environment and install dependencies:**

```bash
python3.10 -m venv .venv
source .venv/bin/activate
poetry install --with=dev # dev is optional
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
    📁 insert-name-here
        insert-name-here-cli.sh
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

The `insert-name-here-cli.sh` will point to the currently used version. Upgrading the software:

1. Download the new version into the respective directory
2. Migrate the config.json
3. Create new .venv
4. Install new dependencies
5. Run tests
6. Update the `insert-name-here-cli.sh` to point to the new version
7. Call `insert-name-here-cli start` using the `at in 1 minute` command
8. Call `sys.exit()`

Set individual output pins to high/low:

```
pigs w 19 0
pigs w 19 1
```

<br/>
<br/>

## Raspberry Pi Setup (`raspi-setup/`)

All files in the `boot-files/` directory should be copied to a Raspberry Pi's `/boot/midcost-init-files/` directory. The setup script has to be run manually after initially connecting the Pi using the following command:

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
