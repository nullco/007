"""Command palette providers for login and model selection."""

import logging
from functools import partial
from textual.command import DiscoveryHit, Hit, Hits, Provider
from app.tui.app import AgentApp


logger = logging.getLogger(__name__)

class LoginProvider(Provider):
    """Command provider for selecting a login provider."""

    def get_providers(self):
        return ['copilot']

    def login(self, provider_name: str):
        # Placeholder for actual login logic
        logger.info(f"Logging in with {provider_name}")
        return f"Logged in with {provider_name}"

    async def discover(self) -> Hits:

        for provider_name in self.get_providers():
            display = f"{provider_name}"
            yield DiscoveryHit(
                display,
                partial(self.login, provider_name),
                help=f"Authenticate with {provider_name}",
            )

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        for provider_name in self.get_providers():
            score = matcher.match(provider_name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(provider_name),
                    partial(self.login, provider_name),
                    help=f"Authenticate with {provider_name}",
                )


class ModelProvider(Provider):

    def _get_models(self):
        return [{'id': 'gpt-4', 'provider': 'copilot'}]

    async def startup(self) -> None:
        worker = self.app.run_worker(
            partial(self._get_models), thread=True
        )
        self._models = await worker.wait()

    async def discover(self) -> Hits:
        assert isinstance(self.app, AgentApp)
        for model in self._models:
            model_id = model['id']
            provider = model['provider']
            display = f"{model_id} ({provider})"
            yield DiscoveryHit(
                display,
                partial(self.app.select_model, model_id, provider)
            )

    async def search(self, query: str) -> Hits:
        assert isinstance(self.app, AgentApp)
        matcher = self.matcher(query)

        for model in self._models:
            model_id = model['id']
            provider = model['provider']
            display = f"{model_id} ({provider})"
            score = matcher.match(display)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(display),
                    partial(self.app.select_model, model_id, provider)
                )
