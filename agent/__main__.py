import asyncio
import logging
import os
import traceback

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical
from textual.message import Message
from textual.widgets import Footer, Header, Markdown, OptionList, TextArea
from textual.widgets.option_list import Option

from agent.agent import AgentInput, CodingAgent

logging.basicConfig(
    level=os.getenv("AGENT_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

COMMANDS = [
    ("/help", "❓ Show help"),
    ("/login", "🔑 GitHub Copilot login"),
    ("/logout", "🚪 Clear tokens"),
    ("/status", "📊 Show login status"),
    ("/clear", "🧹 Clear chat"),
    ("/quit", "👋 Quit"),
]

COMMANDS_HELP = """Available commands:
  /help   - Show this help message
  /login  - Start GitHub Copilot OAuth device flow
  /logout - Clear authentication tokens
  /status - Show login status
  /clear  - Clear chat history
  /quit   - Quit the application"""


class MessageOutput(Markdown):
    """A Markdown widget for displaying rendered messages."""

    can_focus = True

    DEFAULT_CSS = """
    MessageOutput {
        height: auto;
        margin: 0 0 1 0;
        padding: 0 1;
        border-left: blank;
    }

    MessageOutput:focus {
        border-left: solid $accent;
    }
    """

    BINDINGS = [
        Binding("y,c", "copy_to_clipboard", "Copy", show=False),
    ]

    def __init__(self, text: str = "", **kwargs):
        super().__init__(text, **kwargs)
        self._raw_text = text

    @property
    def text(self) -> str:
        """Get the raw markdown text."""
        return self._raw_text

    @text.setter
    def text(self, value: str) -> None:
        """Set the markdown text and update the rendered output."""
        self._raw_text = value
        self.update(value)

    def action_copy_to_clipboard(self) -> None:
        """Copy raw markdown text to clipboard."""
        if not self._raw_text:
            return
        try:
            import pyperclip

            pyperclip.copy(self._raw_text)
        except Exception as e:
            logger.debug("pyperclip failed, falling back to app clipboard: %s", e)
            self.app.copy_to_clipboard(self._raw_text)
        self.app.notify(f"Copied {len(self._raw_text)} characters")

    def on_click(self) -> None:
        """Focus the message when clicked."""
        self.focus()


class CommandSuggestions(OptionList):
    """Dropdown for command suggestions."""

    DEFAULT_CSS = """
    CommandSuggestions {
        height: auto;
        max-height: 8;
        display: none;
        layer: overlay;
        dock: bottom;
        margin-bottom: 3;
        margin-left: 1;
        margin-right: 1;
        background: $surface;
        border: solid $primary;
    }

    CommandSuggestions.visible {
        display: block;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._refresh_options("")

    def _refresh_options(self, filter_text: str) -> None:
        """Update options based on filter text."""
        self.clear_options()
        filter_lower = filter_text.lower()
        for cmd, desc in COMMANDS:
            if cmd.startswith(filter_lower):
                self.add_option(Option(f"{desc}  {cmd}", id=cmd))

    def filter(self, text: str) -> None:
        """Filter commands and show/hide dropdown."""
        if text.startswith("/"):
            self._refresh_options(text)
            if self.option_count > 0:
                self.add_class("visible")
                self.highlighted = 0
            else:
                self.remove_class("visible")
        else:
            self.remove_class("visible")

    def hide(self) -> None:
        """Hide the dropdown."""
        self.remove_class("visible")


class UserInput(TextArea):
    """A TextArea for user input with command suggestions."""

    DEFAULT_CSS = """
    UserInput {
        height: auto;
        max-height: 10;
        margin: 0 1;
    }
    """

    class Submit(Message):
        def __init__(self, text: str):
            self.text = text
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.language = None
        self._suggestions: CommandSuggestions | None = None

    def on_mount(self) -> None:
        """Get reference to suggestions widget."""
        try:
            self._suggestions = self.app.query_one(CommandSuggestions)
        except Exception:
            pass

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Update suggestions when text changes."""
        if self._suggestions:
            self._suggestions.filter(self.text)

    async def on_key(self, event) -> None:
        """Handle key events."""
        if self._suggestions and self._suggestions.has_class("visible"):
            if event.key == "down":
                event.prevent_default()
                self._suggestions.action_cursor_down()
                return
            elif event.key == "up":
                event.prevent_default()
                self._suggestions.action_cursor_up()
                return
            elif event.key == "tab":
                event.prevent_default()
                self._accept_suggestion()
                return
            elif event.key == "escape":
                event.prevent_default()
                self._suggestions.hide()
                return

        if event.key == "shift+enter":
            event.prevent_default()
            self.insert("\n")
        elif event.key == "enter":
            event.prevent_default()
            if self._suggestions:
                self._suggestions.hide()
            self.post_message(self.Submit(self.text))

    def _accept_suggestion(self) -> None:
        """Accept the currently highlighted suggestion."""
        if not self._suggestions or self._suggestions.option_count == 0:
            return
        highlighted = self._suggestions.highlighted
        if highlighted is not None:
            option = self._suggestions.get_option_at_index(highlighted)
            if option and option.id:
                self.text = str(option.id)
                self.move_cursor(self.document.end)
                self._suggestions.hide()


class CodingAgentApp(App):
    """A minimalist TUI for the Coding Agent."""

    TITLE = "Agent 007"
    CSS = """
    #main {
        layers: base overlay;
    }
    """
    BINDINGS = [
        Binding("ctrl+c", "handle_sigint", "Quit", show=False),
        Binding("c", "copy_focused", "Copy", show=True),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_sigint_time = 0.0
        self._background_tasks: set[asyncio.Task] = set()

    def action_handle_sigint(self) -> None:
        """Handle Ctrl+C: double-tap within 1s to quit, single clears session."""
        import time

        now = time.time()
        if now - self._last_sigint_time < 1.0:
            self._cancel_background_tasks()
            self.exit()
        else:
            self._last_sigint_time = now
            self.notify("Press Ctrl+C again to quit", severity="warning")

    def action_copy_focused(self) -> None:
        """Copy the focused message to clipboard."""
        focused = self.focused
        if isinstance(focused, MessageOutput):
            focused.action_copy_to_clipboard()

    def _cancel_background_tasks(self) -> None:
        """Cancel all background tasks."""
        self.agent.copilot_auth.cancel()
        for task in self._background_tasks:
            task.cancel()
        self._background_tasks.clear()

    def compose(self) -> ComposeResult:
        yield Header(id="header")
        with Vertical(id="main"):
            yield ScrollableContainer(id="chat-container")
            yield CommandSuggestions(id="suggestions")
            yield UserInput(id="user_input")
        yield Footer(id="footer")

    def on_mount(self) -> None:
        self.input_widget = self.query_one("#user_input", UserInput)
        self.chat_container = self.query_one("#chat-container", ScrollableContainer)
        self.input_widget.focus()
        self.agent = CodingAgent()

    async def _add_message(self, text: str) -> MessageOutput:
        """Add a message bubble to chat."""
        bubble = MessageOutput(text=text)
        await self.chat_container.mount(bubble)
        self.chat_container.scroll_end(animate=False)
        return bubble

    async def on_user_input_submit(self, message: UserInput.Submit) -> None:
        """Handle input submission."""
        user_text = message.text.strip()
        if not user_text:
            return

        self.input_widget.text = ""

        if user_text.startswith("/"):
            await self._handle_command(user_text)
            return

        await self._handle_chat(user_text)

    async def _handle_command(self, cmd: str) -> None:
        """Handle slash commands."""
        cmd_name = cmd.split()[0]

        if cmd_name == "/quit":
            self._cancel_background_tasks()
            self.exit()
            return

        if cmd_name == "/help":
            await self._add_message(COMMANDS_HELP)
            return

        if cmd_name == "/clear":
            self.agent.clear_history()
            await self.chat_container.remove_children()
            await self._add_message("[Agent] Chat history cleared.")
            return

        if cmd_name == "/login":
            result = self.agent.handle_command(cmd_name)
            if result:
                await self._add_message(result)
            task = asyncio.create_task(self._poll_oauth())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            return

        if cmd_name in ("/logout", "/status"):
            result = self.agent.handle_command(cmd_name)
            if result:
                await self._add_message(result)
            return

        await self._add_message(f"[Agent] Unknown command: {cmd_name}\n\n{COMMANDS_HELP}")

    async def _poll_oauth(self) -> None:
        """Poll for OAuth completion in background."""
        loop = asyncio.get_running_loop()
        _, msg = await loop.run_in_executor(
            None, self.agent.copilot_auth.poll_for_token
        )
        await self._add_message(msg)

    async def _handle_chat(self, user_text: str) -> None:
        """Handle a regular chat message."""
        await self._add_message(user_text)
        bubble = await self._add_message("")

        try:

            def stream_handler(update):
                bubble.text = update
                self.chat_container.scroll_end(animate=False)

            await self.agent.stream(AgentInput(user_input=user_text), stream_handler)
        except Exception as e:
            logger.error("Error during agent stream: %s", e)
            logger.debug(traceback.format_exc())
            bubble.text = f"Error: {e}"
            self.chat_container.scroll_end(animate=False)


if __name__ == "__main__":
    CodingAgentApp().run()
