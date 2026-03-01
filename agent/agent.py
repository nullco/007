from pydantic import BaseModel
from pydantic_ai.agent import Agent


class AgentInput(BaseModel):
    user_input: str


class AgentOutput(BaseModel):
    response: str


class CodingAgent(Agent):
    Input = AgentInput
    Output = AgentOutput

    def __init__(self, **kwargs):
        super().__init__(model="github:gpt-4.1", **kwargs)
        self._message_history = None

    async def stream(self, user_input: AgentInput, stream_handler):
        """Return a run_stream context manager for the client to use for streaming."""
        async with self.run_stream(user_input.user_input, message_history=self._message_history) as result:
            async for update in result.stream_output():
                stream_handler(update)
            self._message_history = result.all_messages()
