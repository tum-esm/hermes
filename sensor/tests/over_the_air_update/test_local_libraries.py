import pytest


@pytest.mark.over_the_air_update
def test_local_libraries() -> None:
    """checks whether the raspberry pi specific libraries can be loaded"""

    import board
    import RPi.GPIO
