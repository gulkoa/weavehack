from a2a.server.task_manager import (
    AgentExecutor,
    EventQueue,
    RequestContext,
    TaskUpdater,
)
from a2a.server.task_protocols import TaskState, new_agent_text_message, new_task

from .agent import MCPGenerator


class AgentTaskManager(AgentExecutor):
    def __init__(self):
        self.agent = MCPGenerator()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        try:
            async for item in self.agent.invoke(query, task.contextId):
                if not item.get("is_task_complete", False):
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            item.get("updates"), task.contextId, task.id
                        ),
                    )
                else:
                    message = new_agent_text_message(
                        item.get("content"), task.contextId, task.id
                    )
                    await updater.update_status(TaskState.completed, message)
                    break
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(error_message, task.contextId, task.id),
            )
            raise

    async def cancel(self, task_id: str) -> None:
        # Implementation for canceling tasks if needed
        pass
