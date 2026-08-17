from ollama import chat
from Tools.GPT_agent import run_chatgpt ,processing_chatGPT_response
from Tools.WA_agent import whatsapp_send_message
 
def get_status():
    """Get the status of Jarvis."""
    return "Jarvis is running."


response = chat(
    model="qwen3:1.7b",
    messages=[
        {
            "role": "user",
            "content": "can you ask gpt to write an email to my boss saying I am sick and can't come to work today?"
        }
    ],
    tools=[get_status,
           run_chatgpt,
           whatsapp_send_message],
)

print("Qwen response:")
print(response.message.thinking)
print(response.message.tool_calls)

#Check if Qwen requested a tool
if response.message.tool_calls:

    for tool_call in response.message.tool_calls:

        print("TOOL REQUESTED:")
        print(tool_call.function.name)

        if tool_call.function.name == "get_status":

            # ACTUALLY EXECUTE YOUR PYTHON FUNCTION
            result = get_status()

            print("TOOL RESULT:")
            print(result)

            
        elif tool_call.function.name == "run_chatgpt":
            # ACTUALLY EXECUTE YOUR PYTHON FUNCTION
            result = run_chatgpt(tool_call.function.arguments["prompt_text"])
            fresult = processing_chatGPT_response(
                            prompt_text=tool_call.function.arguments["prompt_text"],
                            response_text=result
                        )
            print("TOOL RESULT:")
            print(fresult)


        elif tool_call.function.name == "whatsapp_send_message":
            # ACTUALLY EXECUTE YOUR PYTHON FUNCTION
            result = whatsapp_send_message(
                contact_name=tool_call.function.arguments["contact_name"],
                message_text=tool_call.function.arguments["message_text"]
            )
            

            print("TOOL RESULT:")
            print(result)