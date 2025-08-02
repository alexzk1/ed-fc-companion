import sys
import os

from ui_frame import MainUiFrame

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "ed-fc-cargo-tracker-lib")
)

from _logger import logger
from _logger import plugin_name
from typing import Any
from typing import Dict, Optional

this = sys.modules[__name__]


def plugin_start3(plugin_dir: str) -> str:
    logger.debug("Loading plugin")
    return plugin_name


def journal_entry(
    cmdr: str,
    is_beta: bool,
    system: Optional[str],
    station: Optional[str],
    entry: Dict[str, Any],
    state: Dict[str, Any],
) -> None:
    pass


# def plugin_prefs(parent, cmdr, is_beta):
#     return nb.Frame()


# def prefs_changed(cmdr, is_beta):
#     pass


def plugin_app(parent: Any):
    return MainUiFrame(parent)
