import tkinter as tk
from tkinter import ttk


class Tooltip:
    """
    Tooltip for a tkinter widget.
    Shows a small popup label with text on mouse hover, with delay.
    Uses current ttk styling for "TLabel" component.
    """

    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay  # delay in milliseconds before showing tooltip

        self.tipwindow = None
        self._after_id = None

        self.widget.bind("<Enter>", self._schedule)  # type: ignore
        self.widget.bind("<Leave>", self._hide)  # type: ignore
        self.widget.bind("<ButtonPress>", self._hide)  # type: ignore
        self.style = ttk.Style()

    def set_text(self, text: str | None):
        """
        Allows to change existing tooltip's text.
        Set empty string or None to hide tooltip completely.
        """
        self.text = text

    def _schedule(self, event=None):  # type: ignore
        self._unschedule()
        self._after_id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = (  # type: ignore
            self.widget.bbox("insert") if self.widget.bbox("insert") else (0, 0, 0, 0)  # type: ignore
        )  # type: ignore
        x += self.widget.winfo_rootx() + 25  # type: ignore
        y += self.widget.winfo_rooty() + cy + 20  # type: ignore

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")

        bg = self.style.lookup("TLabel", "background") or "#ffffe0"  # type: ignore
        fg = self.style.lookup("TLabel", "foreground") or "black"  # type: ignore
        font = self.style.lookup("TLabel", "font") or None  # type: ignore

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background=bg,  # type: ignore
            foreground=fg,  # type: ignore
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=300,
            font=font,  # type: ignore
        )
        label.pack(ipadx=1)

    def _hide(self, event=None):  # type: ignore
        self._unschedule()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
