from os.path import dirname, abspath, join
import sys
import traceback
from datetime import datetime, timedelta
from typing import Optional

from src import custom_types

from .mqtt_sending import SendingMQTTClient

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOGS_ARCHIVE_DIR = join(PROJECT_DIR, "logs", "archive")
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")

# The logging module behaved very weird with the setup we have
# therefore I am just formatting and appending the log lines
# manually. Doesn't really make a performance difference


def log_line_has_date(log_line: str) -> bool:
    """returns true when a give log line (string) starts
    with a valid date. This is not true for exception
    tracebacks. This log line time is used to determine
    which file to archive logs lines into"""
    try:
        datetime.strptime(log_line[:10], "%Y-%m-%d")
        return True
    except:
        return False


class Logger:
    last_archive_time = datetime.now()

    def __init__(
        self,
        origin: str = "insert-name-here",
        print_to_console: bool = False,
    ) -> None:
        self.origin: str = origin
        self.print_to_console = print_to_console

    def debug(self, message: str) -> None:
        """writes a debug log line, used for verbose output"""
        self._write_log_line("DEBUG", message)

    def info(self, message: str) -> None:
        """writes an info log line"""
        self._write_log_line("INFO", message)

    def warning(
        self, message: str, config: Optional[custom_types.Config] = None
    ) -> None:
        """writes a warning log line, sends the message via
        MQTT when config is passed (required for revision number)
        """
        self._write_log_line("WARNING", message)
        if config is not None:
            SendingMQTTClient.enqueue_message(
                config=config,
                message_body=custom_types.MQTTStatusMessageBody(
                    severity="warning", subject=message, details=""
                ),
            )

    def error(self, message: str, config: Optional[custom_types.Config] = None) -> None:
        """writes an error log line, sends the message via
        MQTT when config is passed (required for revision number)
        """
        self._write_log_line("ERROR", message)
        if config is not None:
            SendingMQTTClient.enqueue_message(
                config=config,
                message_body=custom_types.MQTTStatusMessageBody(
                    severity="error", subject=message, details=""
                ),
            )

    def exception(
        self, e: Exception, config: Optional[custom_types.Config] = None
    ) -> None:
        """logs the traceback of an exception, sends the message via
        MQTT when config is passed (required for revision number)
        """
        exception_name = type(e).__name__
        exception_traceback = "\n".join(traceback.format_exception(*sys.exc_info()))
        self._write_log_line(
            "EXCEPTION", f"{exception_name} occured: {exception_traceback}"
        )
        if config is not None:
            SendingMQTTClient.enqueue_message(
                config=config,
                message_body=custom_types.MQTTStatusMessageBody(
                    severity="error",
                    subject=exception_name,
                    details=exception_traceback,
                ),
            )

    def _write_log_line(self, level: str, message: str) -> None:
        """formats the log line string and writes it to
        `logs/current-logs.log`"""
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
        if self.print_to_console:
            print(log_string, end="")
        else:
            with open(LOG_FILE, "a") as f1:
                f1.write(log_string)

            # Archive lines older than 60 minutes, every 10 minutes
            if (now - Logger.last_archive_time).total_seconds() > 600:
                self._archive()

    def _archive(self) -> None:
        """moves old log lines in "logs/current-logs.log" into an
        archive file "logs/archive/YYYYMMDD.log". log lines from
        the last hour will remain"""

        with open(LOG_FILE, "r") as f:
            log_lines_in_file = f.readlines()
        if len(log_lines_in_file) == 0:
            return

        lines_to_be_kept, lines_to_be_archived = [], []
        latest_time = str(datetime.now() - timedelta(hours=1))
        line_time = log_lines_in_file[0][:26]
        for index, line in enumerate(log_lines_in_file):
            if log_line_has_date(line):
                line_time = line[:26]
            if line_time > latest_time:
                lines_to_be_archived = log_lines_in_file[:index]
                lines_to_be_kept = log_lines_in_file[index:]
                break

        with open(LOG_FILE, "w") as f:
            f.writelines(lines_to_be_kept)

        if len(lines_to_be_archived) == 0:
            return

        archive_log_date_groups: dict[str, list[str]] = {}
        line_date = lines_to_be_archived[0][:10].replace("-", "")
        for line in lines_to_be_archived:
            if log_line_has_date(line):
                line_date = line[:10].replace("-", "")
            if line_date not in archive_log_date_groups.keys():
                archive_log_date_groups[line_date] = []
            archive_log_date_groups[line_date].append(line)

        for date in archive_log_date_groups.keys():
            filename = join(LOGS_ARCHIVE_DIR, f"{date}.log")
            with open(filename, "a") as f:
                f.writelines(archive_log_date_groups[date] + [""])

        Logger.last_archive_time = datetime.now()
