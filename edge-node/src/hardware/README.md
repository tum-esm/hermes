# Manual commands

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