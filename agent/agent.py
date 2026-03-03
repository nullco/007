from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai.agent import Agent

from ai.auth import CopilotAuthenticator
from ai.model import build_copilot_model


class AgentInput(BaseModel):
    user_input: str


class CodingAgent(Agent):
    Input = AgentInput

    def __init__(self, model=None, **kwargs):
        self._model_name = model
        super().__init__(model=build_copilot_model(self._model_name), **kwargs)
        self._message_history = None
        self.copilot_auth = CopilotAuthenticator()

    def refresh_model(self) -> None:
        """Rebuild the model client with current tokens."""
        self.model = build_copilot_model(self._model_name)

    async def stream(self, user_input: AgentInput, stream_handler):
        """Stream responses from the agent."""
        if self.copilot_auth.refresh_token():
            self.refresh_model()
        async with self.run_stream(
            user_input.user_input, message_history=self._message_history
        ) as result:
            async for update in result.stream_output():
                stream_handler(update)
            self._message_history = result.all_messages()

    def clear_history(self) -> None:
        """Clear the message history."""
        self._message_history = None

    def handle_command(self, cmd: str) -> str | None:
        """Handle slash commands. Returns a message or None."""
        cmd = cmd.strip()
        if cmd == "/login":
            ok, msg = self.copilot_auth.start_login()
            return msg
        if cmd == "/logout":
            return self.copilot_auth.logout()
        if cmd == "/status":
            return f"[Agent] {self.copilot_auth.get_status()}"
        return "[Agent] Unknown command."
