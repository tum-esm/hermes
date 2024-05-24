## Installation

**Set up virtual environment and install dependencies:**

```bash
python3.9 -m venv .venv
source .venv/bin/activate
poetry install --with=dev
```

## System release & update process

1. Create a new release

   1. Merge all changes into the `main` branch
   2. Check whether the GitHub CI tests were successful for this commit
   3. Tag the commit as `v0.1.0-beta.3` (or whatever the new version is)
   4. Create a release on GitHub with the same tag (`v0.1.0-beta.3`)
   5. Write release notes

2. Update the `config.json` that is sent to the system

   ```json
   {
       "version": "0.1.0-beta.3",
       ...
   }
   ```

3. Wait for the system to confirm the update with new revision

## Visualisation

### Automation

![](../docs//hermes-main-py.png)

### Main Loop

**System Check Procedure**

![](../docs/procedure-system-check.png)

**Calibration Procedure**

![](../docs/procedure-calibration.png)

**Measurement Procedure**

![](../docs/procedure-measurement.png)

**Configuration Procedure**

![](../docs/procedure-configuration.png)

**Exception Handling**

![](../docs/main-loop-exception-handling.png)
