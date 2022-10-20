On the sensor the codebase layout will look like this:

```bash
📁 Documents
    📁 insert-name-here
        insert-name-here-cli.sh
        📁 0.1.0
            run.py
            ...
        📁 0.1.1
            run.py
            ...
        ...
```

The `insert-name-here-cli.sh` will point to the currently used version. Upgrading the software:

1. Download the new version into the respective directory
2. Migrate the config.json
3. Update the `insert-name-here-cli.sh` to point to the new version
4. Call `insert-name-here-cli start` using the `at in 1 minute` command
5. Call `sys.exit()`
