from dataclasses import dataclass


@dataclass(frozen=True)
class RequestedAddOn:
    name: str
    quantity: int
