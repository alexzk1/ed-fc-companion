from fleetcarriercargo import FleetCarrierCargo, CargoTally


def get_carrier_name() -> str:
    """
    Returns carrier's call sign or empty string if it is not known yet.
    """
    carrier_name: str = ""

    def get_name(call_sign: str | None, cargo: CargoTally):
        nonlocal carrier_name
        carrier_name = call_sign or ""
        return False

    FleetCarrierCargo.inventory(get_name)
    return carrier_name
