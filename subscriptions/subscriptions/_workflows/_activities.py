from dataclasses import dataclass

from temporalio import activity

from subscriptions.main import container
from subscriptions.subscriptions._app._renewal import RenewalService


@dataclass(frozen=True)
class Input:
    subscription_id: int


@activity.defn
async def hello_world(input: Input) -> str:
    # no integration of lagom and temporal exists,
    # so we're getting a bit nasty here and use container directly
    renewal_service = container.resolve(RenewalService)  # noqa: F841

    activity.logger.info("Running activity with parameter %s" % input)

    return f"Hello, {input.subscription_id}!"
