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

The `insert-name-here-cli.sh` will point to the currently used version.

Upgrading the software:

1. Downloading the new version into the respective directory
2. Updating the `insert-name-here-cli.sh` to point to the new version
3. Calling `insert-name-here-cli start` using the `at in 1 minute` command
4. Calling `sys.exit()`
