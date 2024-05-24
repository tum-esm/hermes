# Tests

## Pytest Marks

- @pytest.mark.hardware_interface
- @pytest.mark.remote_update
- @pytest.mark.github_action

## Additional Info

- The Pytest mark `hardware_interface` can be skipped via the config parameter `run_hardware_tests`
- The Pytest mark `remote_update` is run after every config update
- The Pytest mark `github_action` is run for commits within a pull request or the main branch
