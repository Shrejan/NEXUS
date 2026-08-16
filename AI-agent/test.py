import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")


llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
search = TavilySearch(max_results=3)


def ask_llm(prompt: str) -> str:
    return llm.invoke(prompt).content.strip()


def run_search(query: str) -> str:
    result = search.invoke({"query": query})
    chunks = [f"[{r.get('url')}] {r.get('content', '')}" for r in result.get("results", [])]
    return "\n\n".join(chunks)


# --------------------------------------------------
# 1. RESEARCH PLAN
# --------------------------------------------------

def make_research_plan(question: str) -> str:
    prompt = f"""Question: {question}

List 2-3 short search queries that would help research this question.
One query per line. No numbering, no extra text.
"""
    return ask_llm(prompt)


# --------------------------------------------------
# 2 & 3. SEARCH + INSPECT SOURCES
# --------------------------------------------------

def search_sources(queries: list) -> str:
    all_results = []
    for q in queries:
        print(f"Searching: {q}")
        all_results.append(run_search(q))
    return "\n\n".join(all_results)


# --------------------------------------------------
# 4. EXTRACT EVIDENCE
# --------------------------------------------------

def extract_evidence(question: str, raw_sources: str) -> str:
    prompt = f"""Question: {question}

Sources:
{raw_sources}

Extract the key facts relevant to the question as short bullet points.
Include the source URL next to each fact in brackets.
"""
    return ask_llm(prompt)


# --------------------------------------------------
# 5. FIND GAPS + SEARCH AGAIN
# --------------------------------------------------

def find_gaps(question: str, evidence: str) -> str:
    prompt = f"""Question: {question}

Evidence gathered so far:
{evidence}

What important information is still missing to fully answer the question?
List 1-2 short follow-up search queries to fill these gaps.
If nothing is missing, reply with just: NONE
"""
    return ask_llm(prompt)


# --------------------------------------------------
# 6. CROSS-CHECK CONTRADICTIONS
# --------------------------------------------------

def cross_check(question: str, evidence: str) -> str:
    prompt = f"""Question: {question}

Evidence:
{evidence}

Check this evidence for contradictions or disagreements between sources.
Briefly note any conflicts found, or say "No contradictions found."
"""
    return ask_llm(prompt)


# --------------------------------------------------
# 7. FINAL CONCLUSION
# --------------------------------------------------

def make_conclusion(question: str, evidence: str, contradictions: str) -> str:
    prompt = f"""Question: {question}

Evidence:
{evidence}

Contradiction check:
{contradictions}

Based only on the evidence above, write a clear final answer to the question.
If sources disagree, mention it briefly.
"""
    return ask_llm(prompt)


# --------------------------------------------------
# PIPELINE
# --------------------------------------------------

def research(question: str) -> str:
    print("\nQUESTION:", question)

    plan = make_research_plan(question)
    queries = [q.strip("-• ").strip() for q in plan.splitlines() if q.strip()]
    print("\nRESEARCH PLAN:\n", plan)

    raw_sources = search_sources(queries)

    evidence = extract_evidence(question, raw_sources)
    print("\nEVIDENCE:\n", evidence)

    gaps = find_gaps(question, evidence)
    print("\nGAPS:\n", gaps)

    if gaps.strip().upper() != "NONE":
        gap_queries = [q.strip("-• ").strip() for q in gaps.splitlines() if q.strip()]
        more_sources = search_sources(gap_queries)
        more_evidence = extract_evidence(question, more_sources)
        evidence += "\n" + more_evidence
        print("\nADDITIONAL EVIDENCE:\n", more_evidence)

    contradictions = cross_check(question, evidence)
    print("\nCONTRADICTION CHECK:\n", contradictions)

    conclusion = make_conclusion(question, evidence, contradictions)
    print("\nCONCLUSION:\n", conclusion)

    return conclusion


if __name__ == "__main__":
    question = """Conduct an evidence-based investigation into the following:

"Reconstruct the development timeline of NVIDIA's GPU computing platform from the earliest publicly documented programmable-GPU computing efforts through the introduction of CUDA and the first CUDA-capable Tesla products.

Your task is not to give me a general history. I want you to discover evidence that is difficult to retrieve from ordinary summaries.

Search the web extensively and identify:

1. The earliest publicly accessible NVIDIA document you can find describing GPU computation for purposes beyond traditional graphics.
2. The earliest evidence you can find for the CUDA name itself.
3. The earliest official NVIDIA documentation that describes CUDA as a programming platform.
4. The first CUDA-capable GPU/product you can verify from primary sources.
5. The first CUDA Toolkit release you can verify.
6. The relationship between CUDA, Tesla, and NVIDIA's earlier GPU-computing initiatives.
7. Any discrepancies between NVIDIA's current historical pages and contemporary documents.

For every major claim:
- provide the source,
- publication date,
- URL,
- whether it is a primary or secondary source,
- and explain why you consider it reliable.

Search beyond the first page of search results.

Look for archived pages, old NVIDIA PDFs, conference presentations, technical papers, press releases, and contemporary documentation.

Do not assume that the first search result is correct.

If two sources disagree, investigate the disagreement.

At the end, construct a chronological table containing:

Date | Event | Evidence | Source | Confidence

Your final answer must clearly separate:
A. Directly verified facts
B. Strongly supported conclusions
C. Uncertain or unresolved claims

Do not use your pretrained knowledge to fill missing evidence. If you cannot verify something, explicitly say "I could not verify this."""
    research(question)