All files in the `boot-files/` directory should be copied to a Raspberry Pi's `/boot/midcost-init-files/` directory. The setup script has to be run manually after initially connecting the Pi using the following command:

```bash
python3 /boot/midcost-init-files/initialize-midcost-node.py
```

The `boot-files/midcost-init-files/` directory should contain the following:

```bash
# Setup script
initialize-midcost-node.py

# Wifi Credentials for personal hotspots and eduroam
network_wpa_com*.conf

# SSH keys for GitHub Access
ssh_config.txt
ssh_id_ed25519_esm_technical_user
ssh_id_ed25519_esm_technical_user.pub

# Automatic job dispatching
crontab
```
