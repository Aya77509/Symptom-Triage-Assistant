"""
The baseline you compare the hybrid pipeline against: just ask the LLM
directly for a triage level, no rules involved. This is "what most
people's first chatbot prototype would do."
"""

from ollama_client import chat

VALID_LEVELS = ["EMERGENCY", "URGENT", "ROUTINE", "SELF_CARE"]

SYSTEM_PROMPT = """You are a medical triage assistant. Given a patient's
description of their symptoms, decide how urgently they need care.

Respond with ONLY one word, exactly one of:
EMERGENCY, URGENT, ROUTINE, SELF_CARE

EMERGENCY = call emergency services / go to ER right now
URGENT = seek care today
ROUTINE = book a regular appointment
SELF_CARE = likely manageable at home
"""


def run_baseline(patient_text: str) -> str:
    raw = chat(prompt=patient_text, system=SYSTEM_PROMPT, temperature=0.0).strip().upper()
    for level in VALID_LEVELS:
        if level in raw:
            return level
    return "UNPARSEABLE:" + raw[:50]


if __name__ == "__main__":
    example = "I'm 52 and I've had crushing chest pain for the last hour, and I feel short of breath."
    print(run_baseline(example))
