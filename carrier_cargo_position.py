from typing import Any
from cargo_names import MarketName


class CarrierCargoPosition:
    """
    Represents a single cargo item in the carrier inventory,
    containing all relevant information as shown in the in-game interface.
    """

    def __init__(self, data: tuple[MarketName, int, str]):
        self._market_data = data[0]
        self.quantity: int = data[1]
        self.commodity: str = data[2]  # This is what API uses

    @property
    def category(self) -> str:
        return self._market_data.category

    @property
    def trade_name(self) -> str:
        """
        This is what user / Inara sees.
        """
        return self._market_data.trade_name

    @property
    def id(self) -> int:
        return self._market_data.id

    def __repr__(self):
        return (
            f"CarrierPosition(trade_name={self.trade_name!r}, "
            f"quantity={self.quantity}, category={self.category!r}, "
            f"commodity={self.commodity!r})"
        )

    def __eq__(self, other: Any):
        if not isinstance(other, CarrierCargoPosition):
            return NotImplemented
        return (
            self._market_data == other._market_data
            and self.quantity == other.quantity
            and self.commodity == other.commodity
        )

    def __hash__(self):
        return hash((self._market_data, self.quantity, self.commodity))
