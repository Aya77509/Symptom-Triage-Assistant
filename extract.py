"""
Step 1 of the hybrid pipeline: turn a free-text patient description into
structured facts the rule engine (rules.py) can understand.

This is the "neural" half - the LLM's only job here is translation
(messy language -> clean fields), NOT deciding urgency. The rules decide.
"""

from ollama_client import chat, extract_json
from rules import SYMPTOM_VOCAB

SYSTEM_PROMPT = f"""You are a medical intake assistant. Your ONLY job is to read a
patient's free-text description and extract structured facts as JSON.
Do NOT diagnose. Do NOT decide urgency or triage level. Just extract facts.

Map anything the patient mentions to this FIXED list of symptom tags
(use ONLY tags from this list, pick every tag that applies, use an
empty list if none apply):
{", ".join(SYMPTOM_VOCAB)}

Output ONLY a single JSON object with exactly this shape, no extra text:
{{
  "symptoms": ["tag1", "tag2"],
  "age": <integer or null>,
  "duration_hours": <number or null, convert days to hours>,
  "vitals": {{
    "temperature_c": <number or null, convert F to C if needed>,
    "spo2_percent": <integer or null>
  }},
  "notes": "<anything medically relevant that didn't fit the tags, 1 sentence, or empty string>"
}}
"""


def extract_structured_data(patient_text: str) -> dict:
    raw = chat(prompt=patient_text, system=SYSTEM_PROMPT, json_mode=True, temperature=0.0)
    data = extract_json(raw)

    # Defensive cleanup: drop any symptom tag the model invented outside our vocab
    symptoms = data.get("symptoms") or []
    data["symptoms"] = [s for s in symptoms if s in SYMPTOM_VOCAB]

    data.setdefault("age", None)
    data.setdefault("duration_hours", None)
    data.setdefault("vitals", {})
    data.setdefault("notes", "")
    return data


if __name__ == "__main__":
    example = (
        "I'm 52 and I've had crushing chest pain for the last hour, "
        "and I feel short of breath."
    )
    print(extract_structured_data(example))
