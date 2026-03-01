# agent

A coding agent with a minimalist, colored TUI using Textual and pydantic-ai.

## Project Setup & Installation
- Python 3.13 required (`uv` recommended)
- All dependencies in `pyproject.toml`

```sh
uv pip install -r requirements.txt
```

## Usage

```sh
uv run python -m agent
```

### TUI Controls & Features
- **Minimalist appearance**: just a log and input box, with color-coded output
- **Color support**: User input, agent responses, system/info, errors, and commands are visually distinct
- **Single Ctrl+C**: Clears session (log and state)
- **Double Ctrl+C**: Quits the app
- **Command mode**: Type `/quit` (press Enter) to quit, `/` to show available commands

---

## Extending
Edit or subclass `agent/agent.py` for new agent logic or LLM tools.

## Troubleshooting/Dev
- If `uv run` fails, try `uv pip install` again
