"""Command handlers for the TUI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import AppConfig

logger = logging.getLogger(__name__)


class CommandHandler:
    """Handles slash commands in the TUI."""

    def __init__(self, app_config: AppConfig):
        """Initialize the command handler.
        
        Args:
            app_config: Application configuration with agent and authenticator.
        """
        self.app_config = app_config
        self.agent = app_config.agent
        self.authenticator = app_config.get_authenticator()

    async def handle_login(self) -> str | None:
        """Handle /login command."""
        if not self.authenticator:
            return "[Commands] No authenticator available for this provider"
        
        try:
            ok, msg = self.authenticator.start_login()
            return msg
        except Exception as e:
            logger.error("Login failed: %s", e)
            return f"[Commands] Login failed: {e}"

    async def handle_logout(self) -> str | None:
        """Handle /logout command."""
        if not self.authenticator:
            return "[Commands] No authenticator available for this provider"
        
        try:
            return self.authenticator.logout()
        except Exception as e:
            logger.error("Logout failed: %s", e)
            return f"[Commands] Logout failed: {e}"

    async def handle_status(self) -> str | None:
        """Handle /status command."""
        if not self.authenticator:
            return "[Commands] No authenticator available for this provider"
        
        try:
            status = self.authenticator.get_status()
            return f"[Agent] {status}"
        except Exception as e:
            logger.error("Status check failed: %s", e)
            return f"[Commands] Status check failed: {e}"

    async def handle_clear(self) -> str | None:
        """Handle /clear command."""
        try:
            self.agent.clear_history()
            return "[Agent] Chat history cleared."
        except Exception as e:
            logger.error("Clear history failed: %s", e)
            return f"[Commands] Clear failed: {e}"

    async def handle_model(self, args: str = "") -> str | None:
        """Handle /model command.
        
        Usage:
            /model              - Show available models from all providers
            /model <id>         - Select a model (switches to its provider)
        """
        args = args.strip().lower()
        
        if not args:
            # List available models from all providers
            try:
                models = self.app_config.ai_manager.get_all_models()
                current = self.app_config.ai_manager.get_current_model()
                current_provider = self.app_config.ai_manager.provider_name()
                
                if not models:
                    return "[Model] No models available. You may need to log in first."
                
                model_lines = []
                for m in models:
                    model_id = m.get("id", "unknown")
                    model_name = m.get("name", model_id)
                    provider = m.get("provider", "unknown")
                    is_current = "→" if (model_id == current and provider == current_provider) else " "
                    enabled = " (enabled)" if m.get("enabled") else ""
                    requires_policy = " (requires acceptance)" if m.get("requires_policy") else ""
                    
                    model_lines.append(
                        f"  {is_current} {model_id:<20} {model_name:<25} [{provider}]{enabled}{requires_policy}"
                    )
                
                model_list = "\n".join(model_lines)
                return f"[Model] Current: {current} ({current_provider})\n\nAvailable:\n{model_list}\n\nUse: /model <id>"
            except Exception as e:
                logger.debug("Failed to list models: %s", e)
                return f"[Model] Failed to list models: {e}"
        
        # Find model by ID and switch to its provider
        try:
            all_models = self.app_config.ai_manager.get_all_models()
            selected_model = None
            
            for m in all_models:
                if m.get("id", "").lower() == args or m.get("name", "").lower() == args:
                    selected_model = m
                    break
            
            if not selected_model:
                return f"[Model] Model not found: {args}\n\nTry /model to see available options."
            
            provider = selected_model.get("provider")
            model_id = selected_model.get("id")
            
            # Switch provider
            if not self.app_config.ai_manager.switch_provider(provider):
                return f"[Model] Failed to switch to provider: {provider}"
            
            # Select model in the new provider
            if not self.app_config.ai_manager.select_model(model_id):
                return f"[Model] Failed to select model: {model_id}"
            
            # Rebuild agent with new provider and model
            self.app_config.rebuild_agent()
            self.authenticator = self.app_config.get_authenticator()
            
            return f"[Model] Switched to: {model_id} (provider: {provider})"
        except Exception as e:
            logger.error("Model selection failed: %s", e)
            return f"[Commands] Model selection failed: {e}"

    async def handle_command(self, cmd: str) -> str | None:
        """Handle a slash command.
        
        Args:
            cmd: Command string (e.g., "/login", "/status").
            
        Returns:
            Message to display, or None.
        """
        cmd = cmd.strip()
        
        # Parse command and arguments
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command == "/login":
            return await self.handle_login()
        elif command == "/logout":
            return await self.handle_logout()
        elif command == "/status":
            return await self.handle_status()
        elif command == "/clear":
            return await self.handle_clear()
        elif command == "/model":
            return await self.handle_model(args)
        else:
            return "[Commands] Unknown command."
