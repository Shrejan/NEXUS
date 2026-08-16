from playwright.sync_api import sync_playwright

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

    prompt.fill("""# Deep Research Prompt

You are an expert research agent. Conduct a **deep, systematic, evidence-based investigation** into the following topic:

**TOPIC:** `get an new invention about black holes`

## 1. Define the Research Problem

* Clearly explain what the topic means.
* Identify the main research question.
* Break the topic into important sub-questions.
* Identify ambiguities, competing definitions, and assumptions.

## 2. Build a Research Plan

Before answering, determine:

* What information needs to be established.
* What evidence is required.
* Which aspects require historical, technical, scientific, economic, or current information.
* What claims need independent verification.

## 3. Search Broadly

Research using multiple high-quality sources, including where appropriate:

* Official documentation and government sources
* Academic papers and research publications
* University sources
* Industry documentation
* Company primary sources
* Reputable news organizations
* Books and historical archives
* Technical reports
* Expert/community discussions when useful

Prioritize **primary sources over secondary sources**.

## 4. Verify Important Claims

For every important factual claim:

* Find supporting evidence.
* Cross-check significant claims with independent sources.
* Identify contradictions between sources.
* Do not treat search-result snippets as sufficient evidence.
* Clearly distinguish established facts from interpretations and speculation.

If reliable evidence cannot be found, explicitly say:

> "Evidence is insufficient to establish this claim."

Never invent missing information.

## 5. Investigate Conflicting Information

When sources disagree:

* Present the competing claims.
* Identify which sources support each claim.
* Compare the quality, date, authority, and methodology of the sources.
* Explain why one explanation may be more credible.
* Do not hide uncertainty.

## 6. Go Beyond Surface-Level Information

Look for:

* Historical context
* Technical details
* Causes and consequences
* Important milestones
* Key people, organizations, or technologies
* Relationships between events
* Alternative explanations
* Common misconceptions
* Limitations and unresolved questions
* Recent developments

Look for information that is **not obvious from the first few search results**.

## 7. Analyze the Evidence

Separate the final findings into:

**Established facts**
Claims strongly supported by reliable evidence.

**Likely conclusions**
Conclusions supported by multiple pieces of evidence but not absolutely certain.

**Uncertain / disputed claims**
Claims where credible sources disagree or evidence is incomplete.

**Speculation**
Reasonable possibilities that are not directly established by evidence.

## 8. Produce the Final Research Report

Structure the answer as:

### Executive Summary

Give the most important conclusions in a concise form.

### Research Question

State exactly what was investigated.

### Background

Explain the necessary context.

### Detailed Findings

Present the research findings systematically.

### Evidence

For important claims, provide the supporting sources and explain what they establish.

### Timeline

If the topic has historical development, provide a chronological timeline.

### Competing Views

Explain important disagreements or alternative interpretations.

### Technical / Detailed Analysis

Go deeper into mechanisms, architecture, methodology, data, or technical details when relevant.

### Important Discoveries

Highlight findings that are surprising, non-obvious, or particularly important.

### Limitations

Explain what could not be established and why.

### Conclusion

Give the strongest evidence-based answer to the original research question.

### Sources

Provide the most important sources used, preferably with direct links.

## 9. Source Quality Rules

Rank evidence approximately as:

1. Primary documents / original research
2. Official government or institutional sources
3. Peer-reviewed academic research
4. Official technical documentation
5. Reputable secondary sources
6. Expert analysis
7. Community discussions
8. Social media / unsourced claims

Use lower-quality sources only when they provide useful information unavailable elsewhere, and clearly identify their limitations.

## 10. Research Discipline

* Do not fabricate sources, quotations, statistics, dates, or citations.
* Do not assume a claim is true because many websites repeat it.
* Prefer the earliest available primary source when investigating historical claims.
* Prefer the newest authoritative source for rapidly changing information.
* Distinguish correlation from causation.
* Distinguish fact from inference.
* Include exact dates when dates matter.
* If information is unavailable, say so.
* If the research question is poorly defined, refine it before proceeding.
* Be skeptical of marketing claims and unsupported expert opinions.

## Final Requirement

Do not simply provide a general explanation of the topic.

Act like a **professional investigative researcher** whose goal is to determine:

**"What is actually true, what evidence supports it, what is uncertain, and what can we confidently conclude?"**

At the end, provide a short **"Bottom Line"** containing the most important conclusion.
""")

    send = page.locator(
        'button[aria-label="Send message"]'
    )

    send.wait_for(state="visible", timeout=10000)
    send.click()

    print("Message sent.")

    page.wait_for_timeout(5000)

    print("\n===== PAGE TEXT =====")
    print(page.locator("body").inner_text())

    input("\nPress Enter to close...")
    context.close()