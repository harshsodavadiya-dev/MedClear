import json
import os
import re

from labs import find_labs
from readability import reading_grade
from wordparts import segment

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_CHARS = 5000


def _load(name, required=True):
    path = os.path.join(BASE_DIR, name)
    if not os.path.exists(path):
        if required:
            raise FileNotFoundError(f"{name} is missing. Run: python build_terms.py")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


TERMS = _load("terms.json")
PHRASES = _load("phrases.json")
IMPORTED = _load("medlineplus_terms.json", required=False)

for _key in list(IMPORTED):
    if _key in TERMS:
        del IMPORTED[_key]

TERM_TOTAL = len(TERMS) + len(IMPORTED)


def get_info(key):
    return TERMS.get(key) or IMPORTED[key]


def _term_regex(term, info):
    body = re.escape(term)
    if info.get("abbr"):
        return re.compile(r"\b" + body + r"\b")
    return re.compile(r"\b" + body + r"(?:s|es)?\b", re.IGNORECASE)


TERM_PATTERNS = [(term, _term_regex(term, info)) for term, info in TERMS.items()]
PHRASE_PATTERNS = [(re.compile(r"\b" + p["pattern"] + r"\b", re.IGNORECASE), p["swap"]) for p in PHRASES]

_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")
_MAX_IMPORTED_WORDS = 5


def _imported_candidates(text):
    if not IMPORTED:
        return []
    tokens = [(m.start(), m.end()) for m in _WORD.finditer(text)]
    found = []
    for i in range(len(tokens)):
        for n in range(min(_MAX_IMPORTED_WORDS, len(tokens) - i), 0, -1):
            start, end = tokens[i][0], tokens[i + n - 1][1]
            key = re.sub(r"\s+", " ", text[start:end]).lower()
            hit = None
            for candidate in (key, key[:-1] if key.endswith("s") else None, key[:-2] if key.endswith("es") else None):
                if candidate and candidate in IMPORTED:
                    hit = candidate
                    break
            if hit:
                found.append((start, end, "term", hit))
                break
    return found


_ROMAN_CONTEXT = re.compile(
    r"(?:\b(?:[Ss]tages?|[Gg]rades?|[Tt]ypes?|[Cc]lass(?:es)?|[Pp]hases?|[Gg]roups?|[Ff]actor|[Ll]evels?|[Tt]iers?|[Cc]ategory|NYHA)"
    r"\s+(?:[IVX]+[ABCabc]?\s*(?:/|-|\u2013|,|or|and|to)\s*)*)$"
)
_ROMAN_LOOKALIKES = {"IV"}


def find_spans(text):
    candidates = []
    for term, regex in TERM_PATTERNS:
        for m in regex.finditer(text):
            if term in _ROMAN_LOOKALIKES and _ROMAN_CONTEXT.search(text[:m.start()]):
                continue
            candidates.append((m.start(), m.end(), "term", term))
    for index, (regex, _swap) in enumerate(PHRASE_PATTERNS):
        for m in regex.finditer(text):
            candidates.append((m.start(), m.end(), "phrase", index))
    candidates.extend(_imported_candidates(text))

    candidates.sort(key=lambda c: (-(c[1] - c[0]), c[0]))

    taken = []
    for start, end, kind, key in candidates:
        if any(start < t_end and end > t_start for t_start, t_end, _, _ in taken):
            continue
        taken.append((start, end, kind, key))

    taken.sort()
    return taken


def _starts_sentence(text, pos):
    i = pos - 1
    while i >= 0 and text[i] in " \t\"'(":
        i -= 1
    return i < 0 or text[i] in ".!?\n"


_ARTICLE_AT_END = re.compile(r"\b([Aa]n?)(\s+)$")
_SOUNDS_LIKE_CONSONANT = ("uri", "uni", "use", "usu", "uti", "eu", "one", "once")


def _article_for(word):
    w = word.lower()
    if w.startswith(_SOUNDS_LIKE_CONSONANT):
        return "a"
    return "an" if w[:1] in "aeiou" else "a"


def _fix_article(before, swap):
    m = _ARTICLE_AT_END.search(before)
    if not m:
        return before
    article = _article_for(swap)
    if m.group(1)[0].isupper():
        article = article.capitalize()
    return before[:m.start(1)] + article + m.group(2)


def _swap_for(kind, key, original):
    if kind == "phrase":
        return PHRASE_PATTERNS[key][1]
    info = get_info(key)
    swap = info.get("swap")
    if swap:
        is_plural = original.lower() != key.lower() and original.lower().startswith(key.lower())
        if is_plural and " " not in swap and "(" not in swap:
            swap += "s"
        return swap
    if info.get("source") == "MedlinePlus":
        return original
    return f"{original} ({info['plain'].split('.')[0].lower()})"


def make_plain_text(text, spans):
    pieces = []
    pos = 0
    for start, end, kind, key in spans:
        swap = _swap_for(kind, key, text[start:end])
        before = _fix_article(text[pos:start], swap)
        pieces.append(before)
        if _starts_sentence(text, start):
            swap = swap[0].upper() + swap[1:]
        pieces.append(swap)
        pos = end
    pieces.append(text[pos:])
    return "".join(pieces)


_MEDICAL_ENDINGS = (r"itis|osis|emia|aemia|pathy|ectomy|ostomy|otomy|plasty|scopy|"
                    r"algia|penia|megaly|plegia|rrhea|uria|oma")
_SUSPECT = re.compile(r"[A-Za-z]{4,}(?:" + _MEDICAL_ENDINGS + r")", re.IGNORECASE)

_NOT_MEDICAL = {
    "diploma", "aroma", "diagnosis", "hypothesis", "analysis", "emphasis", "synthesis",
    "sympathy", "empathy", "apathy", "antipathy", "nostalgia", "academia", "bohemia",
    "genesis", "metropolis", "thesis", "paralysis", "oasis",
    "colonial", "anticolonial", "neocolonial", "postcolonial", "precolonial",
    "alderman", "anagram", "analogy", "anadiplosis", "anamorphosis", "antilogy", "apodosis",
    "apotheosis", "biography", "biology", "chemosmosis", "diagram", "dichotomy", "trichotomy",
    "epanorthosis", "epigram", "epigraphy", "eugenic", "eulogy", "heterography", "histogram",
    "homology", "horoscopy", "hydrography", "hydrology", "hydrolysis", "hypnosis", "hysteria",
    "intrapreneur", "intrapreneurial", "kurtosis", "lithography", "lithology", "macrobiotic",
    "macrography", "macrology", "malacology", "mammalian", "mammalogy", "melancholic",
    "metamorphosis", "metapsychology", "metempsychosis", "microanalysis", "micrography",
    "microlith", "microlithic", "morphosis", "neolith", "neolithic", "neology", "oligopoly",
    "parapsychology", "periderm", "perisarc", "psychoanal", "psychoanalysis", "psychognosis",
    "psychology", "sociopathy", "spectroscopy", "splendent", "stereoscopy", "stereotomy",
    "stomata", "symbiosis", "tachygraphy", "telepathy", "telescopy", "trident", "trigram",
    "trilogy", "trihydric", "uniocular", "pneuma",
}


def _is_common_word(word):
    stems = [word]
    if word.endswith("es"):
        stems.append(word[:-2])
    if word.endswith("s"):
        stems.append(word[:-1])
    return any(s in _NOT_MEDICAL for s in stems)


def find_unrecognized(text, spans):
    covered = [(s, e) for s, e, _, _ in spans]
    found = []
    seen = set()
    for m in re.finditer(r"[A-Za-z]{6,}", text):
        word = m.group(0).lower()
        if word in seen or word in _NOT_MEDICAL or word in TERMS or word in IMPORTED:
            continue
        if any(m.start() < e and m.end() > s for s, e in covered):
            continue
        if _is_common_word(word):
            continue
        parts = segment(word, strict=True)
        if parts or _SUSPECT.fullmatch(word):
            seen.add(word)
            found.append({"word": word, "parts": parts or []})
    return found[:8]


QUESTIONS_BY_CATEGORY = {
    "Medications": "What is this medicine for, what side effects should I watch for, and what do I do if I miss a dose?",
    "Diagnosis & Results": "What does this result mean for me, and what happens next?",
    "Heart & Circulation": "Should I be tracking anything at home, like blood pressure or heart rate?",
    "Blood & Labs": "Is this result normal for me, and should we repeat the test?",
    "Hormones & Diabetes": "How often should I check my blood sugar, and what numbers should I aim for?",
    "Lungs & Breathing": "Which breathing symptoms mean I should get care right away?",
    "Digestion, Liver & Kidneys": "Are there foods, drinks, or medicines I should avoid?",
    "Body Systems & Symptoms": "What symptoms mean I should call you or go to the ER?",
}
GENERIC_QUESTION = "What should I do next, and when should I follow up?"


def build_questions(matches, labs):
    questions = []
    if labs:
        questions.append("Some of my lab numbers are outside the typical range. Does that matter for me, and when should we recheck?")
    for m in matches:
        q = QUESTIONS_BY_CATEGORY.get(m["category"])
        if q and q not in questions:
            questions.append(q)
    questions.append(GENERIC_QUESTION)
    return questions[:5]


def analyze(text):
    spans = find_spans(text)
    term_spans = [s for s in spans if s[2] == "term"]

    segments = []
    pos = 0
    for start, end, _, key in term_spans:
        if start > pos:
            segments.append({"text": text[pos:start]})
        segments.append({"text": text[start:end], "term": key})
        pos = end
    if pos < len(text):
        segments.append({"text": text[pos:]})

    matches = []
    seen = set()
    for _, _, _, key in term_spans:
        if key in seen:
            continue
        seen.add(key)
        info = get_info(key)
        matches.append({
            "term": key,
            "plain": info["plain"],
            "analogy": info.get("analogy", ""),
            "category": info.get("category", "General"),
            "source": info.get("source", "MedClear glossary"),
            "url": info.get("url", ""),
        })

    labs = find_labs(text)
    plain_text = make_plain_text(text, spans)

    return {
        "segments": segments,
        "matches": matches,
        "labs": labs,
        "plain_text": plain_text,
        "unrecognized": find_unrecognized(text, spans),
        "questions": build_questions(matches, labs),
        "stats": {
            "terms": len(matches),
            "labs": len(labs),
            "grade_before": reading_grade(text),
            "grade_after": reading_grade(plain_text),
        },
    }


def glossary_categories():
    categories = sorted({info.get("category", "General") for info in TERMS.values()})
    if IMPORTED:
        categories.append("From MedlinePlus")
    return categories


def glossary_search(query="", category="", offset=0, limit=40):
    q = query.strip().lower()
    rows = []

    def consider(key, info, source):
        cat = info.get("category", "General")
        if category and cat != category:
            return
        if q and q not in key.lower() and q not in info["plain"].lower():
            return
        rank = 0 if key.lower().startswith(q) else 1 if q in key.lower() else 2
        rows.append((rank, key.lower(), {
            "term": key,
            "plain": info["plain"],
            "analogy": info.get("analogy", ""),
            "category": cat,
            "source": source,
            "url": info.get("url", ""),
        }))

    for key, info in TERMS.items():
        consider(key, info, "MedClear glossary")
    for key, info in IMPORTED.items():
        consider(key, info, "MedlinePlus")

    rows.sort(key=lambda r: (r[0], r[1]))
    items = [r[2] for r in rows]
    return {"total": len(items), "items": items[offset:offset + limit]}
