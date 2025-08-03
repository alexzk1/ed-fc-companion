import sys
import os

from ui_frame import MainUiFrame

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "ed-fc-cargo-tracker-lib")
)

from _logger import logger
from _logger import plugin_name
from typing import Any
from typing import Optional

_main_frame: MainUiFrame | None = None


def plugin_start3(plugin_dir: str) -> str:
    logger.debug("Loading plugin")
    return plugin_name


def journal_entry(
    cmdr: str,
    is_beta: bool,
    system: Optional[str],
    station: Optional[str],
    entry: dict[str, Any],
    state: dict[str, Any],
) -> None:
    global _main_frame
    if _main_frame:
        _main_frame.journal_entry(cmdr, is_beta, system, station, entry, state)


# def plugin_prefs(parent, cmdr, is_beta):
#     return nb.Frame()


# def prefs_changed(cmdr, is_beta):
#     pass


def plugin_app(parent: Any):
    global _main_frame
    _main_frame = MainUiFrame(parent)
    return _main_frame
