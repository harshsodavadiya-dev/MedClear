import html
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

MEDICAL_ENDING = re.compile(
    r"(?:itis|osis|emia|aemia|pathy|ectomy|ostomy|otomy|plasty|scopy|algia|penia|megaly|plegia|rrhea|uria|oma|emesis)$",
    re.IGNORECASE)
ALLOWED_NAME = re.compile(r"[a-z0-9 '\-]+")


def clean(text):
    text = re.sub(r"</(?:p|li|ul|ol|div|h\d)>", " ", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def first_sentences(text, count=2, max_chars=320):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = " ".join(sentences[:count]).strip()
    if len(out) > max_chars:
        out = out[:max_chars - 3].rsplit(" ", 1)[0] + "..."
    return out


def keep_name(name):
    low = name.lower().strip()
    if not (5 <= len(low) <= 60) or not ALLOWED_NAME.fullmatch(low):
        return False
    return " " in low or bool(MEDICAL_ENDING.search(low))


def read_xml_bytes(path):
    import os
    if not os.path.exists(path):
        raise SystemExit(f"Can't find '{path}'. Upload the MedlinePlus file into this project folder "
                         "and check the spelling of the file name.")
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".xml")]
            if not names:
                raise SystemExit("No .xml file found inside that zip.")
            return z.read(names[0])
    with open(path, "rb") as f:
        return f.read()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python import_medlineplus.py <mplus_topics file (.zip or .xml)>")

    root = ET.fromstring(read_xml_bytes(sys.argv[1]))
    topics = list(root.iter("health-topic"))
    if not topics:
        raise SystemExit("No <health-topic> entries found. Is this the MedlinePlus Health Topic XML file? "
                         "Top-level tag was: " + root.tag)

    out = {}
    english = 0
    for topic in topics:
        if (topic.get("language") or "English").lower() != "english":
            continue
        english += 1

        title = (topic.get("title") or "").strip()
        url = topic.get("url") or ""
        summary_el = topic.find("full-summary")
        summary = clean("".join(summary_el.itertext())) if summary_el is not None else ""
        meaning = first_sentences(summary) or clean(topic.get("meta-desc") or "")
        if not title or not meaning or not url.startswith("https://medlineplus.gov/"):
            continue

        base = {"plain": meaning, "analogy": "", "category": "From MedlinePlus",
                "source": "MedlinePlus", "url": url}

        if keep_name(title) and title.lower() not in out:
            out[title.lower()] = dict(base)

        for syn_el in topic.findall("also-called"):
            syn = clean("".join(syn_el.itertext()))
            if keep_name(syn) and syn.lower() not in out:
                entry = dict(base)
                entry["swap"] = title.lower()
                out[syn.lower()] = entry

    with open("medlineplus_terms.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    print(f"Read {english} English topics. Wrote {len(out)} terms to medlineplus_terms.json")
    for key in list(out)[:3]:
        print(" example:", key, "->", out[key]["plain"][:80])


if __name__ == "__main__":
    main()
