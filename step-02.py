import anthropic
from anthropic.types import MessageParam

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system="You are a senior Python developer. Keep answers concise and practical.",
    messages=[
        MessageParam(role="user",
                     content="Write a function that checks if a string is a valid email address. No Regex.")
    ]
)

# The response text
print(message.content[0].text)

# Did Claude finish or get cut off?
print(f"stop reason: {message.stop_reason}")

# Token usage for cost tracking
print(f"Input Tokens: {message.usage.input_tokens}")
print(f"Output Tokens: {message.usage.output_tokens}")
