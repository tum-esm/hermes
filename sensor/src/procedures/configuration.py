"""
if not a version upgrade:
1. test new config on local hardware
2. if tests unsuccessful: send errors per mqtt, keep old config, exit
3. save new config version

if version upgrade
1. Download the new version into the respective directory
2. Create new .venv
3. Install new dependencies
4. Run tests
5. if tests unsuccessful: send errors per mqtt, keep old config, exit
6. Update the `insert-name-here-cli.sh` to point to the new version
7. Call `insert-name-here-cli start` using the `at in 1 minute` command
8. Call `sys.exit()`
"""

import json
import os
import shutil
from src import custom_types, utils

REPOSITORY = "tum-esm/insert-name-here"


class ConfigurationProcedure:
    """runs when a config change has been requested"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(origin="configuration")
        self.config = config

    def run(self, mqtt_request: custom_types.MQTTConfigurationRequest) -> None:
        version = mqtt_request.configuration.version

        self._download_code(version)
        self._set_up_venv(version)
        self._dump_new_config(mqtt_request)

        try:
            self._run_pytests(version)
            # TODO: emitsuccess message
            # TODO: switch cli pointer
        except Exception as e:
            # TODO: emit error message
            pass

    def _download_code(self, version: str) -> None:
        """uses the GitHub CLI to download the code for a specific release"""

        dst_dir = f"$HOME/Documents/insert-name-here/{version}"
        assert not os.path.exists(dst_dir), f'dst directory "{dst_dir}" exists'

        utils.run_shell_command(
            f"gh release download --repo={REPOSITORY} --archive=tar.gz v{version}",
        )
        archive_label = f"insert-name-here-{version}"

        # extract code archive
        utils.run_shell_command(f"tar -xf {archive_label}.tar.gz")

        # move sensor subdirectory
        shutil.move(
            f"{archive_label}/sensor",
            f"$HOME/Documents/insert-name-here/{version}",
        )

        # remove download assets
        os.remove(f"{archive_label}.tar.gz")
        shutil.rmtree(archive_label)

    def _set_up_venv(self, version: str) -> None:
        """set up a virtual python3.9 environment inside the version subdirectory"""

        dst_dir = f"$HOME/Documents/insert-name-here/{version}"

        # create virtual environment
        utils.run_shell_command(f"python3.9 -m venv .venv", working_directory=dst_dir)

        # install dependencies
        utils.run_shell_command(f"poetry install", working_directory=dst_dir)

    def _dump_new_config(
        self, mqtt_request: custom_types.MQTTConfigurationRequest
    ) -> None:
        """write new config config to json file"""

        new_config_path = (
            "$HOME/Documents/insert-name-here/"
            + f"{mqtt_request.configuration.version}/config/config.json"
        )
        with open(new_config_path, "w") as f:
            json.dump(
                {
                    "revision": mqtt_request.revision,
                    **mqtt_request.configuration.dict(),
                },
                indent=4,
            )

    def _run_pytests(self, version: str) -> None:
        """run all pytests for the new version. The pytest tests should
        ensure that everything is running. If the new version's code doesn't
        run properly, there should be more pytests."""

        dst_path = f"$HOME/Documents/insert-name-here/{version}"
        venv_path = f"{dst_path}/.venv/bin/python"
        utils.run_shell_command(
            f"{venv_path} -m pytest tests/", working_directory=dst_path
        )
