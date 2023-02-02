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
from typing import Callable
from src import custom_types, utils

NAME = "hermes"
REPOSITORY = f"tum-esm/{NAME}"
ROOT_PATH = f"$HOME/Documents/{NAME}"

tarball_path: Callable[[str], str] = lambda version: f"{NAME}-{version}.tar.gz"
tarball_content_path: Callable[[str], str] = lambda version: f"{NAME}-{version}"
code_path: Callable[[str], str] = lambda version: f"{ROOT_PATH}/{version}"
venv_path: Callable[[str], str] = lambda version: f"{ROOT_PATH}/{version}/.venv"

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
CURRENT_CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")
CURRENT_TMP_CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.tmp.json")


def clear_path(path: str) -> bool:
    """remove a file or directory, returns true if it existed"""
    if os.path.isfile(path):
        os.remove(path)
        return True
    if os.path.isdir(path):
        shutil.rmtree(path)
        return True
    return False


# TODO: do not try an upgrade to a specific revision twice


def overwrite_file(src_path, dst_path) -> None:
    if os.path.isfile(dst_path):
        os.remove(dst_path)
    os.rename(src_path, dst_path)


class ConfigurationProcedure:
    """runs when a config change has been requested"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(origin="configuration-procedure")
        self.config = config

    def run(self, config_request: custom_types.MQTTConfigurationRequest) -> None:
        new_revision = config_request.revision
        new_version = config_request.configuration.version

        self.logger.info(
            f"upgrading to new revision {new_revision} and version {new_version}"
        )

        same_version_and_directory = (self.config.version == new_version) and (
            PROJECT_DIR == code_path(new_version)
        )
        if same_version_and_directory:
            overwrite_file(CURRENT_CONFIG_PATH, CURRENT_TMP_CONFIG_PATH)

        if not same_version_and_directory:
            self._download_code(new_version)
            self._set_up_venv(new_version)
            self._dump_new_config(config_request)

        try:
            self._run_pytests(new_version)
        except Exception as e:
            self.logger.error(
                f"exception during pytest upgrade to revision {new_revision}",
                config=self.config,
            )
            self.logger.exception(e, config=self.config)
            if same_version_and_directory:
                overwrite_file(CURRENT_TMP_CONFIG_PATH, CURRENT_CONFIG_PATH)
            self.logger.error(
                f"continuing with current revision {self.config.revision} "
                + "and version {self.config.version}"
            )
            return

        self.logger.info(f"tests for revision {new_revision} successful")
        self._update_cli_pointer(new_version)
        self.logger.info(f"switched CLI pointer to revision {new_revision}")

        exit(0)

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
        self.logger.info(f"setting up Python for version {version}")

        if os.path.isdir(venv_path(version)):
            shutil.rmtree(venv_path(version))
        utils.run_shell_command(
            f"python3.9 -m venv .venv",
            working_directory=code_path(version),
        )
        utils.run_shell_command(
            f"souce .venv/bin/activate && poetry install",
            working_directory=code_path(version),
        )

    def _dump_new_config(
        self,
        config_request: custom_types.MQTTConfigurationRequest,
    ) -> None:
        """write new config config to json file"""

        self.logger.info(
            f"dumping config for version {config_request.configuration.version}"
        )

        with open(
            f"{code_path(config_request.configuration.version)}/config/config.json",
            "w",
        ) as f:
            json.dump(
                {
                    "revision": config_request.revision,
                    **config_request.configuration.dict(),
                },
                f,
                indent=4,
            )

    def _run_pytests(self, version: str) -> None:
        """run pytests for the new version. The tests should only ensure that
        the new software starts up and is able to perform new confi requests"""
        self.logger.info(f"running pytests for version {version}")
        utils.run_shell_command(
            f'.venv/bin/python -m pytest -m "configuration_procedure" tests/',
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
