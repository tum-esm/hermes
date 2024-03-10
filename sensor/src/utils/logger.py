import time
import traceback
from datetime import datetime
from os.path import dirname, abspath, join
from typing import Literal, Optional

import filelock

from src import custom_types, utils
from .functions import CommandLineException
from .message_queue import MessageQueue

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOGS_ARCHIVE_DIR = join(PROJECT_DIR, "logs", "archive")
FILELOCK_PATH = join(PROJECT_DIR, "logs", "archive.lock")

# The logging module behaved very weird with the setup we have
# therefore I am just formatting and appending the log lines
# manually. Doesn't really make a performance difference


def _pad_str_right(
    text: str, min_width: int, fill_char: Literal["0", " "] = " "
) -> str:
    if len(text) >= min_width:
        return text
    else:
        return text + (fill_char * (min_width - len(text)))


class Logger:
    def __init__(
        self,
        origin: str = "insert-name-here",
        print_to_console: bool = False,
        write_to_file: bool = True,
    ) -> None:
        self.origin: str = origin
        self.print_to_console = print_to_console
        self.write_to_file = write_to_file
        self.message_queue = MessageQueue()
        self.filelock = filelock.FileLock(FILELOCK_PATH, timeout=3)

    def horizontal_line(self, fill_char: Literal["-", "=", ".", "_"] = "=") -> None:
        """writes a debug log line, used for verbose output"""
        self._write_log_line("INFO", fill_char * 46)

    def debug(self, message: str) -> None:
        """writes a debug log line, used for verbose output"""
        self._write_log_line("DEBUG", message)

    def info(
        self,
        message: str,
        config: Optional[custom_types.Config] = None,
        details: str = "",
    ) -> None:
        """writes an info log line, sends the message via
        MQTT when config is passed (required for revision number)"""
        if len(details) == 0:
            self._write_log_line("INFO", message)
        else:
            self._write_log_line("INFO", f"{message}, details: {details}")
        if config is not None:
            self._write_mqtt_message(
                config,
                level="info",
                subject=message,
                details=details,
            )

    def warning(
        self,
        message: str,
        config: Optional[custom_types.Config] = None,
        details: str = "",
    ) -> None:
        """writes a warning log line, sends the message via
        MQTT when config is passed (required for revision number)
        """
        if len(details) == 0:
            self._write_log_line("WARNING", message)
        else:
            self._write_log_line("WARNING", f"{message}, details: {details}")
        if config is not None:
            self._write_mqtt_message(
                config,
                level="warning",
                subject=message,
            )

    def error(
        self,
        message: str,
        config: Optional[custom_types.Config] = None,
        details: str = "",
    ) -> None:
        """writes an error log line, sends the message via
        MQTT when config is passed (required for revision number)
        """
        if len(details) == 0:
            self._write_log_line("ERROR", message)
        else:
            self._write_log_line(
                "ERROR",
                "\n".join(
                    [
                        message,
                        "--- details: -----------------",
                        details,
                        "------------------------------",
                    ]
                ),
            )
        if config is not None:
            self._write_mqtt_message(
                config, level="error", subject=message, details=details
            )

    def exception(
        self,
        e: Exception,
        label: Optional[str] = None,
        config: Optional[custom_types.Config] = None,
    ) -> None:
        """logs the traceback of an exception, sends the message via
        MQTT when config is passed (required for revision number).

        exceptions will be formatted like this:

        ```txt
        (label, )ZeroDivisionError: division by zer
        --- details: -----------------
        ...
        --- traceback: ---------------
        ...
        ------------------------------
        ```
        """
        exception_name = traceback.format_exception_only(type(e), e)[0].strip()
        exception_traceback = "\n".join(
            traceback.format_exception(type(e), e, e.__traceback__)
        ).strip()
        exception_details = "None"
        if isinstance(e, CommandLineException) and (e.details is not None):
            exception_details = e.details.strip()

        subject_string = (
            exception_name if label is None else f"{label}, {exception_name}"
        )
        details_string = (
            f"--- details: -----------------\n"
            + f"{exception_details}\n"
            + f"--- traceback: ---------------\n"
            + f"{exception_traceback}\n"
            + f"------------------------------"
        )

        self._write_log_line("EXCEPTION", f"{subject_string}\n{details_string}")
        if config is not None:
            self._write_mqtt_message(
                config,
                level="error",
                subject=subject_string,
                details=details_string,
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
            f"{str(now)[:-3]} UTC{'' if utc_offset < 0 else '+'}{utc_offset} "
            + f"- {_pad_str_right(self.origin, min_width=23)} "
            + f"- {_pad_str_right(level, min_width=13)} "
            + f"- {message}\n"
        )
        if self.print_to_console:
            print(log_string, end="")
        if self.write_to_file:
            # YYYY-MM-DD.log
            log_file_name = str(now)[:10] + ".log"
            with self.filelock:
                with open(join(LOGS_ARCHIVE_DIR, log_file_name), "a") as f1:
                    f1.write(log_string)

    def _write_mqtt_message(
        self,
        config: custom_types.Config,
        level: Literal["info", "warning", "error"],
        subject: str,
        details: str = "",
    ) -> None:
        subject = f"{self.origin} - {subject}"

        # TODO: refactor the split of subject and detail to only one message
        if len(subject) > 256:
            extension_message_subject = f" ... CUT ({len(subject)} -> 256)"
            subject = (
                subject[: (256 - len(extension_message_subject))]
                + extension_message_subject
            )

        if len(details) > 16384:
            extension_message_details = f" ... CUT ({len(details)} -> 16384)"
            details = (
                details[: (16384 - len(extension_message_details))]
                + extension_message_details
            )

        state = utils.StateInterface.read()

        self.message_queue.enqueue_message(
            config,
            message_body=custom_types.MQTTLogMessageBody(
                severity=level,
                message=subject + " " + details,
                timestamp=round(time.time(), 2),
                revision=state.current_config_revision,
            ),
        )
