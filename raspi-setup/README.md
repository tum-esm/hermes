All files in the `boot-files/` directory should be copied to a Raspberry Pi's `/boot/midcost-init-files/` directory. The setup script has to be run manually after initially connecting the Pi using the following command:

```bash
# initialize the node
sudo python3 /boot/midcost-init-files/initialize-midcost-node.py
sudo reboot

# test the initial installation
python3 /boot/midcost-init-files/test-midcost-node.py
```

The `boot-files/` should contain the following files:

```
📁 boot-files/

    📄 wpa_supplicant.conf
    📄 config.txt

    📁 midcost-init-files/

        📄initialize_midcost_node.py
        📄test_midcost_node.py

        📁 baserow-ip-logger/
            📄 config.json

        📁 hermes/
            📄 .env
            📄 config.json
            📄 hermes-cli.template.sh

        📁 ssh/
            📄 authorized_keys
            📄 config.txt
            📄 id_ed25519_esm_technical_user
            📄 id_ed25519_esm_technical_user.pub

        📁 system/
            📄 .bashrc
            📄 crontab
```
