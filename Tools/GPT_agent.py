from playwright.sync_api import sync_playwright
from ollama import chat



def run_chatgpt(prompt_text):
    """Run ChatGPT with the your prompt text. keep the prompt text short and concise. The function will open a browser window, navigate to ChatGPT, fill in the prompt, and send the message. It will then print the page text and wait for user input before closing the browser."""
    with sync_playwright() as p:

    
        context = p.chromium.launch_persistent_context(
                user_data_dir=r"C:\Users\User\code_file_folder\jarvis\whatsapp_profile",
                headless=False
            )
        page = context.pages[0] if context.pages else context.new_page()

        page.goto("https://chatgpt.com/")

        print("Opening ChatGPT...")

        prompt = page.locator(
            'textarea[aria-label="Chat with ChatGPT"]'
        )

        prompt.wait_for(state="visible", timeout=60000)

        print("ChatGPT composer found.")

        prompt.fill(prompt_text)

        send = page.locator(
            'button[aria-label="Send message"]'
        )

        send.wait_for(state="visible", timeout=10000)
        send.click()

        print("Message sent.")

        page.wait_for_timeout(5000)
        
        cuntent=page.locator("body").inner_text()

        context.close()

    return cuntent






def processing_chatGPT_response(prompt_text, response_text):
    """
    Use Qwen to extract the actual ChatGPT response
    from messy DOM-extracted text.
    """

    system_prompt = """
You are a response extraction system.

The input contains:
1. The original user prompt.
2. A messy response extracted from ChatGPT's DOM.

Your job is to extract ONLY the actual ChatGPT answer.

Remove:
- UI elements
- buttons
- usernames
- timestamps
- navigation text
- "Copy"
- "Regenerate"
- "Edit"
- DOM artifacts
- duplicated text
- irrelevant interface content

IMPORTANT:
- Preserve the meaning of ChatGPT's answer.
- Do not answer the original prompt yourself.
- Do not summarize.
- Do not explain your extraction.
- Do not add anything.
- Return ONLY the cleaned ChatGPT response.
"""

    user_content = f"""
ORIGINAL PROMPT:
{prompt_text}

MESSY CHATGPT RESPONSE:
{response_text}
"""

    response = chat(
        model="qwen3:1.7b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
    )

    return response.message.content.strip()
