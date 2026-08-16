from ollama import chat


def get_status():
    """Get the status of Jarvis."""
    return "Jarvis is running."


response = chat(
    model="qwen3:1.7b",
    messages=[
        {
            "role": "user",
            "content": "What is the status of Jarvis?"
        }
    ],
    tools=[get_status],
)

print(response)