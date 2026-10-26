const EXAMPLES = [
  "Patient presents with tachycardia and bilateral lower extremity edema. Denies chest pain. BP 148/92, HR 112. History of hypertension and hyperlipidemia. Recent tonsillitis resolved. No evidence of pneumonia. Follow-up in 2 weeks to rule out atrial fibrillation. Started on a diuretic PRN.",
  "CBC: WBC 12.8, hemoglobin 10.9, platelets 142. BMP: glucose 118 mg/dL, sodium 138, potassium 5.3, creatinine 1.1. HbA1c 6.1%. LDL 132 mg/dL, triglycerides 160. Leukocytosis noted with mild anemia. Findings otherwise unremarkable.",
  "Take one tablet BID with food. Use acetaminophen PRN for pain. This anticoagulant can cause hemorrhage, so tell your doctor before any surgery. Contraindicated with some antibiotics. Do not discontinue without talking to your doctor. Monitor for vertigo and syncope.",
  "Discharge diagnosis: acute pharyngitis with mild dehydration. Patient was afebrile at discharge. Prescribed an antibiotic BID for 7 days. Return to the ER for dyspnea, persistent emesis, or syncope. Follow-up with primary care in 3 to 5 days."
];

const $ = id => document.getElementById(id);
const inputEl = $("inputText");
const outputEl = $("output");
const messageEl = $("message");

let current = null;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function slug(term) {
  return "entry-" + term.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

function jumpToEntry(term) {
  const entry = $(slug(term));
  if (!entry) return;
  entry.scrollIntoView({ behavior: "smooth", block: "center" });
  entry.classList.remove("flash");
  void entry.offsetWidth;
  entry.classList.add("flash");
}

async function copyText(button, text) {
  const original = button.textContent;
  try {
    await navigator.clipboard.writeText(text);
    button.textContent = "Copied!";
  } catch (err) {
    button.textContent = "Copy failed";
  }
  setTimeout(() => { button.textContent = original; }, 1500);
}

function renderStats(stats) {
  const box = $("stats");
  box.textContent = "";

  const add = (num, label) => {
    const stat = el("div", "stat");
    stat.appendChild(el("div", "stat-num", num));
    stat.appendChild(el("div", "stat-label", label));
    box.appendChild(stat);
  };

  add(String(stats.terms), stats.terms === 1 ? "term explained" : "terms explained");
  if (stats.labs > 0) add(String(stats.labs), stats.labs === 1 ? "lab number checked" : "lab numbers checked");
  if (stats.grade_before !== null && stats.grade_after !== null) {
    const fmt = g => (g >= 18 ? "18+" : String(g));
    add("Grade " + fmt(stats.grade_before) + " \u2192 " + fmt(stats.grade_after), "reading level, before and after (estimate)");
  }
}

function renderLabs(labs) {
  const box = $("labs");
  box.textContent = "";
  $("labsCard").hidden = labs.length === 0;

  labs.forEach(lab => {
    const card = el("div", "lab");
    const top = el("div", "lab-top");
    const left = el("div");
    left.appendChild(el("span", "lab-name", lab.label + ": "));
    left.appendChild(el("span", "lab-value", lab.value_text));
    top.appendChild(left);
    top.appendChild(el("span", "badge " + lab.status, lab.status_text));
    card.appendChild(top);
    if (lab.range_text) card.appendChild(el("div", "lab-note", lab.range_text));
    if (lab.note) card.appendChild(el("div", "lab-note", lab.note));
    box.appendChild(card);
  });
}

function renderAnnotated(segments) {
  const box = $("annotated");
  box.textContent = "";
  segments.forEach(seg => {
    if (seg.term) {
      const span = el("span", "term", seg.text);
      span.tabIndex = 0;
      span.addEventListener("click", () => jumpToEntry(seg.term));
      span.addEventListener("keydown", e => { if (e.key === "Enter") jumpToEntry(seg.term); });
      box.appendChild(span);
    } else {
      box.appendChild(document.createTextNode(seg.text));
    }
  });
}

function renderTerms(matches) {
  const box = $("results");
  box.textContent = "";
  $("termsCard").hidden = matches.length === 0;
  $("termsTitle").textContent = matches.length + (matches.length === 1 ? " term explained" : " terms explained");

  matches.forEach(m => {
    const entry = el("div", "entry");
    entry.id = slug(m.term);
    entry.dataset.cat = m.category;

    const top = el("div", "entry-top");
    top.appendChild(el("span", "entry-term", m.term));
    top.appendChild(el("span", "tag", m.category));
    entry.appendChild(top);

    entry.appendChild(el("div", "", m.plain));
    if (m.analogy) entry.appendChild(el("div", "analogy", m.analogy));
    if (m.source === "MedlinePlus") {
      const credit = el("div", "source-credit", "Source: MedlinePlus.gov, National Library of Medicine. ");
      if (m.url) {
        const link = el("a", "", "Read more");
        link.href = m.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        credit.appendChild(link);
      }
      entry.appendChild(credit);
    }
    box.appendChild(entry);
  });
}

function partsText(parts) {
  return parts.map(p => {
    const label = p.kind === "prefix" ? p.text + "-" : p.kind === "suffix" ? "-" + p.text : p.text;
    return label + " (" + p.meaning + ")";
  }).join(" + ");
}

function renderUnknown(items) {
  const box = $("unknown");
  box.textContent = "";
  $("unknownCard").hidden = items.length === 0;
  items.forEach(item => {
    const row = el("div", "unknown-item");
    row.appendChild(el("div", "unknown-word", item.word));
    if (item.parts && item.parts.length) {
      row.appendChild(el("div", "unknown-parts", "Word parts: " + partsText(item.parts)));
    }
    const btn = el("button", "chip", "Look up \u201c" + item.word + "\u201d");
    btn.addEventListener("click", () => {
      $("lookupInput").value = item.word;
      runLookup();
      $("lookupCard").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    row.appendChild(btn);
    box.appendChild(row);
  });
}

function renderQuestions(questions) {
  const list = $("questions");
  list.textContent = "";
  questions.forEach(q => list.appendChild(el("li", "", q)));
}

async function explain() {
  const text = inputEl.value;
  messageEl.textContent = "";
  outputEl.hidden = true;

  if (!text.trim()) {
    messageEl.textContent = "Paste or type something first.";
    return;
  }

  messageEl.textContent = "Reading it...";

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text })
    });
    if (!response.ok) throw new Error("Server error");
    const data = await response.json();

    messageEl.textContent = data.message || "";
    if (!data.stats) return;

    current = data;
    renderStats(data.stats);
    $("plainText").textContent = data.plain_text;
    renderLabs(data.labs);
    renderAnnotated(data.segments);
    renderTerms(data.matches);
    renderUnknown(data.unrecognized);
    renderQuestions(data.questions);

    if (data.matches.length === 0 && data.labs.length === 0 && data.unrecognized.length === 0) return;
    outputEl.hidden = false;
    outputEl.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    messageEl.textContent = "Something went wrong. Try again.";
  }
}

async function runLookup() {
  const term = $("lookupInput").value.trim();
  const box = $("lookupResults");
  box.textContent = "";
  if (!term) return;

  box.appendChild(el("p", "muted", "Searching MedlinePlus..."));

  try {
    const response = await fetch("/lookup?term=" + encodeURIComponent(term));
    const data = await response.json();
    box.textContent = "";

    if (data.error) { box.appendChild(el("p", "message", data.error)); return; }
    if (!data.results || data.results.length === 0) {
      box.appendChild(el("p", "muted", data.message || "No results."));
      return;
    }

    data.results.forEach(r => {
      const item = el("div", "lookup-item");
      item.appendChild(el("div", "lookup-title", r.title));
      item.appendChild(el("div", "", r.summary));
      if (r.url) {
        const link = el("a", "", "Read more on MedlinePlus");
        link.href = r.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        item.appendChild(link);
      }
      box.appendChild(item);
    });
    box.appendChild(el("p", "credit", "Source: " + data.source));
  } catch (err) {
    box.textContent = "";
    box.appendChild(el("p", "message", "Something went wrong. Try again."));
  }
}

$("explainBtn").addEventListener("click", explain);
$("clearBtn").addEventListener("click", () => {
  inputEl.value = "";
  outputEl.hidden = true;
  messageEl.textContent = "";
  current = null;
});
inputEl.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") explain();
});

document.querySelectorAll(".example-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    inputEl.value = EXAMPLES[Number(btn.dataset.example)];
    explain();
  });
});

$("copyPlainBtn").addEventListener("click", () => {
  if (current) copyText($("copyPlainBtn"), current.plain_text);
});
$("copyTermsBtn").addEventListener("click", () => {
  if (current) copyText($("copyTermsBtn"), current.matches.map(m => m.term + ": " + m.plain).join("\n"));
});
$("printBtn").addEventListener("click", () => window.print());

$("lookupBtn").addEventListener("click", runLookup);
$("lookupInput").addEventListener("keydown", e => { if (e.key === "Enter") runLookup(); });

document.querySelectorAll(".jump .chip").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = $(btn.dataset.target);
    if (target && !target.hidden) target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});
