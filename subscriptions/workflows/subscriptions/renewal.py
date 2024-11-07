from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from subscriptions.subscriptions import activities


@workflow.defn
class RenewSubscriptionWorkflow:
    @workflow.run
    async def run(self, subscription_id: int) -> str:
        workflow.logger.info("Running workflow with parameter %s" % subscription_id)
        result = await workflow.execute_activity(
            activities.hello_world,
            activities.Input(subscription_id=subscription_id),
            start_to_close_timeout=timedelta(seconds=10),
        )
        return result
