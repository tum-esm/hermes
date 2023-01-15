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

import os
import shutil
import requests
from src import custom_types, utils

# TODO: statically type config request message
# TODO: create new venv
# TODO: install new dependencies
# TODO: run tests on the new version

REPOSITORY = "tum-esm/insert-name-here"


class ConfigurationProcedure:
    """runs when a config change has been requested"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(origin="configuration")
        self.config = config

    def run(self, mqtt_request: str) -> None:
        self._download_code("v1.0.0-alpha.1")
        # TODO: implement configuration procedure

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
