"""Smoke tests for the TUI application."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.__main__ import (
    CodingAgentApp,
    CommandSuggestions,
    MessageOutput,
    UserInput,
)


@pytest.fixture
def mock_agent():
    """Create a mock CodingAgent."""
    with patch("agent.__main__.CodingAgent") as mock_class:
        mock_instance = MagicMock()
        mock_instance.copilot_auth = MagicMock()
        mock_instance.copilot_auth.cancel = MagicMock()
        mock_instance.clear_history = MagicMock()
        mock_instance.handle_command = MagicMock(return_value="[Agent] Command result")

        async def mock_stream(input_data, handler):
            handler("Test response from agent")

        mock_instance.stream = AsyncMock(side_effect=mock_stream)
        mock_class.return_value = mock_instance
        yield mock_instance


class TestCodingAgentApp:
    @pytest.mark.asyncio
    async def test_app_starts(self, mock_agent):
        """Test that the app starts and has expected widgets."""
        app = CodingAgentApp()
        async with app.run_test() as _pilot:  # noqa: F841
            assert app.query_one("#user_input", UserInput) is not None
            assert app.query_one("#chat-container") is not None
            assert app.query_one("#header") is not None
            assert app.query_one("#footer") is not None

    @pytest.mark.asyncio
    async def test_help_command(self, mock_agent):
        """Test /help command shows help text."""
        app = CodingAgentApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#user_input", UserInput)
            input_widget.text = "/help"
            input_widget.post_message(UserInput.Submit("/help"))
            await pilot.pause()

            messages = app.query(MessageOutput)
            assert len(messages) > 0

            help_shown = any(
                "/login" in msg.text and "/logout" in msg.text for msg in messages
            )
            assert help_shown

    @pytest.mark.asyncio
    async def test_clear_command(self, mock_agent):
        """Test /clear command clears history."""
        app = CodingAgentApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#user_input", UserInput)
            input_widget.text = "/clear"
            input_widget.post_message(UserInput.Submit("/clear"))
            await pilot.pause()

            mock_agent.clear_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_command_shows_help(self, mock_agent):
        """Test unknown command shows help."""
        app = CodingAgentApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#user_input", UserInput)
            input_widget.text = "/unknowncommand"
            input_widget.post_message(UserInput.Submit("/unknowncommand"))
            await pilot.pause()

            messages = app.query(MessageOutput)
            unknown_msg = [m for m in messages if "Unknown command" in m.text]
            assert len(unknown_msg) > 0

    @pytest.mark.asyncio
    async def test_chat_message(self, mock_agent):
        """Test sending a chat message."""
        app = CodingAgentApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#user_input", UserInput)
            input_widget.text = "Hello agent"
            input_widget.post_message(UserInput.Submit("Hello agent"))
            await pilot.pause()

            mock_agent.stream.assert_called_once()

            messages = app.query(MessageOutput)
            assert len(messages) >= 2

    @pytest.mark.asyncio
    async def test_empty_input_ignored(self, mock_agent):
        """Test that empty input is ignored."""
        app = CodingAgentApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#user_input", UserInput)
            input_widget.text = "   "
            input_widget.post_message(UserInput.Submit("   "))
            await pilot.pause()

            mock_agent.stream.assert_not_called()

    @pytest.mark.asyncio
    async def test_status_command(self, mock_agent):
        """Test /status command."""
        mock_agent.handle_command.return_value = "[Agent] Not logged in"

        app = CodingAgentApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#user_input", UserInput)
            input_widget.text = "/status"
            input_widget.post_message(UserInput.Submit("/status"))
            await pilot.pause()

            mock_agent.handle_command.assert_called_with("/status")


class TestMessageOutput:
    @pytest.mark.asyncio
    async def test_message_output_renders_markdown(self, mock_agent):
        """Test MessageOutput stores and can update text."""
        app = CodingAgentApp()
        async with app.run_test():
            msg = MessageOutput(text="**bold** text")
            assert msg.text == "**bold** text"

            msg.text = "# Header"
            assert msg.text == "# Header"


class TestUserInput:
    @pytest.mark.asyncio
    async def test_user_input_is_textarea(self, mock_agent):
        """Test UserInput is a TextArea."""
        app = CodingAgentApp()
        async with app.run_test():
            from textual.widgets import TextArea

            input_widget = app.query_one("#user_input", UserInput)
            assert isinstance(input_widget, TextArea)


class TestCommandSuggestions:
    @pytest.mark.asyncio
    async def test_suggestions_exist(self, mock_agent):
        """Test that suggestions widget is present."""
        app = CodingAgentApp()
        async with app.run_test() as _pilot:  # noqa: F841
            suggestions = app.query_one(CommandSuggestions)
            assert suggestions is not None

    @pytest.mark.asyncio
    async def test_suggestions_hidden_by_default(self, mock_agent):
        """Test suggestions are hidden by default."""
        app = CodingAgentApp()
        async with app.run_test() as _pilot:  # noqa: F841
            suggestions = app.query_one(CommandSuggestions)
            assert not suggestions.has_class("visible")

    @pytest.mark.asyncio
    async def test_suggestions_filter_shows_on_slash(self, mock_agent):
        """Test suggestions appear when filtering with /."""
        app = CodingAgentApp()
        async with app.run_test() as _pilot:  # noqa: F841
            suggestions = app.query_one(CommandSuggestions)
            suggestions.filter("/he")
            assert suggestions.has_class("visible")
            assert suggestions.option_count > 0

    @pytest.mark.asyncio
    async def test_suggestions_hidden_without_slash(self, mock_agent):
        """Test suggestions stay hidden for regular text."""
        app = CodingAgentApp()
        async with app.run_test() as _pilot:  # noqa: F841
            suggestions = app.query_one(CommandSuggestions)
            suggestions.filter("hello")
            assert not suggestions.has_class("visible")
