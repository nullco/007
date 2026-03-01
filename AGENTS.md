# Usage Notes for Minimalist TUI

## Starting the agent
uv run python -m agent

## Quitting/Clearing the TUI
- **Single Ctrl+C**: Clear session and start over.
- **Double Ctrl+C** (within 1 second): Quit the app.
- **/quit**: Type `/quit` and press Enter to quit (command mode).

## Command Mode
- Begin input with `/` to enter command mode.
- `/quit`: Quit the app.
- `/` alone: List available commands.

## Appearance
- Minimalist: Only a conversation log and input box, no extra panels.
- Terminal colors are used:
  - User, agent, system, error, and command outputs are color-coded.

### Example Interaction
- User: Hello
- Agent: responds
- Type `/` for command list

---

For development shortcuts & agent extension: see README.md and agent/agent.py.
