from dataclasses import dataclass

from temporalio import activity

from subscriptions.main import container
from subscriptions.subscriptions._app._renewal import RenewalService
from subscriptions.subscriptions._domain._subscription_id import SubscriptionId


@dataclass(frozen=True)
class Input:
    subscription_id: int


@activity.defn
async def charge_for_renewal(input: Input) -> bool:
    # no integration of lagom and temporal exists,
    # so we're getting a bit nasty here and use container directly
    renewal_service = container.resolve(RenewalService)  # noqa: F841

    result = renewal_service.calculate_cost_and_charge(
        SubscriptionId(input.subscription_id),
    )

    return result


@activity.defn
async def mark_as_success(input: Input) -> None:
    renewal_service = container.resolve(RenewalService)
    renewal_service.renew_successful(
        SubscriptionId(input.subscription_id),
    )


@activity.defn
async def mark_as_failure(input: Input) -> None:
    renewal_service = container.resolve(RenewalService)
    renewal_service.renew_failed(
        SubscriptionId(input.subscription_id),
    )
