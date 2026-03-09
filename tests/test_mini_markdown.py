import asyncio
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest
from prompt_toolkit.input.posix_pipe import PosixPipeInput
from prompt_toolkit.output import DummyOutput

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.tui import mini


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


class FakeAgent:
    model_name = "demo-model"
    provider_name = "demo-provider"

    async def stream(self, user_text: str, handler) -> None:
        handler("Here is some code:\n```python\nprint('ok')\n```\n")

    def clear_history(self) -> None:
        return None


@pytest.mark.asyncio
async def test_render_markdown_highlights_code_block() -> None:
    rendered = mini._render_markdown("```python\nprint('ok')\n```")

    assert "```" not in rendered
    assert "print('ok')" in strip_ansi(rendered)
    assert ANSI_RE.search(rendered)


@pytest.mark.asyncio
async def test_mini_app_renders_markdown_with_pipe_input() -> None:
    agent = FakeAgent()
    buffer = io.StringIO()
    with PosixPipeInput.create() as pipe, redirect_stdout(buffer):
        output = DummyOutput()
        task = asyncio.create_task(
            mini.main(agent=agent, session_input=pipe, session_output=output)
        )
        await asyncio.sleep(0)
        pipe.send_text("hello\n/quit\n")
        await task

    captured = buffer.getvalue()

    assert "```" not in captured
    assert "print('ok')" in strip_ansi(captured)
    assert ANSI_RE.search(captured)
