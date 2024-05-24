import os
from smbus2 import SMBus

for b in os.listdir("/dev"):
    if os.path.isdir(os.path.join("/dev", b)):
        continue

    try:
        bus = SMBus(f"/dev/{b}")

        for a in range(0x000, 0xFFF):
            try:
                bus.write_byte_data(a, 0, 0)
                print(f"{b} -> {hex(a)} exists")
            except OSError:
                pass
        bus.close()
    except (PermissionError, OSError):
        pass
