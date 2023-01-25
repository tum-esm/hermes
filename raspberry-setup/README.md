All files in the `boot-files/` directory should be copied to a Raspberry Pi's `/boot/midcost-init-files/` directory. The setup script has to be run manually after initially connecting the Pi using the following command:

```bash
python3 /boot/midcost-init-files/initialize-midcost-node.py
```

The `boot-files/` should contain the following files:

```bash
# Wifi credentials for personal hotspots and eduroam
wpa_supplicant.conf

# Setup script
midcost-init-files/initialize-midcost-node.py

# SSH keys for GitHub Access
midcost-init-files/ssh_authorized_keys
midcost-init-files/ssh_config.txt
midcost-init-files/ssh_id_ed25519_esm_technical_user
midcost-init-files/ssh_id_ed25519_esm_technical_user.pub

# Automatic job dispatching
midcost-init-files/crontab
```
