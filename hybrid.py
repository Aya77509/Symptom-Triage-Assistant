"""
The full hybrid pipeline: LLM extracts facts -> rules.py decides the
triage level (deterministic, traceable) -> LLM explains the decision
in plain language.

This is what you compare against baseline.py (pure-LLM, no rules).
"""
import re
from extract import extract_structured_data
from rules import evaluate, source_str, SOURCES
from ollama_client import chat

EXPLAIN_SYSTEM_PROMPT = """You are a calm, clear medical intake assistant.
You will be given a triage decision that was already made by a fixed
rule book (you do not get to change it). Explain it to the patient in
2-3 short sentences, in plain language, mentioning the relevant symptom(s)
that led to it. End with a brief reminder that this is not a diagnosis.

Output ONLY those 2-3 patient-facing sentences. Nothing else.
Do NOT include a preamble like "Here's the explanation:" or "Sure,".
Do NOT include a "Note:" or any comment about your own reasoning,
what instructions you followed, or what you chose to leave out.
Do NOT wrap the output in quotation marks."""

# Defensive cleanup: strip common preambles/meta-commentary the model adds
# despite being told not to (small local models don't always follow
# "output only X" instructions perfectly).
_PREAMBLE_RE = re.compile(
    r'^\s*(here[\'’]?s?( is)? (the )?explanation:?|sure[,!]?|okay[,!]?|certainly[,!]?)\s*:?\s*\n+',
    re.IGNORECASE,
)
_TRAILING_NOTE_RE = re.compile(r'\n+\s*note:.*$', re.IGNORECASE | re.DOTALL)


def _clean_explanation(text: str) -> str:
    text = text.strip()
    text = _PREAMBLE_RE.sub('', text)
    text = _TRAILING_NOTE_RE.sub('', text)
    text = text.strip()
    # Strip a single pair of wrapping quotes, if the model added them anyway
    if len(text) >= 2 and text[0] in '"“' and text[-1] in '"”':
        text = text[1:-1].strip()
    return text


def run_hybrid(patient_text: str) -> dict:
    structured = extract_structured_data(patient_text)
    rule_id, rule_description, level, source_key = evaluate(structured)
    source = source_str(source_key)
    source_title, source_url = SOURCES.get(source_key, SOURCES["none"])

    explanation_prompt = (
        f"Patient said: \"{patient_text}\"\n"
        f"Extracted facts: {structured}\n"
        f"Triage level decided by the rule book: {level}\n"
        f"Reason the rule book gave: {rule_description}\n\n"
        f"Write the patient-facing explanation now."
    )
    raw_explanation = chat(prompt=explanation_prompt, system=EXPLAIN_SYSTEM_PROMPT, temperature=0.3)
    explanation = _clean_explanation(raw_explanation)

    return {
        "level": level,
        "rule_id": rule_id,
        "rule_description": rule_description,
        "source": source,
        "source_title": source_title,
        "source_url": source_url,
        "structured_data": structured,
        "explanation": explanation,
    }


if __name__ == "__main__":
    example = "I'm 52 and I've had crushing chest pain for the last hour, and I feel short of breath."
    result = run_hybrid(example)
    print(f"Level: {result['level']}  (rule: {result['rule_id']} - {result['rule_description']})")
    print(f"Structured data: {result['structured_data']}")
    print(f"Explanation: {result['explanation']}")
