import subprocess


def run_shell_command(command: str) -> str:
    p = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout = p.stdout.decode("utf-8", errors="replace")
    stderr = p.stderr.decode("utf-8", errors="replace")

    assert p.returncode == 0, (
        f"command '{command}' failed with exit code "
        + f"{p.returncode}: stderr = '{stderr}'"
    )
    return stdout.strip()
