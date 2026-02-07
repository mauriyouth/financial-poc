# System Prompts

This directory contains system prompts used for AI interactions across the application.

## Available Prompts

### `default.txt`
The default system prompt for general financial analysis conversations.
- Used for: General chat, financial analysis, document insights
- Tone: Professional financial analyst
- Focus: Accuracy, clarity, actionable insights

### `document_qa.txt`
System prompt for document-based question answering (RAG).
- Used for: Questions about uploaded documents
- Tone: Precise, fact-based
- Focus: Staying within document context, citing sources

### `prompt_improver.txt`
System prompt for the prompt improvement feature.
- Used for: Enhancing user prompts for better AI responses
- Tone: Helpful, optimization-focused
- Focus: Clarity, specificity, structure

## Usage

```python
from src.prompts import get_default_prompt, PromptManager

# Get default prompt
system_prompt = get_default_prompt()

# Get specific prompt
qa_prompt = PromptManager.get_prompt("document_qa")

# List all available prompts
available = PromptManager.list_prompts()

# Reload a prompt (bypass cache)
fresh_prompt = PromptManager.reload_prompt("default")
```

## Adding New Prompts

1. Create a new `.txt` file in this directory
2. Write your system prompt with clear guidelines and structure
3. Use the PromptManager to load it:
   ```python
   custom_prompt = PromptManager.get_prompt("your_prompt_name")
   ```

## Best Practices

1. **Be specific** - Define clear roles and capabilities
2. **Structure well** - Use sections, bullet points, and examples
3. **Set boundaries** - Clearly state what the AI should and shouldn't do
4. **Format guidance** - Specify how responses should be structured
5. **Test thoroughly** - Validate prompts with real use cases
