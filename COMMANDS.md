# Command Reference

Your TUI supports the following slash commands:

## Authentication Commands

### `/login`
Start GitHub Copilot authentication (device flow).
- Displays a user code and verification URL
- Opens a device flow for you to authorize
- Automatically polls for completion

### `/logout`
Clear all authentication tokens.
- Removes stored GitHub and Copilot tokens
- Updates environment variables

### `/status`
Show current login status.
- Displays username if logged in
- Shows "Not logged in" otherwise

## Chat & History

### `/clear`
Clear chat history.
- Removes all previous messages in the current session
- Agent state is reset

## Model Selection

### `/model`
List or select a model. Selecting a model automatically switches to its provider.

**Usage:**
- `/model` - Show all available models from all providers with their provider names
- `/model <id>` - Select a model (automatically switches to its provider)

**Example:**
```
/model

Current: gpt-4 (copilot)

Available:
  → gpt-4                  GPT-4                     [copilot] (enabled)
    gpt-4-turbo            GPT-4 Turbo               [copilot] (enabled)
    claude-opus            Claude 3 Opus             [copilot] (requires acceptance)
    gpt-4o                 GPT-4o                    [openai]

/model gpt-4o
# Automatically switches to OpenAI provider and selects gpt-4o
```

**Features:**
- Shows all models from all configured providers
- Displays current model and provider
- Shows model status (enabled, requires acceptance, etc.)
- Automatically handles provider switching when you select a model
- Models are inherently tied to their providers

## Interactive Usage

All commands can be:
1. **Typed** in the chat input with `/` prefix
2. **Selected** from the system command palette (usually Ctrl+\)

## Key Bindings

- `Ctrl+C` - Single press clears session, double press within 1 second quits
- `c` - Copy focused message to clipboard
