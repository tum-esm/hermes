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
import sys
from typing import Callable
from src import custom_types, utils

NAME = "insert-name-here"
REPOSITORY = f"tum-esm/{NAME}"
ROOT_PATH = f"$HOME/Documents/{NAME}"

tarball_path: Callable[[str], str] = lambda version: f"{NAME}-{version}.tar.gz"
tarball_content_path: Callable[[str], str] = lambda version: f"{NAME}-{version}"
code_path: Callable[[str], str] = lambda version: f"{ROOT_PATH}/{version}"
venv_path: Callable[[str], str] = lambda version: f"{ROOT_PATH}/{version}/.venv"


def clear_path(path: str) -> bool:
    """remove a file or directory, returns true if it existed"""
    if os.path.isfile(path):
        os.remove(path)
        return True
    if os.path.isdir(path):
        shutil.rmtree(path)
        return True
    return False


class ConfigurationProcedure:
    """runs when a config change has been requested"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(origin="configuration-procedure")
        self.config = config

    def run(self, mqtt_request: custom_types.MQTTConfigurationRequest) -> None:
        version = mqtt_request.configuration.version

        self._download_code(version)
        self._set_up_venv(version)
        self._dump_new_config(mqtt_request)

        try:
            self._run_pytests(version)
            # TODO: emit test success message
            self._update_cli_pointer(version)
            # TODO: emit pointer update success message
            sys.exit()
        except Exception as e:
            # TODO: emit error message
            pass

    def _download_code(self, version: str) -> None:
        """uses the GitHub CLI to download the code for a specific release"""
        if clear_path(code_path(version)):
            self.logger.info("removed old code")

        # download release using the github cli
        utils.run_shell_command(
            f"gh release download --repo={REPOSITORY} --archive=tar.gz v{version}",
        )

        # extract code archive
        utils.run_shell_command(f"tar -xf {tarball_path(version)}")

        # move sensor subdirectory
        shutil.move(
            f"{tarball_content_path(version)}/sensor",
            code_path(version),
        )

        # remove download assets
        os.remove(tarball_path(version))
        shutil.rmtree(tarball_content_path(version))

    def _set_up_venv(self, version: str) -> None:
        """set up a virtual python3.9 environment inside the version subdirectory"""
        if clear_path(venv_path(version)):
            self.logger.info("removed old virtual environment")

        # create virtual environment
        utils.run_shell_command(f"python3.9 -m venv {venv_path(version)}")

        # install dependencies
        utils.run_shell_command(f"poetry install", working_directory=code_path(version))

    def _dump_new_config(
        self, mqtt_request: custom_types.MQTTConfigurationRequest
    ) -> None:
        """write new config config to json file"""

        with open(
            f"{code_path(mqtt_request.configuration.version)}/config/config.json",
            "w",
        ) as f:
            json.dump(
                {
                    "revision": mqtt_request.revision,
                    **mqtt_request.configuration.dict(),
                },
                f,
                indent=4,
            )

    def _run_pytests(self, version: str) -> None:
        """run all pytests for the new version. The pytest tests should
        ensure that everything is running. If the new version's code doesn't
        run properly, there should be more pytests."""

        utils.run_shell_command(
            f"{venv_path(version)}/bin/python -m pytest tests/",
            working_directory=code_path(version),
        )

    def _update_cli_pointer(self, version: str) -> None:
        """make the file pointing to the used cli to the new version's cli"""
        with open(f"{ROOT_PATH}/{NAME}-cli.sh", "w") as f:
            f.write(
                "set -o errexit\n\n"
                + f"{venv_path(version)}/bin/python "
                + f"{code_path(version)}/cli/main.py $*"
            )
