import re

NUM = r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
GLUE = r"(?:\s+(?:level|count))?\s*(?:[:=\-\u2013]|\bis\b|\bwas\b|\bof\b|\bat\b)?\s*"

LABS = [
    {"id": "wbc", "label": "White blood cell count",
     "what": "White blood cells fight infection. This test counts how many are in your blood.",
     "pat": r"WBC|white blood cells?|white (?:blood )?cell count|white count",
     "unit": "thousand cells/\u00b5L", "low": 4.5, "high": 11.0, "thousands": True,
     "range_text": "about 4.5 to 11.0 thousand cells/\u00b5L", "plausible": (0.1, 500), "note": ""},
    {"id": "hgb", "label": "Hemoglobin",
     "what": "Hemoglobin is the protein in red blood cells that carries oxygen around your body.",
     "pat": r"hemoglobin|hgb",
     "unit": "g/dL", "low": 12.0, "high": 17.5, "thousands": False,
     "range_text": "about 12.0 to 17.5 g/dL across adults", "plausible": (2, 25),
     "note": "Normal hemoglobin is different for men and women (roughly 12 to 15.5 for women and 13.5 to 17.5 for men), so a number inside this wide range can still be low or high for you."},
    {"id": "plt", "label": "Platelet count",
     "what": "Platelets are tiny cell pieces that help your blood clot after a cut.",
     "pat": r"platelets?|(?-i:PLT)",
     "unit": "thousand/\u00b5L", "low": 150, "high": 450, "thousands": True,
     "range_text": "about 150 to 450 thousand/\u00b5L", "plausible": (1, 2000), "note": ""},
    {"id": "glu", "label": "Glucose",
     "what": "Glucose is the sugar in your blood. It's your body's main fuel.",
     "pat": r"glucose|blood sugar",
     "unit": "mg/dL", "low": 70, "high": 99, "thousands": False,
     "range_text": "about 70 to 99 mg/dL when fasting", "plausible": (20, 900),
     "note": "Glucose depends on whether you fasted before the test, so this comparison is rough."},
    {"id": "na", "label": "Sodium",
     "what": "Sodium is a salt your body uses to balance fluids and keep nerves and muscles working.",
     "pat": r"sodium|(?-i:Na)\+?",
     "unit": "mmol/L", "low": 135, "high": 145, "thousands": False,
     "range_text": "about 135 to 145 mmol/L", "plausible": (90, 190), "note": ""},
    {"id": "k", "label": "Potassium",
     "what": "Potassium is a mineral your heart and muscles need to work right.",
     "pat": r"potassium|K\+",
     "unit": "mmol/L", "low": 3.5, "high": 5.0, "thousands": False,
     "range_text": "about 3.5 to 5.0 mmol/L", "plausible": (1.5, 9), "note": ""},
    {"id": "cr", "label": "Creatinine",
     "what": "Creatinine is a waste product from your muscles. Your kidneys filter it out, so the level in your blood helps show how well your kidneys are working.",
     "pat": r"creatinine",
     "unit": "mg/dL", "low": 0.6, "high": 1.3, "thousands": False,
     "range_text": "about 0.6 to 1.3 mg/dL across adults", "plausible": (0.1, 30),
     "note": "Normal creatinine is different for men (about 0.7 to 1.3) and women (about 0.6 to 1.1), and it depends on muscle mass, so a number inside this wide range can still be high or low for you."},
    {"id": "a1c", "label": "Hemoglobin A1c",
     "what": "A1c shows your average blood sugar over the past 2 to 3 months.",
     "pat": r"HbA1c|hemoglobin A1c|A1c",
     "unit": "%", "low": None, "high": 5.6, "thousands": False,
     "range_text": "below 5.7%", "plausible": (3, 20),
     "note": "Your doctor decides what your A1c means for you."},
    {"id": "ldl", "label": "LDL cholesterol",
     "what": "LDL is the \"bad\" cholesterol. Too much can build up inside artery walls.",
     "pat": r"LDL(?:[- ]C)?(?:\s+cholesterol)?",
     "unit": "mg/dL", "low": None, "high": 99, "thousands": False,
     "range_text": "below 100 mg/dL", "plausible": (10, 600),
     "note": "Cholesterol goals depend on your overall heart risk, so your target may be different."},
    {"id": "hdl", "label": "HDL cholesterol",
     "what": "HDL is the \"good\" cholesterol. It helps carry other cholesterol away from your arteries.",
     "pat": r"HDL(?:[- ]C)?(?:\s+cholesterol)?",
     "unit": "mg/dL", "low": None, "high": None, "thousands": False,
     "range_text": "", "plausible": (5, 200), "info_only": True,
     "note": "Higher HDL is usually better. Goals are different for men and women."},
    {"id": "tg", "label": "Triglycerides",
     "what": "Triglycerides are a type of fat in your blood that stores extra energy.",
     "pat": r"triglycerides?|(?-i:TG)",
     "unit": "mg/dL", "low": None, "high": 149, "thousands": False,
     "range_text": "below 150 mg/dL", "plausible": (10, 3000), "note": ""},
    {"id": "chol", "label": "Total cholesterol",
     "what": "Total cholesterol adds up all the cholesterol in your blood.",
     "pat": r"total cholesterol|cholesterol",
     "unit": "mg/dL", "low": None, "high": 199, "thousands": False,
     "range_text": "below 200 mg/dL", "plausible": (50, 700), "note": ""},
    {"id": "hr", "label": "Heart rate",
     "what": "Heart rate is how many times your heart beats in a minute.",
     "pat": r"heart rate|(?-i:HR)|pulse",
     "unit": "beats per minute", "low": 60, "high": 100, "thousands": False,
     "range_text": "about 60 to 100 beats per minute at rest", "plausible": (20, 260),
     "note": "Your heart rate goes up with exercise, stress, fever, and some medicines."},
    {"id": "spo2", "label": "Blood oxygen (SpO2)",
     "what": "SpO2 is the percent of your blood that's carrying oxygen. A clip on your finger measures it.",
     "pat": r"SpO2|O2 sat(?:uration)?|oxygen saturation",
     "unit": "%", "low": 95, "high": 100, "thousands": False,
     "range_text": "about 95 to 100%", "plausible": (50, 100),
     "note": "Some people with lung conditions normally run lower. Ask your doctor what's normal for you."},
]

STATUS_TEXT = {
    "below": "Below the typical range",
    "within": "Within the typical range",
    "above": "Above the typical range",
    "info": "Good to know",
}

BP_GUIDE = {
    "id": "bp",
    "label": "Blood pressure",
    "what": "Blood pressure is how hard blood pushes on your artery walls. The top number is the pressure when your heart beats. The bottom number is the pressure between beats.",
    "unit": "mmHg",
    "range_text": "normal is under 120/80",
    "note": "A high blood pressure diagnosis needs readings on more than one day.",
}

BP_CATEGORIES = [
    ("Normal", "Under 120 and under 80"),
    ("Elevated", "120 to 129 and under 80"),
    ("Stage 1 high", "130 to 139 or 80 to 89"),
    ("Stage 2 high", "140 or higher, or 90 or higher"),
    ("Crisis", "Over 180 and/or over 120"),
]

BP_RE = re.compile(
    r"(?:\bBP\b|blood pressure)\s*(?:[:=\-\u2013]|\bis\b|\bwas\b|\bof\b|\bat\b)?\s*(\d{2,3})\s*/\s*(\d{2,3})",
    re.IGNORECASE,
)


def _to_float(num_text):
    return float(num_text.replace(",", ""))


def _lab_regex(lab):
    return re.compile(r"\b(?:" + lab["pat"] + r")\b" + GLUE + NUM, re.IGNORECASE)


_COMPILED = [(lab, _lab_regex(lab)) for lab in LABS]
_BY_ID = {lab["id"]: lab for lab in LABS}


def _lab_result(lab, value):
    if lab.get("info_only"):
        status = "info"
    elif lab["low"] is not None and value < lab["low"]:
        status = "below"
    elif lab["high"] is not None and value > lab["high"]:
        status = "above"
    else:
        status = "within"

    unit_gap = "" if lab["unit"] == "%" else " "
    return {
        "label": lab["label"],
        "value_text": f"{value:g}{unit_gap}{lab['unit']}",
        "status": status,
        "status_text": STATUS_TEXT[status],
        "range_text": ("typical: " + lab["range_text"]) if lab["range_text"] else "",
        "note": lab["note"],
    }


def _bp_result_from_numbers(sys_, dia):
    if sys_ > 180 or dia > 120:
        status, text = "urgent", "In the range the American Heart Association calls a hypertensive crisis"
        note = ("If this is a new reading, sit quietly for a few minutes and check again. Call your doctor soon. "
                "Call 911 if you have chest pain, trouble breathing, weakness, or trouble speaking.")
    elif sys_ >= 140 or dia >= 90:
        status, text = "above", "In the stage 2 high blood pressure range (140/90 or higher)"
        note = "A high blood pressure diagnosis needs readings on more than one day."
    elif sys_ >= 130 or dia >= 80:
        status, text = "above", "In the stage 1 high blood pressure range (130/80 or higher)"
        note = "A high blood pressure diagnosis needs readings on more than one day."
    elif sys_ >= 120:
        status, text = "above", "A little above normal (the \"elevated\" range)"
        note = "Elevated means 120 to 129 over less than 80."
    elif sys_ < 90 or dia < 60:
        status, text = "below", "Below the typical range"
        note = "Low readings mostly matter if you feel dizzy or faint. Ask your doctor."
    else:
        status, text = "within", "Within the normal range (under 120/80)"
        note = ""

    return {
        "label": "Blood pressure",
        "value_text": f"{sys_}/{dia} mmHg",
        "status": status,
        "status_text": text,
        "range_text": "normal is under 120/80 mmHg",
        "note": note,
    }


def find_labs(text):
    found = []

    for m in BP_RE.finditer(text):
        sys_, dia = int(m.group(1)), int(m.group(2))
        if 60 <= sys_ <= 280 and 30 <= dia <= 180 and sys_ > dia:
            result = _bp_result_from_numbers(sys_, dia)
            result["span"] = (m.start(), m.end())
            found.append(result)

    for lab, regex in _COMPILED:
        for m in regex.finditer(text):
            value = _to_float(m.group(m.lastindex))
            if lab["thousands"] and value >= 1000:
                value = value / 1000.0
            low_ok, high_ok = lab["plausible"]
            if not (low_ok <= value <= high_ok):
                continue
            result = _lab_result(lab, value)
            result["span"] = (m.start(), m.end())
            found.append(result)

    found.sort(key=lambda r: -(r["span"][1] - r["span"][0]))
    kept = []
    for r in found:
        s, e = r["span"]
        if any(s < ke and e > ks for ks, ke in (k["span"] for k in kept)):
            continue
        kept.append(r)

    kept.sort(key=lambda r: r["span"][0])
    for r in kept:
        del r["span"]
    return kept


def check_lab(lab_id, value_text, value2_text=""):
    if lab_id == "bp":
        try:
            sys_, dia = int(float(value_text)), int(float(value2_text))
        except (TypeError, ValueError):
            return {"error": "Enter both blood pressure numbers, like 120 and 80."}
        if not (60 <= sys_ <= 280 and 30 <= dia <= 180 and sys_ > dia):
            return {"error": "Those numbers don't look like a blood pressure reading. Check them and try again."}
        return _bp_result_from_numbers(sys_, dia)

    lab = _BY_ID.get(lab_id)
    if not lab:
        return {"error": "Pick a test from the list."}
    try:
        value = float(str(value_text).replace(",", ""))
    except ValueError:
        return {"error": "Enter a number."}
    if lab["thousands"] and value >= 1000:
        value = value / 1000.0
    low_ok, high_ok = lab["plausible"]
    if not (low_ok <= value <= high_ok):
        return {"error": "That number looks off for this test. Double-check the units."}
    return _lab_result(lab, value)


def lab_guide():
    guide = []
    for lab in LABS:
        guide.append({
            "id": lab["id"],
            "label": lab["label"],
            "what": lab["what"],
            "unit": lab["unit"],
            "range_text": lab["range_text"] or "no single cutoff (higher is usually better)",
            "note": lab["note"],
        })
    return guide
