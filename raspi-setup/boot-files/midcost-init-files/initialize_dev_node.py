from utils import run_shell_command


# =============================================================================
# Add global git settings

run_shell_command('git config --global core.editor "vim"')
run_shell_command('git config --global core.commentChar "$"')
run_shell_command('git config --global user.name "Moritz Makowski"')
run_shell_command('git config --global user.email "moritz.makowski@tum.de"')
run_shell_command("git config --global pull.ff only")
