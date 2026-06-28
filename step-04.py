import anthropic
from anthropic.types import MessageParam

client = anthropic.Anthropic()
conversation = []

for model in client.models.list():
    print(model.id)

print("Chat with Claude (type 'quit' to exit)")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() == "quit":
        break

    conversation.append(MessageParam(role="user", content=user_input))

    response = client.messages.create(
        # model="claude-fable-5",
        # model="claude-opus-4-8",
        # model="claude-sonnet-4-6",
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system="you are a helpful coding assistant.",
        messages=conversation
    )

    assistant_reply = response.content[0].text

    conversation.append(MessageParam(role="assistant", content=assistant_reply))

    print(f"Claude: {assistant_reply}")
