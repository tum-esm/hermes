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
import time
from typing import Callable, Literal

from src import custom_types, utils, hardware

NAME = "hermes"
REPOSITORY = f"tum-esm/{NAME}"
ROOT_PATH = os.environ.get(
    "HERMES_DEPLOYMENT_ROOT_PATH", f"{os.environ['HOME']}/Documents/{NAME}"
)

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

    def __init__(self, config: custom_types.Config, simulate: bool = False) -> None:
        self.logger = utils.Logger(origin="configuration-procedure")
        self.config = config
        self._remove_old_venvs()
        self.message_queue = utils.MessageQueue()

        try:
            self.hardware_interface = hardware.HardwareInterface(
                config, simulate=simulate
            )
        except Exception as e:
            self.logger.exception(
                e, label="could not initialize hardware interface", config=config
            )
            raise e

    def run(self, config_request: custom_types.MQTTConfigurationRequest) -> None:

        # validate that upgrade is executed by latest sw version
        # TODO: why is this needed?
        if code_path(self.config.version) != PROJECT_DIR:
            self.logger.info(
                "skipping upgrade because executed code is not in default directory",
                config=self.config,
                details=(
                    f'current directory = "{PROJECT_DIR}", '
                    + f'expected directory = "{code_path(self.config.version)}"'
                ),
            )
            return

        state = utils.StateInterface.read()
        current_revision = state.current_config_revision
        new_revision = config_request.revision
        new_version = config_request.configuration.version

        # check if config has a newer revision
        if current_revision >= new_revision:
            self.logger.info(
                "received config revision is not newer",
                details=f"received revision = {new_revision}, current revision = {current_revision}",
            )
            return

        self.logger.info(
            message=f"upgrading to revision {new_revision}. using config {json.dumps(config_request.configuration.dict(), indent=4)}",
            config=self.config,
        )

        # shut down hardware interface before config update
        # this allows the pytests to test the new config on local hardware
        try:
            self.hardware_interface.teardown()
        except Exception as e:
            self.logger.exception(
                e,
                "error in hardware-teardown before configuration procedure",
                config=self.config,
            )
            exit(1)

        # True: parameter update without version update
        # False: version update (+ parameter update)
        has_same_directory = PROJECT_DIR == code_path(new_version)

        try:
            # parameter update without version update
            if has_same_directory:
                # create a tmp file to store current config
                store_current_config()
                self._update_state_file(new_revision)
                self._set_up_local_files(config_request)
                self._run_pytests(new_version)
            # version update (+ parameter update)
            else:
                self._download_code(new_version)
                self._set_up_venv(new_version)
                self._update_state_file(new_revision)
                self._set_up_local_files(config_request)
                self._run_pytests(new_version)
                self._update_cli_pointer(new_version)
                self._empty_message_queue()

            # send UPGRADE SUCCESS message
            self.message_queue.enqueue_message(
                self.config,
                custom_types.MQTTAcknowledgmentMessageBody(
                    revision=new_revision,
                    timestamp=time.time(),
                    success=True,
                ),
            )

            # stop execution and wait for restart by cron job
            # the restart will initialise with the new config
            exit(0)

        # This exception is reached if the config update fails and returns
        # to calling function
        except Exception as e:
            if has_same_directory:
                restore_current_config()

            # Revert to last valid revision in state file
            state = utils.StateInterface.read()
            state.current_config_revision = current_revision
            utils.StateInterface.write(state)

            self.logger.exception(
                e,
                label=f"exception during upgrade",
                config=self.config,
            )

            self.logger.info(
                f"continuing with current revision {state.current_config_revision} "
                + f"and version {self.config.version}"
            )

            # send UPGRADE FAILED message
            self.message_queue.enqueue_message(
                self.config,
                custom_types.MQTTAcknowledgmentMessageBody(
                    revision=new_revision,
                    timestamp=time.time(),
                    success=False,
                ),
            )

            raise e

    def _download_code(self, version: str) -> None:
        """uses the GitHub CLI to download the code for a specific release"""
        if os.path.isdir(code_path(version)):
            self.logger.info("code directory already exists")
            return

        # download release using the GitHub cli
        self.logger.info("downloading code from GitHub")
        utils.run_shell_command(
            f"wget https://github.com/tum-esm/hermes/archive/refs/tags/{tarball_name(version)}"
        )

        # extract code archive
        self.logger.info("extracting tarball")
        utils.run_shell_command(f"tar -xf {tarball_name(version)}")

        # move sensor subdirectory
        self.logger.info("copying sensor code")

        if os.path.exists(f"{tarball_content_name(version)}/sensor"):
            shutil.move(
                f"{tarball_content_name(version)}/sensor",
                code_path(version),
            )
        elif os.path.exists(f"{tarball_content_name(version)}/edge-node"):
            shutil.move(
                f"{tarball_content_name(version)}/edge-node",
                code_path(version),
            )
        else:
            self.logger.info(
                message=f"Failed to extract edge node software from download.",
                config=self.config,
            )
            exit(1)

        # remove download assets
        self.logger.info("removing artifacts")
        os.remove(tarball_name(version))
        shutil.rmtree(tarball_content_name(version))

        self.logger.info(
            f"download was successful",
            config=self.config,
        )

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

        self.logger.info(
            f"set up new virtual environment was successful",
            config=self.config,
        )

    def _set_up_local_files(
        self,
        config_request: custom_types.MQTTConfigurationRequest,
    ) -> None:
        """write new config to json file, copy .env, copy state file"""

        # config.json
        self.logger.info("dumping config.json file")
        with open(
            f"{code_path(config_request.configuration.version)}/config/config.json",
            "w",
        ) as f:
            json.dump(
                {
                    **config_request.configuration.dict(),
                },
                f,
                indent=4,
            )

        # .env file
        self.logger.info("copying .env file")
        src = f"{PROJECT_DIR}/config/.env"
        dst = f"{code_path(config_request.configuration.version)}/config/.env"
        if not os.path.isfile(dst):
            shutil.copy(src, dst)

        # state.json
        self.logger.info("copying state.json file")
        src = f"{PROJECT_DIR}/config/state.json"
        dst = f"{code_path(config_request.configuration.version)}/config/state.json"
        if os.path.isfile(src) and (not os.path.isfile(dst)):
            shutil.copy(src, dst)

    def _run_pytests(
        self,
        version: str,
    ) -> None:
        """run pytests for the new version. The tests should only ensure that
        the new software starts up and is able to perform new confi requests"""

        self.logger.debug(f"running all upgrading pytests")
        utils.run_shell_command(
            f'.venv/bin/python -m pytest -m "remote_update" tests/',
            working_directory=code_path(version),
        )

        if self.config.active_components.run_hardware_tests:
            self.logger.debug(f"running all hardware interface pytests")
            utils.run_shell_command(
                f'.venv/bin/python -m pytest -m "hardware_interface" tests/',
                working_directory=code_path(version),
            )

        self.logger.info(
            f"tests were successful",
            config=self.config,
        )

    def _update_cli_pointer(self, version: str) -> None:
        """make the file pointing to the used cli to the new version's cli"""
        with open(f"{ROOT_PATH}/{NAME}-cli.sh", "w") as f:
            f.write(
                "set -o errexit\n\n"
                + f"{venv_path(version)}/bin/python "
                + f"{code_path(version)}/cli/main.py $*"
            )
        self.logger.info(
            f"switched CLI pointer successfully",
            config=self.config,
        )

    def _remove_old_venvs(self) -> None:
        venvs_to_be_removed: list[str] = []
        version_regex_pattern = re.compile(r"^\d+\.\d+\.\d+(-(alpha|beta)\.\d+)?$")
        for old_version in os.listdir(ROOT_PATH):
            old_venv_path = os.path.join(ROOT_PATH, old_version, ".venv")
            if not os.path.isdir(old_venv_path):
                continue
            if not version_regex_pattern.match(old_version):
                continue
            if old_version == self.config.version:
                continue
            venvs_to_be_removed.append(old_venv_path)

        for p in venvs_to_be_removed:
            self.logger.debug(f'removing old .venv at path "{p}"')
            shutil.rmtree(p)

        self.logger.info(f"successfully removed all old .venvs")

    def _update_state_file(self, new_revision: int) -> None:
        "Update revision in the state file."

        # Update revision in state file
        state = utils.StateInterface.read()
        state.current_config_revision = new_revision
        utils.StateInterface.write(state)

        self.logger.info(
            f"Updated state file to new revision: {new_revision}",
            config=self.config,
        )

    def _empty_message_queue(self) -> None:
        try:
            self.logger.debug("waiting to send out remaining messages")
            self.message_queue.wait_until_queue_is_empty(timeout=120)
            self.logger.debug("successfully sent out remaining messages")
        except TimeoutError:
            self.logger.debug(
                "sending out remaining messages took more the "
                + "2 minutes continuing anyway",
            )
