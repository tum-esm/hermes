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
import re
import shutil
from typing import Callable, Literal
from src import custom_types, utils

NAME = "hermes"
REPOSITORY = f"tum-esm/{NAME}"
ROOT_PATH = f"{os.environ['HOME']}/Documents/{NAME}"

tarball_name: Callable[[str], str] = lambda version: f"v{version}.tar.gz"
tarball_content_name: Callable[[str], str] = lambda version: f"{NAME}-{version}"
code_path: Callable[[str], str] = lambda version: f"{ROOT_PATH}/{version}"
venv_path: Callable[[str], str] = lambda version: f"{ROOT_PATH}/{version}/.venv"

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
CURRENT_CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")
CURRENT_TMP_CONFIG_PATH = os.path.join(
    PROJECT_DIR, "config", "config.param-change-tmp.json"
)


def clear_path(path: str) -> bool:
    """remove a file or directory, returns true if it existed"""
    if os.path.isfile(path):
        os.remove(path)
        return True
    if os.path.isdir(path):
        shutil.rmtree(path)
        return True
    return False


def store_current_config() -> None:
    if os.path.isfile(CURRENT_TMP_CONFIG_PATH):
        os.remove(CURRENT_TMP_CONFIG_PATH)
    os.rename(CURRENT_CONFIG_PATH, CURRENT_TMP_CONFIG_PATH)


def restore_current_config() -> None:
    assert os.path.isfile(
        CURRENT_TMP_CONFIG_PATH
    ), f"{CURRENT_TMP_CONFIG_PATH} does not exist"
    if os.path.isfile(CURRENT_CONFIG_PATH):
        os.remove(CURRENT_CONFIG_PATH)
    os.rename(CURRENT_TMP_CONFIG_PATH, CURRENT_CONFIG_PATH)


class ConfigurationProcedure:
    """runs when a config change has been requested"""

    @staticmethod
    class ExitOnUpdateSuccess(Exception):
        """raised when mainloop should stop because an update has been successful"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(origin="configuration-procedure")
        self.config = config
        self._remove_old_venvs()

    def run(self, config_request: custom_types.MQTTConfigurationRequest) -> None:
        new_revision = config_request.revision
        new_version = config_request.configuration.version

        if self.config.revision == new_revision:
            self.logger.info("received config has the same revision")
            return

        has_same_directory = PROJECT_DIR == code_path(new_version)

        self.logger.info(
            message=f"upgrading to revision {new_revision}", config=self.config
        )
        self.logger.info(
            message=f"using config {json.dumps(config_request.configuration.dict(), indent=4)}"
        )

        try:
            if has_same_directory:
                store_current_config()
            else:
                self._download_code(new_version)
                self._set_up_venv(new_version)

            self._dump_new_config(config_request)

            self._run_pytests(
                new_version,
                scope=(
                    "parameter-change" if (has_same_directory) else "version-change"
                ),
            )

            self.logger.info(
                f"upgrading to revision {new_revision}: tests were successful",
                config=self.config,
            )

            self._update_cli_pointer(new_version)
            self.logger.info(
                f"upgrading to revision {new_revision}: switched CLI pointer successfully",
                config=self.config,
            )

            if has_same_directory:
                restore_current_config()

            raise ConfigurationProcedure.ExitOnUpdateSuccess()

        except ConfigurationProcedure.ExitOnUpdateSuccess as e:
            raise e

        except Exception as e:
            self.logger.error(
                f"upgrading to revision {new_revision}: exception during upgrade",
                config=self.config,
            )
            self.logger.exception(config=self.config)

        if has_same_directory:
            restore_current_config()
        self.logger.info(
            f"continuing with current revision {self.config.revision} "
            + f"and version {self.config.version}"
        )

    def _download_code(self, version: str) -> None:
        """uses the GitHub CLI to download the code for a specific release"""
        if os.path.isdir(code_path(version)):
            self.logger.info("code directory already exists")
            return

        # download release using the github cli
        self.logger.info("downloading code from GitHub")
        utils.run_shell_command(
            f"wget https://github.com/tum-esm/hermes/archive/refs/tags/{tarball_name(version)}"
        )

        # extract code archive
        self.logger.info("extracting tarball")
        utils.run_shell_command(f"tar -xf {tarball_name(version)}")

        # move sensor subdirectory
        self.logger.info("copying sensor code")
        shutil.move(
            f"{tarball_content_name(version)}/sensor",
            code_path(version),
        )

        # remove download assets
        self.logger.info("removing artifacts")
        os.remove(tarball_name(version))
        shutil.rmtree(tarball_content_name(version))

    def _set_up_venv(self, version: str) -> None:
        """set up a virtual python3.9 environment inside the version subdirectory"""
        if os.path.isdir(venv_path(version)):
            self.logger.info("venv already exists")
            return

        self.logger.info(f"setting up new venv")
        utils.run_shell_command(
            f"python3.9 -m venv .venv",
            working_directory=code_path(version),
        )

        self.logger.info(f"installing dependencies")
        utils.run_shell_command(
            f"source .venv/bin/activate && poetry install",
            working_directory=code_path(version),
        )

    def _dump_new_config(
        self,
        config_request: custom_types.MQTTConfigurationRequest,
    ) -> None:
        """write new config config to json file"""

        self.logger.info("dumping config.json file")
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

        self.logger.info("copying .env file")
        src = f"{PROJECT_DIR}/config/.env"
        dst = f"{code_path(config_request.configuration.version)}/config/.env"
        if not os.path.isfile(dst):
            shutil.copy(src, dst)

    def _run_pytests(
        self,
        version: str,
        scope: Literal["version-change", "parameter-change"],
    ) -> None:
        """run pytests for the new version. The tests should only ensure that
        the new software starts up and is able to perform new confi requests"""
        if scope == "parameter-change":
            self.logger.debug(f"only validating config")
            utils.run_shell_command(
                f'.venv/bin/python -m pytest -m "parameter_update" tests/',
                working_directory=code_path(version),
            )
        else:
            self.logger.debug(f"running all upgrading pytests")
            utils.run_shell_command(
                f'.venv/bin/python -m pytest -m "version_update" tests/',
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

    def _remove_old_venvs(self) -> None:
        venvs_to_be_removed: list[str] = []
        version_regex_pattern = re.compile(r"^\d+\.\d+\.\d+(-(alpha|beta)\.\d+)?$")
        for old_version in os.listdir(ROOT_PATH):
            venv_path = os.path.join(ROOT_PATH, old_version, ".venv")
            if not os.path.isdir(venv_path):
                continue
            if not version_regex_pattern.match(old_version):
                continue
            if old_version == self.config.version:
                continue
            venvs_to_be_removed.append(venv_path)

        for p in venvs_to_be_removed:
            self.logger.info(f'removing old .venv at path "{p}"', config=self.config)
            shutil.rmtree(p)

        self.logger.info(f"successfully removed all old .venvs", config=self.config)
