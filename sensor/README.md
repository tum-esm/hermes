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