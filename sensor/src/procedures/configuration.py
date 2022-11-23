# a config change has been requested

"""
if not a version upgrade:
1. test new config on local hardware
2. send errors if tests unsuccessful per mqtt, keep old config, exit
3. save new config version

if version upgrade
1. Download the new version into the respective directory
2. Create new .venv
3. Install new dependencies
4. Run tests
5. if tests not successful, send errors, keep old config, exit
6. Update the `insert-name-here-cli.sh` to point to the new version
7. Call `insert-name-here-cli start` using the `at in 1 minute` command
8. Call `sys.exit()`
"""
