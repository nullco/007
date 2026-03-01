from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import Header, Footer, TextArea
from textual.binding import Binding
from agent.agent import CodingAgent, AgentInput
from textual.message import Message


class MessageOutput(TextArea):
    """A TextArea for displaying messages."""
    DEFAULT_CSS = """
    MessageOutput {
        height: auto;
        overflow: hidden;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read_only = True
        self.language = "markdown"


class UserInput(TextArea):
    """A TextArea for user input with a placeholder."""
    DEFAULT_CSS = """
    UserInput {
        height: auto;
        overflow: hidden;
    }
    """

    class Submit(Message):
        def __init__(self, text: str):
            self.text = text
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.placeholder = "Enter your prompt and press Enter..."
        self.read_only = False
        self.focused = True

    async def on_key(self, event):
        if event.key == "enter":
            event.prevent_default()
            self.post_message(self.Submit(self.text))
        elif event.key == "shift+enter":
            self.text += "\n"
            self.cursor_position = len(self.text)


class CodingAgentApp(App):
    """A minimalist TUI for the Coding Agent."""

    TITLE = "Agent 007"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header(id="header")
        with Vertical(id="main"):
            yield ScrollableContainer(id="chat-container")
            yield UserInput(placeholder="Enter your prompt and press Enter...", id="user_input")
        yield Footer(id="footer")

    def on_mount(self) -> None:
        self.input_widget = self.query_one("#user_input", UserInput)
        self.chat_container = self.query_one("#chat-container", ScrollableContainer)
        self.input_widget.focus()
        self.agent = CodingAgent()
        self._last_sigint_time = 0

    AVAILABLE_COMMANDS = {"/quit": "Quit the app"}

    async def on_user_input_submit(self, message: UserInput.Submit) -> None:
        user_text = self.input_widget.text.strip()
        if not user_text:
            return
        # Command mode
        if user_text.startswith("/"):
            cmd = user_text.split()[0]
            if cmd == "/quit":
                await self.action_quit()
                return
            else:
                self.input_widget.text = ""
                return

        bubble = MessageOutput(text=user_text)
        await self.chat_container.mount(bubble)
        self.chat_container.scroll_end(animate=False)
        self.input_widget.text = ""
        bubble = MessageOutput(text="")
        await self.chat_container.mount(bubble)
        try:
            def stream_handler(update):
                bubble.text = update
                self.chat_container.scroll_end(animate=False)

            await self.agent.stream(AgentInput(user_input=user_text), stream_handler)
        except Exception as e:
            bubble.text=f"Error: {str(e)}"
            self.chat_container.scroll_end(animate=False)


if __name__ == "__main__":
    CodingAgentApp().run()
