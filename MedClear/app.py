from flask import Flask, render_template, request, jsonify

from engine import analyze, glossary_categories, glossary_search, TERM_TOTAL, MAX_CHARS
from labs import BP_CATEGORIES, BP_GUIDE, check_lab, lab_guide
from lookup import lookup_term
from wordparts import decode, parts_table

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", max_chars=MAX_CHARS, term_count=TERM_TOTAL)


@app.route("/glossary")
def page_glossary():
    return render_template("glossary.html", categories=glossary_categories(), term_count=TERM_TOTAL)


@app.route("/labs")
def page_labs():
    return render_template("labs.html", labs=lab_guide(), bp=BP_GUIDE, bp_categories=BP_CATEGORIES)


@app.route("/words")
def page_words():
    return render_template("words.html", table=parts_table())


@app.route("/about")
def page_about():
    return render_template("about.html", term_count=TERM_TOTAL)


@app.route("/analyze", methods=["POST"])
def analyze_route():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")

    if not isinstance(text, str) or not text.strip():
        return jsonify({"message": "Paste or type something first."})

    if len(text) > MAX_CHARS:
        return jsonify({"message": f"That's too long. Keep it under {MAX_CHARS} characters."})

    result = analyze(text)
    result["message"] = ""

    nothing_found = not result["matches"] and not result["labs"] and not result["unrecognized"]
    if nothing_found:
        result["message"] = "Nothing medical showed up in that text. Try the lookup box at the bottom."
    return jsonify(result)


@app.route("/lookup")
def lookup_route():
    return jsonify(lookup_term(request.args.get("term", "")))


@app.route("/api/glossary")
def glossary_route():
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        offset = 0
    return jsonify(glossary_search(
        request.args.get("q", ""),
        request.args.get("category", ""),
        offset,
    ))


@app.route("/api/lab-check")
def lab_check_route():
    return jsonify(check_lab(
        request.args.get("lab", ""),
        request.args.get("value", ""),
        request.args.get("value2", ""),
    ))


@app.route("/api/decode")
def decode_route():
    return jsonify(decode(request.args.get("word", "")))


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
