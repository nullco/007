"""Tests for CodingAgent."""

from unittest.mock import MagicMock, patch


from agent.agent import AgentInput, CodingAgent


class TestCodingAgent:
    @patch("agent.agent.build_copilot_model")
    @patch("agent.agent.Agent.__init__", return_value=None)
    def test_default_model(self, mock_init, mock_build, monkeypatch):
        monkeypatch.delenv("AGENT_MODEL", raising=False)
        mock_build.return_value = MagicMock()
        _agent = CodingAgent()
        mock_build.assert_called_once_with(None)

    @patch("agent.agent.build_copilot_model")
    @patch("agent.agent.Agent.__init__", return_value=None)
    def test_custom_model_from_arg(self, mock_init, mock_build, monkeypatch):
        monkeypatch.delenv("AGENT_MODEL", raising=False)
        mock_build.return_value = MagicMock()
        _agent = CodingAgent(model="anthropic:claude-3")
        mock_build.assert_called_once_with("anthropic:claude-3")

    def test_clear_history(self):
        with patch("agent.agent.build_copilot_model", return_value=MagicMock()):
            with patch("agent.agent.Agent.__init__", return_value=None):
                agent = CodingAgent()
                agent._message_history = [{"role": "user", "content": "test"}]

                agent.clear_history()

                assert agent._message_history is None


class TestHandleCommand:
    @patch("agent.agent.CopilotAuthenticator")
    def test_login_command(self, mock_auth_class):
        mock_auth = MagicMock()
        mock_auth.start_login.return_value = (True, "[OAuth] Test message")
        mock_auth_class.return_value = mock_auth

        with patch("agent.agent.build_copilot_model", return_value=MagicMock()):
            with patch("agent.agent.Agent.__init__", return_value=None):
                agent = CodingAgent()
                agent.copilot_auth = mock_auth

                result = agent.handle_command("/login")

                assert result == "[OAuth] Test message"
                mock_auth.start_login.assert_called_once()

    @patch("agent.agent.CopilotAuthenticator")
    def test_logout_command(self, mock_auth_class):
        mock_auth = MagicMock()
        mock_auth.logout.return_value = "[OAuth] Logged out."
        mock_auth_class.return_value = mock_auth

        with patch("agent.agent.build_copilot_model", return_value=MagicMock()):
            with patch("agent.agent.Agent.__init__", return_value=None):
                agent = CodingAgent()
                agent.copilot_auth = mock_auth

                result = agent.handle_command("/logout")

                assert result == "[OAuth] Logged out."
                mock_auth.logout.assert_called_once()

    @patch("agent.agent.CopilotAuthenticator")
    def test_status_command(self, mock_auth_class):
        mock_auth = MagicMock()
        mock_auth.get_status.return_value = "Logged in as: testuser"
        mock_auth_class.return_value = mock_auth

        with patch("agent.agent.build_copilot_model", return_value=MagicMock()):
            with patch("agent.agent.Agent.__init__", return_value=None):
                agent = CodingAgent()
                agent.copilot_auth = mock_auth

                result = agent.handle_command("/status")

                assert "[Agent] Logged in as: testuser" in result
                mock_auth.get_status.assert_called_once()

    def test_unknown_command(self):
        with patch("agent.agent.build_copilot_model", return_value=MagicMock()):
            with patch("agent.agent.Agent.__init__", return_value=None):
                agent = CodingAgent()
                agent.copilot_auth = MagicMock()

                result = agent.handle_command("/unknown")

                assert "Unknown command" in result


class TestAgentInput:
    def test_agent_input_model(self):
        input_data = AgentInput(user_input="Hello, world!")
        assert input_data.user_input == "Hello, world!"
