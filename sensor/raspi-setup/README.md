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
