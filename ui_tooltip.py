import tkinter as tk
from tkinter import ttk


class Tooltip:
    """
    Tooltip for a tkinter widget.
    Shows a small popup label with text on mouse hover, with delay.
    Uses current ttk styling for "TLabel" component.
    """

    def __init__(self, widget: tk.Widget, text: str, delay: int = 350):
        self._widget = widget
        self._text = text
        self._delay = delay  # delay in milliseconds before showing tooltip

        self._tipwindow = None
        self._after_id = None

        self._widget.bind("<Enter>", self._schedule)  # type: ignore
        self._widget.bind("<Leave>", self._hide)  # type: ignore
        self._widget.bind("<ButtonPress>", self._hide)  # type: ignore
        self.style = ttk.Style()

    def set_text(self, text: str | None):
        """
        Allows to change existing tooltip's text.
        Set empty string or None to hide tooltip completely.
        """
        self._text = text

    def _schedule(self, event=None):  # type: ignore
        self._unschedule()
        self._after_id = self._widget.after(self._delay, self._show)

    def _unschedule(self):
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self._tipwindow or not self._text:
            return

        self._tipwindow = tk.Toplevel(self._widget)
        self._tipwindow.wm_overrideredirect(True)

        bg = self.style.lookup("TLabel", "background") or "#ffffe0"  # type: ignore
        fg = self.style.lookup("TLabel", "foreground") or "black"  # type: ignore
        font = self.style.lookup("TLabel", "font") or None  # type: ignore

        label = tk.Label(
            self._tipwindow,
            text=self._text,
            justify=tk.LEFT,
            background=bg,  # type: ignore
            foreground=fg,  # type: ignore
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=300,
            font=font,  # type: ignore
        )
        label.pack(ipadx=1)

        self._tipwindow.update_idletasks()
        tip_w = self._tipwindow.winfo_width()
        tip_h = self._tipwindow.winfo_height()

        screen_w = self._widget.winfo_screenwidth()
        screen_h = self._widget.winfo_screenheight()
        x = self._widget.winfo_pointerx() + 20
        y = self._widget.winfo_pointery() + 15

        # Screen borders guard
        if x + tip_w > screen_w:
            x = screen_w - tip_w - 10
        if y + tip_h > screen_h:
            y = screen_h - tip_h - 10

        self._tipwindow.geometry(f"+{x}+{y}")

    def _hide(self, event=None):  # type: ignore
        self._unschedule()
        if self._tipwindow:
            self._tipwindow.destroy()
            self._tipwindow = None
