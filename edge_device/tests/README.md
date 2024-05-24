# Tests

## Pytest Marks

- @pytest.mark.hardware_interface
- @pytest.mark.remote_update
- @pytest.mark.github_action

## Additional Info

- The Pytest mark `hardware_interface` can be skipped via the config parameter `run_hardware_tests`
- The Pytest mark `remote_update` is run after every config update
- The Pytest mark `github_action` is run for commits within a pull request or the main branch

**Run tests/check static types:**

```bash
# all tests
pytest --cov=src --cov=cli tests/

# only github_action tests
pytest -m "github_action" --cov=src --cov=cli tests/

# only remote_update tests
pytest -m "remote_update" --cov=src --cov=cli tests/

# only hardware interface tests
pytest -m "hardware_interface" --cov=src --cov=cli tests/

#test static types
bash ./scripts/check_static_types.sh
```
