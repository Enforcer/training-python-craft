class InvalidTierRequested(Exception):
    def __init__(
        self, add_on_name: str, quantity: int, available_tiers: list[int]
    ) -> None:
        message = f"Tier {quantity} does not exist for {add_on_name}, available_tiers: {available_tiers}"
        super().__init__(message)
