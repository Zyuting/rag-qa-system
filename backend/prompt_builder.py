"""Prompt construction for the RAG QA system.

Builds structured prompts containing: KB context, conversation history,
retrieved reference documents, and generation rules.
"""

KB_DISPLAY_NAMES = {
    "dongba": "东巴文化",
    "puercha": "普洱茶制作技艺",
    "zharan": "扎染",
    "huobajie": "火把节",
    "poshuijie": "泼水节",
    "kongquewu": "孔雀舞",
    "naxiguyue": "纳西古乐",
    "jianshuizitao": "建水紫陶",
    "wutong": "乌铜走银",
    "heqingyinqi": "鹤庆银器",
}


def build_prompt(query: str, retrieved: list[dict], history_text: str, kb_name: str = "") -> str:
    """Build a structured prompt with context, history, and rules.

    Args:
        query: The user's question.
        retrieved: List of retrieved chunks with content/filename fields.
        history_text: Recent conversation history as formatted text.
        kb_name: Knowledge base identifier for display.

    Returns:
        A formatted prompt string ready for LLM ingestion.
    """
    context_parts = []
    for i, chunk in enumerate(retrieved, 1):
        context_parts.append(
            f"[Reference {i}]\n"
            f"File: {chunk.get('filename', 'unknown')}\n"
            f"Content:\n{chunk.get('content', '')}\n"
        )
    context = "\n".join(context_parts)

    history_section = ""
    if history_text.strip():
        history_section = f"\n## Conversation History\n{history_text}\n"

    kb_display = KB_DISPLAY_NAMES.get(kb_name, kb_name)
    prompt = f"""You are a knowledge base Q&A assistant specializing in Yunnan's intangible cultural heritage. Current knowledge base: [{kb_display}].

{history_section}
## Reference Context
{context}

## Question
{query}

## Rules
1. Only answer if the question is relevant to the current knowledge base.
2. Base your answer primarily on the reference context provided.
3. You may supplement with your own knowledge, but no more than 30% of the answer.
4. Cite source filenames at the end.
5. Respond in Chinese unless asked otherwise.

Answer:"""
    return prompt
