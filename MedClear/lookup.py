import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE_URL = "https://wsearch.nlm.nih.gov/ws/query"
TOOL_NAME = "medclear"
CONTACT_EMAIL = ""
SOURCE_CREDIT = "MedlinePlus.gov, National Library of Medicine"

_cache = {}


def _clean(text):
    text = re.sub(r"</(?:p|li|ul|ol|div|h\d)>", " ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_results(xml_text, max_results=3):
    root = ET.fromstring(xml_text)
    results = []
    for doc in root.iter("document"):
        fields = {}
        for content in doc.findall("content"):
            fields[content.get("name")] = "".join(content.itertext())

        title = _clean(fields.get("title", ""))
        summary = _clean(fields.get("FullSummary") or fields.get("snippet") or "")
        url = doc.get("url", "")
        if not title or not summary:
            continue
        if len(summary) > 500:
            summary = summary[:497].rsplit(" ", 1)[0] + "..."
        if not url.startswith("https://medlineplus.gov/"):
            url = ""
        results.append({"title": title, "summary": summary, "url": url})
        if len(results) >= max_results:
            break
    return results


def _fetch(term):
    params = {"db": "healthTopics", "term": term, "retmax": "3", "rettype": "all", "tool": TOOL_NAME}
    if CONTACT_EMAIL:
        params["email"] = CONTACT_EMAIL
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "MedClear/1.0 (student project)"})
    with urllib.request.urlopen(request, timeout=8) as response:
        return response.read().decode("utf-8", errors="replace")


def lookup_term(term):
    term = (term or "").strip()
    if not term or len(term) > 60 or not re.fullmatch(r"[A-Za-z0-9 \-']+", term):
        return {"error": "Type a medical word or condition (letters and numbers only)."}

    key = term.lower()
    if key in _cache:
        return _cache[key]

    try:
        results = parse_results(_fetch(term))
    except Exception:
        return {"error": "Couldn't reach MedlinePlus right now. Try again in a minute."}

    if not results:
        return {"results": [], "source": SOURCE_CREDIT,
                "message": "MedlinePlus doesn't have a health topic that matches that word."}

    data = {"results": results, "source": SOURCE_CREDIT}
    _cache[key] = data
    return data
