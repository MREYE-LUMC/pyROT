"""Logging helpers for Pyrot.

Provides a custom logging handler that displays messages in a message box,
to make sure that important warnings and errors are noticed by the user.
"""

from __future__ import annotations

import logging
from logging import LogRecord, StreamHandler

import clr

clr.AddReference("System.Windows.Forms")

from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon  # noqa: E402


class PyrotMessageBoxHandler(StreamHandler):
    """Logging handler that shows a message box for warnings and errors."""

    def __init__(self, minimum_level: int = logging.WARNING) -> None:
        """Initialize the handler with a minimum logging level."""
        super().__init__()
        self.setLevel(minimum_level)

    def emit(self, record: LogRecord) -> None:
        """Emit a log record by showing a message box."""
        message = record.getMessage()
        message += (
            f"\n\nSource: {record.pathname}:{record.lineno}.\nCheck the script execution details for more information."
        )
        self.show_message_box(title=record.levelname.title(), message=message, level=record.levelname)

    @staticmethod
    def show_message_box(title: str, message: str, level: str) -> None:
        """Show a message box with the given title and message."""

        level = level.lower()

        if level == "warning":
            icon = MessageBoxIcon.Warning
        elif level in {"error", "critical"}:
            icon = MessageBoxIcon.Error
        else:
            icon = MessageBoxIcon.Information

        buttons = MessageBoxButtons.OK

        MessageBox.Show(message, title, buttons, icon)
