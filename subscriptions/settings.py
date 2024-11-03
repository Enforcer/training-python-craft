from pydantic_settings import BaseSettings


class PaymentsSettings(BaseSettings):
    STRIPE_API_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    class Config:
        env_prefix = "PAYMENTS_"
