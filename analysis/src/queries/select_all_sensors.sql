SELECT sensor_name, sensor_identifier
FROM sensors
WHERE sensor_name LIKE 'tum-esm-midcost-raspi-%'
ORDER BY sensor_name ASC;