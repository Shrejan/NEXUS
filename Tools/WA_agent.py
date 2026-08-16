from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=r"C:\Users\User\code_file_folder\jarvis\whatsapp_profile",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://web.whatsapp.com")

    print("Waiting for WhatsApp to load (scan QR if needed)...")
    page.wait_for_selector("#pane-side", timeout=120000)
    print("WhatsApp loaded.")

    # --- Search for the contact ---
    search = page.locator('input[aria-label="Search or start a new chat"]').first
    search.wait_for(state="visible", timeout=10000)
    search.click()
    search.fill("")
    search.type("shravan", delay=50)
    page.wait_for_timeout(1500)

    # --- Open the chat: click the first row in the results list ---
    # WhatsApp puts search results as rows with role="listitem" or similar under #pane-side
    result_row = page.locator('#pane-side div[role="listitem"]').first
    try:
        result_row.wait_for(state="visible", timeout=8000)
        result_row.click()
    except PWTimeout:
        # fallback: try any span with a title attribute containing "shravan" (case-insensitive)
        fallback = page.locator('span[title]').filter(has_text="hravan").first
        fallback.wait_for(state="visible", timeout=8000)
        fallback.click()

    page.wait_for_timeout(1000)

    # --- Find the message box ---
    message_box = page.locator('footer div[contenteditable="true"]').last
    message_box.wait_for(state="visible", timeout=10000)
    message_box.click()
    message_box.type("I'm busy. Go and find it yourself.", delay=30)

    page.wait_for_timeout(300)
    message_box.press("Enter")

    print("Message sent!")

    page.wait_for_timeout(2000)
    context.close()