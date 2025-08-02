from itertools import accumulate
import tkinter as tk
from typing import Any, Optional, Self
from icons_cache import IconsCache
from theme import theme
from translation import ptl
import tkinter.font as tkfont
import fleetcarriercargo
from _logger import logger


class CanvasTableView:
    _PAD_Y_PER_ROW = 3
    _MIN_CANVAS_HEIGHT = 20
    _MAX_CANVAS_HEIGHT = 400
    _PAD_X_FOR_SCROLL_BAR = 30

    # New column should be added in 3 places: _COLUMNS, _ATTRIBUTES_PER_COL, _COLUMN_WIDTH
    # last column is autoresized to fix
    _COLUMNS = ["name", "amount"]  # Can be used instead indexes.
    _ATTRIBUTES_PER_COL = [
        {"justify": tk.LEFT, "anchor": tk.NW},
        {"justify": tk.RIGHT, "anchor": tk.N},
    ]

    _HEADER_ATTRIBUTES = {"justify": tk.LEFT, "anchor": tk.N}

    def __init__(self, parent: tk.Widget) -> None:
        self._COLUMN_WIDTH: list[int] = [230, 100]

        self.parent_frame = parent
        self.font = tkfont.Font()
        self.frame = tk.Frame(parent, pady=3, padx=3)
        self.frame.grid(sticky=tk.NSEW)
        self.canvas: Optional[tk.Canvas] = None
        self.resizing: bool = False
        self.resizing_y_start: int = 0
        self.resizing_h_start: int = 0
        theme.update(self.frame)
        self._last_width = -1

        self._resize_pending = False
        self.frame.bind("<Configure>", self._on_frame_configure)

        self._COLUMN_OFFSET = list(accumulate([0] + self._COLUMN_WIDTH[:-1]))
        self.frame.after(0, self._delayed_update_column_widths)

    def _on_frame_configure(self, event: Any):
        if not self._resize_pending:
            self._resize_pending = True
            self.frame.after_idle(self._on_resize_done)

    def _on_resize_done(self):
        self._resize_pending = False
        new_width = self.frame.winfo_width()
        if new_width != self._last_width:
            self._last_width = new_width
            self._update_column_widths()

    def _delayed_update_column_widths(self):
        if self.frame.winfo_width() <= 1:
            self.frame.after(50, self._delayed_update_column_widths)
        else:
            self._update_column_widths()

    def _update_column_widths(self):
        total_width = self.frame.winfo_width() - self._PAD_X_FOR_SCROLL_BAR
        logger.debug(
            f"Updating to total_width: {total_width}, {self.parent_frame.winfo_width()}"
        )
        self._COLUMN_WIDTH[-1] = max(0, total_width - self._COLUMN_OFFSET[-1])
        self._TABLE_WIDTH = sum(self._COLUMN_WIDTH)
        logger.debug(
            f"Table width {self._TABLE_WIDTH}, column width: {self._COLUMN_WIDTH[-1]}"
        )
        self.reset()
        self.update_from_carrier()

    def reset(self):
        """
        Empties this object to initial state.
        Call self.update_from_carrier() to fill with data.
        """

        # TODO: make it saved/loaded.
        height_to_set = self._MIN_CANVAS_HEIGHT

        if not self.canvas:
            self.canvas = tk.Canvas(
                self.frame,
                width=self._TABLE_WIDTH,
                height=height_to_set,
                highlightthickness=0,
                scrollregion=(0, 0, self._TABLE_WIDTH, height_to_set),
            )
            self.canvas.pack()
            frame = tk.Frame(self.frame)
            frame.pack(side=tk.RIGHT, fill=tk.Y)
            vbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.canvas.yview)  # type: ignore
            vbar.pack(expand=True, fill=tk.BOTH)
            sizegrip = tk.Label(
                frame, image=IconsCache.icons["resize"], cursor="sizing"
            )
            sizegrip.pack(side=tk.BOTTOM, anchor=tk.SE)
            sizegrip.bind("<ButtonPress-1>", self._start_resize)
            sizegrip.bind("<ButtonRelease-1>", self._stop_resize)
            sizegrip.bind("<Motion>", self._resize_frame)
            self.canvas.config(yscrollcommand=vbar.set)
            self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows/macOS
            self.canvas.bind_all(
                "<Button-4>", self._on_mousewheel_linux
            )  # Linux (scroll up)
            self.canvas.bind_all(
                "<Button-5>", self._on_mousewheel_linux
            )  # Linux (scroll down)
            theme.update(frame)
            theme.update(self.canvas)
        else:
            self.canvas.delete("all")
            self.canvas.config(
                width=self._TABLE_WIDTH,
                height=height_to_set,
                scrollregion=(0, 0, self._TABLE_WIDTH, height_to_set),
            )

    def update_from_carrier(self):
        """
        Main method to display data. It pulls carrier's cargo library, reads current state and displays it.
        """

        def updater(call_sign: str | None, cargo: fleetcarriercargo.CargoTally) -> bool:
            if self.canvas:
                total_rows = 1 + len(cargo)
                self.canvas.delete("all")
                self._draw_cell(0, "name", ptl("Commodity"))
                self._draw_cell(0, "amount", ptl("Amount On Carrier"))
                self.canvas.configure(
                    scrollregion=(
                        0,
                        0,
                        self._TABLE_WIDTH,
                        total_rows * self._get_row_visible_height(),
                    )
                )
                logger.debug(
                    f"We have total rows to draw in table/carrier: {total_rows}."
                )
                row_index = 1
                crop = True  # TODO: make it depend on width
                for cargo_key, amount in cargo.items():
                    self._draw_cell(
                        row_index, "name", cargo_key.market_name(), crop=crop
                    )
                    self._draw_cell(row_index, "amount", amount, crop=crop)
                    row_index += 1
                logger.debug(f"Update finished of {total_rows} rows.")
            return False

        fleetcarriercargo.FleetCarrierCargo.inventory(updater)

    def _get_row_visible_height(self) -> int:
        """
        Returns visible height per row based on current self.font and padding per row.
        """
        return self.font.metrics("linespace") + self._PAD_Y_PER_ROW

    def _draw_cell(
        self,
        row: int,
        col: int | str,
        text: str | int | None = None,
        *,
        crop: bool = False,
    ):
        """Draws single cell, 0-row is assumed as header."""
        if not self.canvas:
            return self

        if isinstance(text, int):
            text = "{:8,d}".format(text)
        if not text or len(text) == 0:
            return self

        if isinstance(col, str):
            col = self._COLUMNS.index(col)

        ellipses = "…"
        measured_width = self.font.measure(text)
        measured_width_ellipses = self.font.measure(ellipses)
        if crop:
            limit_w = self._COLUMN_WIDTH[col] - measured_width_ellipses
            cropped = measured_width > limit_w
            while measured_width > limit_w and text:
                text = text[:-1]
                measured_width = self.font.measure(text)
            if not text:
                return
            if cropped:
                text += ellipses

        y = row * self._get_row_visible_height()
        attr: dict[str, str] = self._ATTRIBUTES_PER_COL[col]
        if row == 0:
            fg = theme.current["highlight"] if theme.current else "blue"  # type: ignore
            attr: dict[str, str] = self._HEADER_ATTRIBUTES
        else:
            fg = theme.current["foreground"] if theme.current else "black"  # type: ignore

        x = self._get_text_x(col, attr)
        self.canvas.create_text(x, y, text=text, fill=fg, **attr)  # type: ignore

    def _start_resize(self, event: tk.Event):
        if self.canvas:
            self.resizing_y_start = event.y_root
            self.resizing_h_start = self.canvas.winfo_height()
            self.resizing = True

    def _stop_resize(self, event: tk.Event):  # pylint: disable=W0613
        self.resizing_y_start = 0
        self.resizing_h_start = 0
        self.resizing = False

    def _resize_frame(self, event: tk.Event):
        if self.resizing and self.canvas:
            delta = self.resizing_y_start - event.y_root
            height = self.resizing_h_start - delta
            height = min(max(height, self._MIN_CANVAS_HEIGHT), self._MAX_CANVAS_HEIGHT)
            self.canvas.config(height=height)

    def _on_mousewheel(self, event: tk.Event) -> None:
        # Windows/macOS: event.delta / 120 → 1 шаг
        if self.canvas:
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _on_mousewheel_linux(self, event: tk.Event) -> None:
        # Linux: Button-4 (up), Button-5 (down)
        if self.canvas:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def _get_text_x(self, col: int, attr: dict[str, str]) -> int:
        x = self._COLUMN_OFFSET[col]
        anchor = attr.get("anchor", tk.NW)
        if anchor == tk.NE:
            x += self._COLUMN_WIDTH[col]
        elif anchor == tk.N:
            x += self._COLUMN_WIDTH[col] // 2
        return x
