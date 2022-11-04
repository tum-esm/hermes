import os
import traceback
from datetime import datetime, timedelta

from src import types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(dir(os.path.abspath(__file__)))))
LOGS_DIR = os.path.join(PROJECT_DIR, "logs")

# The logging module behaved very weird with the setup we have
# therefore I am just formatting and appending the log lines
# manually. Doesn't really make a performance difference


def log_line_has_time(log_line: str) -> bool:
    """Returns true when a give log line (string) starts
    with a valid date. This is not true for exception
    tracebacks. This log line time is used to determine
    which file to archive logs lines into."""
    try:
        assert len(log_line) >= 10
        datetime.strptime(log_line[:10], "%Y-%m-%d")
        return True
    except:
        return False


class Logger:
    last_archive_time = datetime.now()

    def __init__(self, config: types.Config, origin: str = "pyra.core") -> None:
        self.origin: str = origin
        self.config: types.Config = config
        self.log_file_slug: str = f"sensor-node-{config.general.node_id}"

    def debug(self, message: str) -> None:
        """Write a debug log (to debug only). Used for verbose output"""
        self._write_log_line("DEBUG", message)

    def info(self, message: str) -> None:
        """Write an info log (to debug and info)"""
        self._write_log_line("INFO", message)

    def warning(self, message: str) -> None:
        """Write a warning log (to debug and info)"""
        self._write_log_line("WARNING", message)

    def error(self, message: str) -> None:
        """Write an error log (to debug and info)"""
        self._write_log_line("ERROR", message)

    def exception(self, e: Exception) -> None:
        """Log the traceback of an exception"""
        tb = "\n".join(traceback.format_exception(e))
        self._write_log_line("EXCEPTION", f"{type(e).__name__} occured: {tb}")

    def _write_log_line(self, level: str, message: str) -> None:
        """Format the log line string and write it to "logs/debug.log"
        and possibly "logs/info.log"""
        now = datetime.now()
        utc_offset = round(
            (datetime.now() - datetime.utcnow()).total_seconds() / 3600, 1
        )
        if round(utc_offset) == utc_offset:
            utc_offset = round(utc_offset)

        log_string = (
            f"{now} UTC{'' if utc_offset < 0 else '+'}{utc_offset} "
            + f"- {self.origin} - {level} - {message}\n"
        )
        with open(os.path.join(LOGS_DIR, f"{self.log_file_slug}.log"), "a") as f1:
            f1.write(log_string)

        # Archive lines older than 60 minutes, every 10 minutes
        if (now - Logger.last_archive_time).total_seconds() > 600:
            self.archive()
            Logger.last_archive_time = now

    def archive(self) -> None:
        """
        Move old log lines in "logs/sensor-node-{sensor_node_id}.log" into an
        archive file "logs/archive/sensor-node-{sensor_node_id}-YYYYMMDD.log".

        Log lines from the last hour will remain.
        """

        with open(os.path.join(LOGS_DIR, f"{self.log_file_slug}.log"), "r") as f:
            log_lines_in_file = f.readlines()
        if len(log_lines_in_file) == 0:
            return

        lines_to_be_kept, lines_to_be_archived = [], []
        latest_time = str(datetime.now() - timedelta(hours=1))
        line_time = log_lines_in_file[0][:26]
        for index, line in enumerate(log_lines_in_file):
            if log_line_has_time(line):
                line_time = line[:26]
            if line_time > latest_time:
                lines_to_be_archived = log_lines_in_file[:index]
                lines_to_be_kept = log_lines_in_file[index:]
                break

        with open(os.path.join(LOGS_DIR, f"{self.log_file_slug}.log"), "w") as f:
            f.writelines(lines_to_be_kept)

        if len(lines_to_be_archived) == 0:
            return

        archive_log_date_groups: dict[str, list[str]] = {}
        line_date = lines_to_be_archived[0][:10].replace("-", "")
        for line in lines_to_be_archived:
            if log_line_has_time(line):
                line_date = line[:10].replace("-", "")
            if line_date not in archive_log_date_groups.keys():
                archive_log_date_groups[line_date] = []
            archive_log_date_groups[line_date].append(line)

        for date in archive_log_date_groups.keys():
            filename = os.path.join(
                LOGS_DIR, "archive", f"{self.log_file_slug}-{date}.log"
            )
            with open(filename, "a") as f:
                f.writelines(archive_log_date_groups[date] + [""])
