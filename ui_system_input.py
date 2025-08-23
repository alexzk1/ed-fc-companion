import tkinter as tk
from tkinter import ttk
from typing import Optional, Protocol
import translation
from ui_tooltip import Tooltip


class SystemNamesReceiver:
    """
    Signal from plugin/game to UiSystemInput which means some option(s) for user to pick one is(are) ready.
    """

    def __init__(self):
        super().__init__()
        self._current_system: str = ""
        self._route_navigated_final_system: str = ""
        self._targeted_system: str = ""

    def set_current_system(self, system: Optional[str]):
        if system is not None:
            self._current_system = system

    def set_navigated_final_system(self, system: str):
        self._route_navigated_final_system = system

    def set_targeted_system(self, system: str):
        self._targeted_system = system


class UserProvidedSystemName(Protocol):
    """
    Signal sent by UiSystemInput that user finally provided system name.
    """

    def __call__(self, system_name: str) -> None: ...


class UiSystemInput(tk.Frame, SystemNamesReceiver):
    """
    Small component to receive system name from user in different ways.
    """

    def __init__(
        self,
        on_system_name_ready: UserProvidedSystemName,
        parent_widget=None,  # type: ignore
        **kwargs,  # type: ignore
    ):  # type: ignore
        tk.Frame.__init__(self, parent_widget, **kwargs)  # type: ignore
        SystemNamesReceiver.__init__(self)

        self._on_system_name_ready: UserProvidedSystemName = on_system_name_ready

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)

        self._system_entry_value = tk.StringVar()
        self._system_entry_value.trace_add("write", self._on_system_entry_changed)
        self._debounce_system_entry_after_id = None

        self._system_entry_widget = ttk.Entry(
            self, textvariable=self._system_entry_value, width=15
        )
        self._system_entry_widget.grid(row=0, column=0, padx=0, pady=0, sticky="nw")
        Tooltip(
            self._system_entry_widget,
            translation.ptl("System name where to search the station(s)."),
        )

        btn_paste = ttk.Button(
            self, text=translation.ptl("Paste"), command=self._paste_from_clipboard
        )
        Tooltip(btn_paste, translation.ptl("Paste system name from clipboard."))
        btn_paste.grid(row=0, column=1, padx=0)

        btn_current = ttk.Button(
            self,
            text=translation.ptl("Curr.Sys."),
            command=lambda: self._system_entry_value.set(self._current_system),
        )

        btn_selected = ttk.Button(
            self,
            text=translation.ptl("Next Sys."),
            command=lambda: self._system_entry_value.set(self._targeted_system),
        )
        Tooltip(
            btn_selected,
            translation.ptl("Use currently targeted on map system (next jump system)."),
        )
        btn_selected.grid(row=1, column=2, padx=0)

        Tooltip(btn_current, translation.ptl("Use current system."))
        btn_current.grid(row=0, column=2, padx=0)

        btn_dest = ttk.Button(
            self,
            text=translation.ptl("Nav.Dest."),
            command=lambda: self._system_entry_value.set(
                self._route_navigated_final_system
            ),
        )
        Tooltip(
            btn_dest,
            translation.ptl("Use route destination system (last one on the route)."),
        )
        btn_dest.grid(row=1, column=1, padx=0)

        self.grid(row=0, column=0, sticky="nw", padx=3, pady=3)

    def get_system_name(self) -> str:
        """
        Returns system name user wants to use.
        """
        return self._system_entry_value.get()

    def _paste_from_clipboard(self):
        try:
            clipboard = self.clipboard_get()
            self._system_entry_value.set(clipboard)
        except tk.TclError:
            pass  # Clipboard empty or unavailable

    def _on_system_entry_changed(self, _1: str, _2: str, _3: str):
        if self._debounce_system_entry_after_id is not None:
            self.after_cancel(self._debounce_system_entry_after_id)
            self._debounce_system_entry_after_id = None
        self._debounce_system_entry_after_id = self.after(
            1500, self._debounced_system_entry_callback
        )

    def _debounced_system_entry_callback(self):
        self._debounce_system_entry_after_id = None
        if self._on_system_name_ready:
            self._on_system_name_ready(self._system_entry_value.get())
