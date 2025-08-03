from itertools import accumulate
import tkinter as tk
from typing import Any, Optional
from carrier_cargo_position import CarrierCargoPosition
from icons_cache import IconsCache
from rows_rclick_menu import RightClickContextMenuForTable
from sell_on_station import FilterSellOnDockedStation, FilterSellOnStationProtocol
from theme import theme
from translation import ptl
import tkinter.font as tkfont
import fleetcarriercargo
from _logger import logger
from cargo_names import MarketCatalogue, MarketName
from vertical_resize_handler import VerticalResizeHandler
from vertical_wheel_scroll import CanvasVerticalMouseWheelScroller


class CanvasTableView:
    _PAD_Y_PER_ROW = 3
    _PAD_X_FOR_SCROLL_BAR = 30

    # New column should be added in 4 places: _COLUMNS, _ATTRIBUTES_PER_COL, _HEADER_ATTRIBUTES, _COLUMN_WIDTH
    # last column is autoresized to fix
    _COLUMNS = [
        "category",
        "amount",
        "name",
    ]  # Can be used instead indexes.
    _ATTRIBUTES_PER_COL = [
        {"justify": tk.LEFT, "anchor": tk.NW},
        {"justify": tk.LEFT, "anchor": tk.NW},
        {"justify": tk.RIGHT, "anchor": tk.NW},
    ]
    _HEADER_ATTRIBUTES_PER_COLUMN = [
        {"justify": tk.LEFT, "anchor": tk.NW},
        {"justify": tk.LEFT, "anchor": tk.NW},
        {"justify": tk.RIGHT, "anchor": tk.NW},
    ]

    def __init__(self, parent: tk.Widget) -> None:
        self._COLUMN_WIDTH: list[int] = [140, 80, 100]

        self.parent_frame = parent
        self._font = tkfont.Font()
        self._frame = tk.Frame(parent, pady=3, padx=3)
        self._frame.grid(sticky=tk.NSEW)
        self._canvas: Optional[tk.Canvas] = None

        theme.update(self._frame)
        self._last_width = -1
        self._total_rows: int = 0

        self._frame.bind("<Configure>", self._on_frame_configure)
        self._resize_pending = False

        self._COLUMN_OFFSET = list(accumulate([0] + self._COLUMN_WIDTH[:-1]))
        self._frame.after(0, self._delayed_update_column_widths)

        self._last_drawn_items_in_rows_order: list[CarrierCargoPosition] | None = None
        self.probably_color_market_on_station: FilterSellOnStationProtocol | None = None

    def _on_frame_configure(self, event: Any):
        if not self._resize_pending:
            self._resize_pending = True
            self._frame.after_idle(self._on_resize_done)

    def _on_resize_done(self):
        self._resize_pending = False
        new_width = self._frame.winfo_width()
        if new_width != self._last_width:
            self._last_width = new_width
            self._update_column_widths()

    def _delayed_update_column_widths(self):
        if self._frame.winfo_width() <= 1:
            self._frame.after(50, self._delayed_update_column_widths)
        else:
            self._update_column_widths()

    def _update_column_widths(self):
        total_width = self._frame.winfo_width() - self._PAD_X_FOR_SCROLL_BAR
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

        self._total_rows = 0

        if not self._canvas:
            minimal_height_to_set = 20
            self._canvas = tk.Canvas(
                self._frame,
                width=self._TABLE_WIDTH,
                height=minimal_height_to_set,
                highlightthickness=0,
                scrollregion=(0, 0, self._TABLE_WIDTH, minimal_height_to_set),
            )
            self._canvas.pack()
            frame = tk.Frame(self._frame)
            frame.pack(side=tk.RIGHT, fill=tk.Y)
            vbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self._canvas.yview)  # type: ignore
            vbar.pack(expand=True, fill=tk.BOTH)
            sizegrip = tk.Label(
                frame, image=IconsCache.icons["resize"], cursor="sizing"
            )
            sizegrip.pack(side=tk.BOTTOM, anchor=tk.SE)
            # Vertical resize handling.
            self._resize_handler = VerticalResizeHandler(
                target=self._canvas,
                min_height=minimal_height_to_set,
                max_height=400,
            )
            self._resize_handler.set_source_of_events(sizegrip)
            self._canvas.config(yscrollcommand=vbar.set)
            self._canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
            # Scrolling by mouse wheel handling.
            self._vertical_wheel_scroller = CanvasVerticalMouseWheelScroller(
                self._canvas, attach=True
            )
            # Reaction L/R mouse buttons.
            self._canvas.bind("<Button-1>", self._on_left_mouse_click)
            self._canvas.bind("<Button-3>", self._on_right_mouse_click)

            theme.update(frame)
            theme.update(self._canvas)
        else:
            assert self._resize_handler
            minimal_height_to_set, _ = self._resize_handler.get_min_max_height()
            self._canvas.delete("all")
            self._canvas.config(
                width=self._TABLE_WIDTH,
                height=minimal_height_to_set,
                scrollregion=(0, 0, self._TABLE_WIDTH, minimal_height_to_set),
            )

    def update_from_carrier(self):
        """
        Main method to display data. It pulls carrier's cargo library, reads current state and displays it.
        """

        def updater(call_sign: str | None, cargo: fleetcarriercargo.CargoTally) -> bool:
            if self._canvas:
                # +1 for "header" and +1 for "totals"
                self._total_rows = 1 + len(cargo) + 1
                self._canvas.delete("all")
                self._draw_cell(0, "name", ptl("Commodity"))
                self._draw_cell(0, "amount", ptl("Amount"))
                self._draw_cell(0, "category", ptl("Category"))

                self._canvas.configure(
                    scrollregion=(
                        0,
                        0,
                        self._TABLE_WIDTH,
                        self._total_rows * self._get_row_visible_height(),
                    )
                )
                logger.debug(
                    f"We have total rows to draw in table/carrier: {self._total_rows}."
                )

                # This object must strictly correspond visible rows, so when user clicks something,
                # we know what it was
                self._last_drawn_items_in_rows_order = []
                for cargo_key, amount in cargo.items():
                    market = MarketCatalogue.explain_commodity(cargo_key.commodity)
                    if market:
                        self._last_drawn_items_in_rows_order.append(
                            CarrierCargoPosition((market, amount, cargo_key.commodity))
                        )
                    else:
                        market_name = MarketName(
                            category="", trade_name=cargo_key.commodity, id=0
                        )
                        pos = CarrierCargoPosition(
                            (market_name, amount, cargo_key.commodity)
                        )
                        self._last_drawn_items_in_rows_order.append(pos)
                self._last_drawn_items_in_rows_order.sort(key=lambda x: x.category)

                row_index = 1  # Because header was 0th row.
                total_cargo = 0
                crop = True  # TODO: make it depend on width
                for cargo_item in self._last_drawn_items_in_rows_order:
                    total_cargo += cargo_item.quantity
                    self._draw_cell(
                        row_index,
                        "name",
                        cargo_item.trade_name,
                        crop=crop,
                        mark_for_sell=bool(
                            self.probably_color_market_on_station
                            and self.probably_color_market_on_station.is_not(
                                call_sign or ""
                            )
                            and self.probably_color_market_on_station.is_buying(
                                cargo_item
                            )
                        ),
                    )
                    self._draw_cell(row_index, "amount", cargo_item.quantity, crop=crop)
                    self._draw_cell(
                        row_index, "category", cargo_item.category, crop=crop
                    )
                    row_index += 1

                # Total field
                self._draw_cell(row_index, "category", "Total Used:", crop=crop)
                self._draw_cell(row_index, "amount", total_cargo, crop=crop)

                logger.debug(f"Update finished of {self._total_rows} rows.")
            return False

        fleetcarriercargo.FleetCarrierCargo.inventory(updater)

    def _get_row_visible_height(self) -> int:
        """
        Returns visible height per row based on current self.font and padding per row.
        """
        return self._font.metrics("linespace") + self._PAD_Y_PER_ROW

    def _draw_cell(
        self,
        row: int,
        col: int | str,
        text: str | int | None = None,
        *,
        crop: bool = False,
        mark_for_sell: bool = False,
    ):
        """
        Draws single cell, 0-row is assumed as header.
        """

        assert len(self._HEADER_ATTRIBUTES_PER_COLUMN) == len(self._ATTRIBUTES_PER_COL)
        assert len(self._HEADER_ATTRIBUTES_PER_COLUMN) == len(self._COLUMN_WIDTH)
        assert len(self._HEADER_ATTRIBUTES_PER_COLUMN) == len(self._COLUMNS)
        assert len(self._HEADER_ATTRIBUTES_PER_COLUMN) == len(self._COLUMN_OFFSET)

        if not self._canvas:
            return self

        if isinstance(text, int):
            text = "{:8,d}".format(text)
        if not text or len(text) == 0:
            return self

        if isinstance(col, str):
            col = self._COLUMNS.index(col)

        ellipses = "…"
        measured_width = self._font.measure(text)
        measured_width_ellipses = self._font.measure(ellipses)
        if crop:
            limit_w = self._COLUMN_WIDTH[col] - measured_width_ellipses
            cropped = measured_width > limit_w
            while measured_width > limit_w and text:
                text = text[:-1]
                measured_width = self._font.measure(text)
            if not text:
                return
            if cropped:
                text += ellipses

        if row == 0:
            fg = theme.current["highlight"] if theme.current else "blue"  # type: ignore
            attr: dict[str, str] = self._HEADER_ATTRIBUTES_PER_COLUMN[col]
        else:
            if mark_for_sell:
                fg = theme.current["highlight"] if theme.current else "blue"  # type: ignore
            else:
                fg = theme.current["foreground"] if theme.current else "black"  # type: ignore
            attr: dict[str, str] = self._ATTRIBUTES_PER_COL[col]

        x = self._get_text_x(col, attr)
        y = row * self._get_row_visible_height()
        self._canvas.create_text(x, y, text=text, fill=fg, **attr)  # type: ignore

    def _get_text_x(self, col: int, attr: dict[str, str]) -> int:
        x = self._COLUMN_OFFSET[col]
        anchor = attr.get("anchor", tk.NW)
        if anchor == tk.NE:
            x += self._COLUMN_WIDTH[col]
        elif anchor == tk.N:
            x += self._COLUMN_WIDTH[col] // 2
        return x

    def _on_left_mouse_click(self, event: tk.Event):
        row, col = self._get_clicked_data_cell(event)
        logger.debug(f"Left mouse click at adjusted row={row}, col={col}")

    def _on_right_mouse_click(self, event: tk.Event):
        row, col = self._get_clicked_data_cell(event)

        logger.debug(f"Right mouse click at adjusted row={row}, col={col}")

        if row is None or col is None:
            logger.debug("Clicked outside valid data area")
            return

        if self._canvas and self._last_drawn_items_in_rows_order:
            item = self._last_drawn_items_in_rows_order[row]
            logger.debug(f"Right-clicked on {item}")
            menu = RightClickContextMenuForTable(self._canvas, item)
            menu.popup(event)
        else:
            logger.error("Canvas or data cell is/are not available during click event!")

    def _get_clicked_data_cell(self, event: tk.Event) -> tuple[int | None, int | None]:
        """
        Translate a mouse click event's canvas coordinates into the corresponding data cell indices,
        adjusting for and excluding header and footer rows.

        Returns:
            Tuple of (row_index, col_index) relative to data rows (header and footer excluded),
            or (None, None) if the click is outside the valid data area.
        """
        if not self._canvas:
            logger.error("Canvas is not available during click event!")
            return None, None

        if event.x < 0 or event.y < 0:
            logger.warning("Click event coordinates are negative!")
            return None, None

        try:
            x = int(self._canvas.canvasx(event.x))  # type: ignore
            y = int(self._canvas.canvasy(event.y))  # type: ignore
        except Exception as e:
            logger.exception("Failed to convert canvas coordinates", exc_info=e)
            return None, None

        row, col = self._coords_to_cell_including_header_footer(x, y)

        if row is None or col is None:
            return None, None

        # Subtract header (row 0) and check for footer
        exclude_header = 1
        if row < exclude_header:
            return None, None

        adjusted_row = row - exclude_header
        if self._last_drawn_items_in_rows_order is None or adjusted_row >= len(
            self._last_drawn_items_in_rows_order
        ):
            return None, None

        return adjusted_row, col

    def _coords_to_cell_including_header_footer(
        self, x: int, y: int
    ) -> tuple[int | None, int | None]:
        """
        Convert canvas pixel coordinates into table cell indices, including headers and footers.

        Returns:
            Tuple of (row_index, col_index) where indices correspond to the full table including
            header and footer rows, or (None, None) if coordinates fall outside the table.
        """
        for col, (offset, width) in enumerate(
            zip(self._COLUMN_OFFSET, self._COLUMN_WIDTH)
        ):
            if offset <= x < offset + width:
                break
        else:
            return None, None

        row = y // self._get_row_visible_height()
        if row >= self._total_rows:
            return None, None

        return row, col
