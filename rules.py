"""
Triage rule book for the Symptom-Triage Assistant.

Scope: ADULT, GENERAL symptom triage only (not pediatric, not obstetric,
not a specialty protocol). This is NOT a validated or certified clinical
protocol - it is a small set of rules built by hand-translating publicly
published patient-facing guidance from CDC, the American Heart Association,
Mayo Clinic, and MedlinePlus (NIH/National Library of Medicine) into an
if/then decision list. Every rule below cites exactly which source it came
from, and any rule that does NOT have a real source behind it says so
explicitly instead of pretending otherwise.

Each rule is checked IN ORDER. The first rule whose condition matches the
patient's structured data "fires", and its triage level is returned. Rules
are ordered most-severe-first, so this behaves like a simple decision list.

Levels (most to least severe):
  EMERGENCY   -> call emergency services / go to ER immediately
  URGENT      -> seek care same day (urgent care / ER)
  ROUTINE     -> book a regular doctor's appointment
  SELF_CARE   -> likely manageable at home, monitor symptoms

Structured data shape expected by these rules (produced by extract.py):
{
  "symptoms": ["chest_pain", "shortness_of_breath", ...],  # from SYMPTOM_VOCAB
  "age": 45,                       # int or None
  "duration_hours": 6,             # float or None (kept for future use)
  "vitals": {
     "temperature_c": 39.8,        # float or None
     "spo2_percent": 91,           # int or None
  }
}
"""

# ---------------------------------------------------------------------------
# SOURCES - every citation used below, in one place. (key -> (title, url))
# ---------------------------------------------------------------------------
SOURCES = {
    "cdc_stroke": (
        "CDC - Signs and Symptoms of Stroke",
        "https://www.cdc.gov/stroke/signs-symptoms/index.html",
    ),
    "medlineplus_er": (
        "MedlinePlus (NIH) - When to use the emergency room - adult",
        "https://medlineplus.gov/ency/patientinstructions/000593.htm",
    ),
    "lifeline_988": (
        "988 Suicide & Crisis Lifeline (SAMHSA)",
        "https://www.samhsa.gov/mental-health/988",
    ),
    "aha_heart_attack": (
        "American Heart Association - Warning Signs of a Heart Attack",
        "https://www.heart.org/en/health-topics/heart-attack/warning-signs-of-a-heart-attack",
    ),
    "medlineplus_pulseox": (
        "MedlinePlus (NIH) - Pulse Oximetry",
        "https://medlineplus.gov/lab-tests/pulse-oximetry/",
    ),
    "mayo_coughing_blood": (
        "Mayo Clinic - Coughing up blood: When to see a doctor",
        "https://www.mayoclinic.org/symptoms/coughing-up-blood/basics/when-to-see-doctor/sym-20050934",
    ),
    "cdc_headsup": (
        "CDC HEADS UP - Signs and Symptoms of Concussion (danger signs)",
        "https://www.cdc.gov/heads-up/signs-symptoms/index.html",
    ),
    "mayo_anaphylaxis": (
        "Mayo Clinic - Anaphylaxis: Symptoms & causes",
        "https://www.mayoclinic.org/diseases-conditions/anaphylaxis/symptoms-causes/syc-20351468",
    ),
    "cdc_sepsis": (
        "CDC - Sepsis Signs and Symptoms",
        "https://www.cdc.gov/sepsis/communication-resources/gaos-signs-symptoms.html",
    ),
    "mayo_fever": (
        "Mayo Clinic - Fever: Symptoms & causes",
        "https://www.mayoclinic.org/diseases-conditions/fever/symptoms-causes/syc-20352759",
    ),
    "cdc_flu_65": (
        "CDC - People 65 Years and Older & Flu Risk",
        "https://www.cdc.gov/flu/highrisk/65over.htm",
    ),
    "mayo_abdominal_pain": (
        "Mayo Clinic - Abdominal pain: When to see a doctor",
        "https://www.mayoclinic.org/symptoms/abdominal-pain/basics/when-to-see-doctor/sym-20050728",
    ),
    "none": (
        "Not tied to a specific source - general safe-default reasoning, flagged honestly",
        None,
    ),
}


SYMPTOM_VOCAB = [
    "stroke_signs",            # face droop, arm weakness, slurred speech, sudden vision/balance loss
    "loss_of_consciousness",
    "severe_bleeding",
    "suicidal_ideation",
    "seizure",
    "coughing_blood",
    "severe_head_injury",
    "allergic_reaction_swelling",
    "chest_pain",
    "shortness_of_breath",
    "severe_abdominal_pain",
    "persistent_vomiting",
    "confusion",
    "dizziness",
    "high_fever",              # patient reports a "high" fever in words, not measured
    "mild_fever",
    "headache",
    "sore_throat",
    "cough",
    "runny_nose",
    "rash",
    "fatigue",
    "nausea",
    "diarrhea",
    "severe_pain",
    "moderate_pain",
    "mild_pain",
]

LEVELS = ["EMERGENCY", "URGENT", "ROUTINE", "SELF_CARE"]


def _has(symptoms, *names):
    return any(n in symptoms for n in names)


def _spo2(vitals):
    return (vitals or {}).get("spo2_percent")


def _temp_high(vitals, threshold=39.4):
    # 39.4C / 103F - Mayo Clinic's adult "call your doctor" fever threshold.
    v = (vitals or {}).get("temperature_c")
    return v is not None and v >= threshold


# Each rule: (id, description, condition(fn), level, source_key)
RULES = [
    (
        "R01_stroke_signs",
        "Sudden face drooping, arm weakness, slurred speech, or sudden trouble "
        "seeing/walking/balance - classic stroke warning signs",
        lambda d: _has(d["symptoms"], "stroke_signs"),
        "EMERGENCY",
        "cdc_stroke",
    ),
    (
        "R02_consciousness_seizure",
        "Loss of consciousness/fainting with confusion, or a seizure",
        lambda d: _has(d["symptoms"], "loss_of_consciousness", "seizure"),
        "EMERGENCY",
        "medlineplus_er",
    ),
    (
        "R03_severe_bleeding",
        "Heavy or uncontrolled bleeding",
        lambda d: _has(d["symptoms"], "severe_bleeding"),
        "EMERGENCY",
        "medlineplus_er",
    ),
    (
        "R04_suicidal_ideation",
        "Thoughts of hurting yourself - call/text 988 or go to the ER",
        lambda d: _has(d["symptoms"], "suicidal_ideation"),
        "EMERGENCY",
        "lifeline_988",
    ),
    (
        "R05_chest_pain",
        "Chest discomfort/pressure/pain - a heart attack warning sign. Treated as "
        "EMERGENCY regardless of age or other symptoms, matching AHA's unconditional "
        "'call 911' guidance for this symptom",
        lambda d: _has(d["symptoms"], "chest_pain"),
        "EMERGENCY",
        "aha_heart_attack",
    ),
    (
        "R06_anaphylaxis",
        "Allergic reaction with throat/airway swelling and breathing trouble (anaphylaxis). "
        "Checked before the general breathing-trouble rule below so this more specific, "
        "more informative reason wins when both are present",
        lambda d: _has(d["symptoms"], "allergic_reaction_swelling") and _has(d["symptoms"], "shortness_of_breath"),
        "EMERGENCY",
        "mayo_anaphylaxis",
    ),
    (
        "R07_severe_breathing_trouble",
        "Severe shortness of breath / trouble breathing",
        lambda d: _has(d["symptoms"], "shortness_of_breath"),
        "EMERGENCY",
        "medlineplus_er",
    ),
    (
        "R08_low_oxygen_severe",
        "Measured oxygen saturation (SpO2) 88% or lower",
        lambda d: (_spo2(d.get("vitals")) or 100) <= 88,
        "EMERGENCY",
        "medlineplus_pulseox",
    ),
    (
        "R09_coughing_blood",
        "Coughing up blood",
        lambda d: _has(d["symptoms"], "coughing_blood"),
        "EMERGENCY",
        "medlineplus_er",
    ),
    (
        "R10_severe_head_injury",
        "Head injury with any concussion danger sign (worsening confusion, repeated "
        "vomiting, seizure, slurred speech/weakness, worsening headache)",
        lambda d: _has(d["symptoms"], "severe_head_injury"),
        "EMERGENCY",
        "cdc_headsup",
    ),
    (
        "R11_fever_with_confusion",
        "Fever combined with confusion - a red-flag combination for both sepsis "
        "and serious infection",
        lambda d: _has(d["symptoms"], "high_fever", "mild_fever") and _has(d["symptoms"], "confusion"),
        "EMERGENCY",
        "cdc_sepsis",
    ),
    (
        "R12_low_oxygen_moderate",
        "Measured oxygen saturation (SpO2) 89-92% (normal is 95-100%)",
        lambda d: 88 < (_spo2(d.get("vitals")) or 100) <= 92,
        "URGENT",
        "medlineplus_pulseox",
    ),
    (
        "R13_high_measured_fever",
        "Measured temperature 39.4C / 103F or higher",
        lambda d: _temp_high(d.get("vitals")),
        "URGENT",
        "mayo_fever",
    ),
    (
        "R14_fever_elderly",
        "High fever reported in a patient aged 65+, a group at higher risk of "
        "serious complications from infection",
        lambda d: _has(d["symptoms"], "high_fever") and d.get("age") is not None and d["age"] >= 65,
        "URGENT",
        "cdc_flu_65",
    ),
    (
        "R15_severe_abdominal_pain",
        "Severe abdominal pain, or abdominal pain with vomiting that won't stop, "
        "bloody stools, or severe tenderness",
        lambda d: _has(d["symptoms"], "severe_abdominal_pain") or (
            _has(d["symptoms"], "persistent_vomiting") and _has(d["symptoms"], "severe_pain")
        ),
        "URGENT",
        "mayo_abdominal_pain",
    ),
    (
        "R16_persistent_vomiting",
        "Vomiting that won't stop",
        lambda d: _has(d["symptoms"], "persistent_vomiting"),
        "URGENT",
        "mayo_abdominal_pain",
    ),
    (
        "R17_dizzy_with_severe_pain",
        "Dizziness combined with severe pain. Note: some public guidance lists "
        "persistent dizziness alone as an ER-level sign, but this system can't "
        "reliably tell a fleeting dizzy spell from a persistent one from one "
        "message, so it conservatively only escalates when paired with severe pain",
        lambda d: _has(d["symptoms"], "dizziness") and _has(d["symptoms"], "severe_pain"),
        "URGENT",
        "medlineplus_er",
    ),
    (
        "R18_moderate_or_unmeasured_fever",
        "Moderate pain, or a fever the patient reports but hasn't measured",
        lambda d: _has(d["symptoms"], "moderate_pain", "high_fever"),
        "ROUTINE",
        "none",
    ),
    (
        "R19_common_illness",
        "Mild fever, headache, sore throat, cough, rash, fatigue, nausea, or diarrhea",
        lambda d: _has(d["symptoms"], "mild_fever", "headache", "sore_throat",
                        "cough", "rash", "fatigue", "nausea", "diarrhea"),
        "ROUTINE",
        "none",
    ),
    (
        "R20_default_self_care",
        "No rule above matched; only mild/self-limiting symptoms reported",
        lambda d: True,  # catch-all
        "SELF_CARE",
        "none",
    ),
]


def source_str(source_key: str) -> str:
    """Human-readable 'Title (url)' string for a source key, for display/logging."""
    title, url = SOURCES.get(source_key, SOURCES["none"])
    return f"{title} ({url})" if url else title


def evaluate(structured_data: dict):
    """Run the rules in order; return (rule_id, description, level, source_key)
    for the first match."""
    data = {
        "symptoms": structured_data.get("symptoms") or [],
        "age": structured_data.get("age"),
        "duration_hours": structured_data.get("duration_hours"),
        "vitals": structured_data.get("vitals") or {},
    }
    for rule_id, description, condition, level, source_key in RULES:
        try:
            if condition(data):
                return rule_id, description, level, source_key
        except Exception:
            # Malformed data for this rule -> skip it, don't crash the engine
            continue
    # Should never reach here because R20 always matches
    return "R20_default_self_care", "Default", "SELF_CARE", "none"
