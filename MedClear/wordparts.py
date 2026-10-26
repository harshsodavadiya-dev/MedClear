import re
from functools import lru_cache

PARTS_LIST = [
    ("a", "prefix", "without"), ("an", "prefix", "without"),
    ("anti", "prefix", "against"), ("brady", "prefix", "slow"), ("tachy", "prefix", "fast"),
    ("dys", "prefix", "painful, difficult, or abnormal"), ("endo", "prefix", "inside"),
    ("epi", "prefix", "upon or above"), ("ex", "prefix", "out of"), ("exo", "prefix", "outside"),
    ("hyper", "prefix", "above normal or too much"), ("hypo", "prefix", "below normal or too little"),
    ("inter", "prefix", "between"), ("intra", "prefix", "within"), ("macro", "prefix", "large"),
    ("micro", "prefix", "small"), ("mal", "prefix", "bad"), ("meta", "prefix", "change or beyond"),
    ("neo", "prefix", "new"), ("pan", "prefix", "all"), ("para", "prefix", "beside or abnormal"),
    ("peri", "prefix", "around"), ("poly", "prefix", "many"), ("post", "prefix", "after"),
    ("pre", "prefix", "before"), ("pseudo", "prefix", "false"), ("retro", "prefix", "behind or backward"),
    ("sub", "prefix", "under"), ("supra", "prefix", "above"), ("syn", "prefix", "together"),
    ("trans", "prefix", "across"), ("tri", "prefix", "three"), ("uni", "prefix", "one"),
    ("bi", "prefix", "two"), ("hemi", "prefix", "half"), ("dia", "prefix", "through"),
    ("eu", "prefix", "good or normal"), ("oligo", "prefix", "few or scanty"),
    ("contra", "prefix", "against"), ("extra", "prefix", "outside"), ("ecto", "prefix", "outer"),
    ("hetero", "prefix", "different"), ("homo", "prefix", "same"),

    ("abdomin", "root", "belly"), ("aden", "root", "gland"), ("adip", "root", "fat"),
    ("angi", "root", "blood vessel"), ("append", "root", "appendix"), ("appendic", "root", "appendix"),
    ("arteri", "root", "artery"), ("arthr", "root", "joint"), ("ather", "root", "fatty plaque"),
    ("bronch", "root", "airway"), ("cardi", "root", "heart"), ("carcin", "root", "cancer"),
    ("cephal", "root", "head"), ("cerebr", "root", "brain"), ("chol", "root", "bile"),
    ("cholecyst", "root", "gallbladder"), ("chondr", "root", "cartilage"), ("cocc", "root", "round bacteria"),
    ("col", "root", "colon"), ("colon", "root", "colon"), ("cost", "root", "rib"),
    ("crani", "root", "skull"), ("cutane", "root", "skin"), ("cyst", "root", "bladder or sac"),
    ("cyt", "root", "cell"), ("dent", "root", "tooth"), ("derm", "root", "skin"),
    ("dermat", "root", "skin"), ("duoden", "root", "first part of the small intestine"),
    ("encephal", "root", "brain"), ("enter", "root", "intestine"), ("erythr", "root", "red"), ("esophag", "root", "esophagus (food pipe)"),
    ("fibr", "root", "fiber or scar-like tissue"), ("gastr", "root", "stomach"),
    ("gingiv", "root", "gums"), ("glomerul", "root", "kidney filter"), ("gloss", "root", "tongue"),
    ("gluc", "root", "sugar"), ("glyc", "root", "sugar"), ("gynec", "root", "woman"),
    ("hem", "root", "blood"), ("hemat", "root", "blood"), ("hepat", "root", "liver"),
    ("hist", "root", "tissue"), ("hydr", "root", "water"), ("hyster", "root", "uterus"),
    ("immun", "root", "immune system"), ("laryng", "root", "voice box"), ("leuk", "root", "white"),
    ("lip", "root", "fat"), ("lith", "root", "stone"), ("lymph", "root", "lymph"),
    ("mamm", "root", "breast"), ("mast", "root", "breast"), ("melan", "root", "black or dark"),
    ("mening", "root", "membranes around the brain and spinal cord"), ("myel", "root", "bone marrow or spinal cord"),
    ("myo", "root", "muscle"), ("nas", "root", "nose"), ("necr", "root", "death"),
    ("nephr", "root", "kidney"), ("neur", "root", "nerve"), ("ocul", "root", "eye"),
    ("onc", "root", "tumor"), ("ophthalm", "root", "eye"), ("orbit", "root", "eye socket"),
    ("ox", "root", "oxygen"), ("oste", "root", "bone"), ("ot", "root", "ear"), ("pancreat", "root", "pancreas"),
    ("path", "root", "disease"), ("peritone", "root", "lining of the belly"), ("pharyng", "root", "throat"),
    ("phleb", "root", "vein"), ("pleur", "root", "lining around the lungs"), ("pneum", "root", "lung or air"),
    ("pneumon", "root", "lung"), ("proct", "root", "rectum and anus"), ("prostat", "root", "prostate"),
    ("psych", "root", "mind"), ("pulmon", "root", "lung"), ("pyel", "root", "kidney pelvis"),
    ("rect", "root", "rectum"), ("ren", "root", "kidney"), ("rhin", "root", "nose"),
    ("sarc", "root", "flesh or muscle"), ("scler", "root", "hard"), ("splen", "root", "spleen"),
    ("staphyl", "root", "clusters of bacteria"), ("stomat", "root", "mouth"), ("strept", "root", "twisted chain"),
    ("thorac", "root", "chest"), ("thromb", "root", "blood clot"), ("thyr", "root", "thyroid"),
    ("tonsill", "root", "tonsil"), ("trache", "root", "windpipe"), ("ureter", "root", "tube from kidney to bladder"),
    ("urethr", "root", "tube from bladder to outside"), ("uter", "root", "uterus"), ("vas", "root", "vessel"),
    ("ven", "root", "vein"), ("ventricul", "root", "ventricle (heart chamber)"), ("vertebr", "root", "spine bone"),
    ("vesic", "root", "bladder or blister"), ("viscer", "root", "internal organs"),

    ("itis", "suffix", "inflammation"), ("osis", "suffix", "abnormal condition"),
    ("emia", "suffix", "condition of the blood"), ("aemia", "suffix", "condition of the blood"),
    ("pathy", "suffix", "disease"), ("ectomy", "suffix", "surgical removal"),
    ("ostomy", "suffix", "creating an opening"), ("otomy", "suffix", "cutting into"),
    ("plasty", "suffix", "surgical repair"), ("scopy", "suffix", "looking inside with an instrument"),
    ("algia", "suffix", "pain"), ("dynia", "suffix", "pain"), ("penia", "suffix", "too few"),
    ("megaly", "suffix", "enlargement"), ("plegia", "suffix", "paralysis"),
    ("rrhea", "suffix", "flow or discharge"), ("rrhage", "suffix", "heavy bleeding"),
    ("uria", "suffix", "urine condition"), ("oma", "suffix", "tumor or mass"),
    ("gram", "suffix", "a record or image"), ("graphy", "suffix", "process of recording or imaging"),
    ("logy", "suffix", "study of"), ("lysis", "suffix", "breakdown"), ("sclerosis", "suffix", "hardening"),
    ("stasis", "suffix", "stopping or control"), ("trophy", "suffix", "growth"),
    ("spasm", "suffix", "sudden tightening"), ("phagia", "suffix", "swallowing"),
    ("phasia", "suffix", "speech"), ("pnea", "suffix", "breathing"), ("ptosis", "suffix", "drooping"),
    ("centesis", "suffix", "puncture to remove fluid"), ("pexy", "suffix", "fixing in place"),
    ("genic", "suffix", "caused by or producing"), ("emesis", "suffix", "vomiting"),
    ("iasis", "suffix", "condition"), ("ia", "suffix", "condition"),
    ("eal", "suffix", "relating to"), ("al", "suffix", "relating to"), ("ic", "suffix", "relating to"),
    ("ac", "suffix", "relating to"), ("ar", "suffix", "relating to"), ("ary", "suffix", "relating to"),
    ("ous", "suffix", "relating to"),
]

PARTS = {}
for _text, _kind, _meaning in PARTS_LIST:
    if _text in PARTS:
        raise ValueError("Duplicate word part: " + _text)
    PARTS[_text] = (_kind, _meaning)

_MAX_LEN = max(len(p) for p in PARTS)
_CONNECTORS = "oi"


_GENERIC = {"ac", "al", "ar", "ary", "ic", "ous", "eal"}


def segment(word, strict=False):
    word = re.sub(r"[^a-z]", "", word.lower())
    if len(word) < 6:
        return None

    @lru_cache(maxsize=None)
    def best(i, after_part):
        if i == len(word):
            return ()
        result = None
        for j in range(min(len(word), i + _MAX_LEN), i, -1):
            piece = word[i:j]
            if piece in PARTS:
                rest = best(j, True)
                if rest is not None:
                    candidate = (piece,) + rest
                    if result is None or len(candidate) < len(result):
                        result = candidate
        if after_part and word[i] in _CONNECTORS:
            rest = best(i + 1, False)
            if rest and (result is None or len(rest) < len(result)):
                result = rest
        return result

    pieces = best(0, False)
    if not pieces or len(pieces) < 2:
        return None
    if strict:
        meaningful = [p for p in pieces if p not in _GENERIC]
        if len(meaningful) < 2 or max(len(p) for p in pieces) < 4:
            return None
    return [{"text": p, "kind": PARTS[p][0], "meaning": PARTS[p][1]} for p in pieces]


def parts_table():
    table = {"prefix": [], "root": [], "suffix": []}
    for text, kind, meaning in PARTS_LIST:
        table[kind].append({"text": text, "meaning": meaning})
    for kind in table:
        table[kind].sort(key=lambda p: p["text"])
    return table


def decode(word):
    clean = re.sub(r"[^a-z]", "", (word or "").lower())
    if len(clean) < 6:
        return {"error": "Try a word with at least 6 letters."}
    parts = segment(clean)
    if not parts:
        return {"word": clean, "parts": [],
                "message": "I can't split that one into known word parts. Try the lookup on the Translate page."}
    return {"word": clean, "parts": parts}
