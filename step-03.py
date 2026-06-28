import anthropic
from anthropic.types import MessageParam

client = anthropic.Anthropic()

conversation = [MessageParam(role="user", content="What is the capital of France?")]

# First turn
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    messages=conversation
)

assistant_reply = response.content[0].text

# The response text
print(f"Claude: {assistant_reply}")

# Add Claude's response to the conversation history

conversation.append(MessageParam(role="assistant", content=assistant_reply))

# Second turn

conversation.append(MessageParam(role="user", content="What's its population?"))

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    messages=conversation
)

print(f"Claude: {response.content[0].text}")
