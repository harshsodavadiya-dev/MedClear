import re


def count_syllables(word):
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    word = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", word)
    word = re.sub(r"^y", "", word)
    groups = re.findall(r"[aeiouy]{1,2}", word)
    return max(1, len(groups))


def reading_grade(text):
    words = re.findall(r"[A-Za-z']+", text)
    if len(words) < 8:
        return None

    pieces = [p for p in re.split(r"[.!?]+\s|\n+", text) if p.strip()]
    sentences = len(pieces)
    if sentences < 2:
        return None

    syllables = sum(count_syllables(w) for w in words)
    grade = 0.39 * (len(words) / sentences) + 11.8 * (syllables / len(words)) - 15.59
    return round(min(18.0, max(0.0, grade)), 1)
