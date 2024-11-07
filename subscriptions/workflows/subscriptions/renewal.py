from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity
from temporalio import workflow


@dataclass(frozen=True)
class HelloWorld:
    greeting: str
    name: str


@activity.defn
async def hello_world(input: HelloWorld) -> str:
    activity.logger.info("Running activity with parameter %s" % input)
    return f"{input.greeting}, {input.name}!"


@workflow.defn
class RenewSubscriptionWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        workflow.logger.info("Running workflow with parameter %s" % name)
        result = await workflow.execute_activity(
            hello_world,
            HelloWorld("Hello", name),
            start_to_close_timeout=timedelta(seconds=10),
        )
        return result
