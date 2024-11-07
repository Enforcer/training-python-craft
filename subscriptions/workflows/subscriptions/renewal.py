from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from subscriptions.subscriptions import activities


@workflow.defn
class RenewSubscriptionWorkflow:
    @workflow.run
    async def run(self, subscription_id: int) -> None:
        workflow.logger.info("Running workflow with parameter %s" % subscription_id)
        charge_succeeded = await workflow.execute_activity(
            activities.charge_for_renewal,
            activities.Input(subscription_id=subscription_id),
            start_to_close_timeout=timedelta(seconds=10),
        )

        if charge_succeeded:
            await workflow.execute_activity(
                activities.mark_as_success,
                activities.Input(subscription_id=subscription_id),
                start_to_close_timeout=timedelta(seconds=10),
            )
        else:
            await workflow.execute_activity(
                activities.mark_as_failure,
                activities.Input(subscription_id=subscription_id),
                start_to_close_timeout=timedelta(seconds=10),
            )
