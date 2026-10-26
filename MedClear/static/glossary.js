const $ = id => document.getElementById(id);
const PAGE = 40;

let offset = 0;
let total = 0;
let timer = null;
let requestId = 0;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function addEntries(items) {
  const box = $("entries");
  items.forEach(m => {
    const entry = el("div", "entry");
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

async function load(reset) {
  if (reset) {
    offset = 0;
    $("entries").textContent = "";
  }
  const mine = ++requestId;
  const params = new URLSearchParams({
    q: $("q").value,
    category: $("cat").value,
    offset: String(offset)
  });

  try {
    const response = await fetch("/api/glossary?" + params.toString());
    const data = await response.json();
    if (mine !== requestId) return;

    total = data.total;
    addEntries(data.items);
    offset += data.items.length;

    if (total === 0) {
      $("count").textContent = "No matches. Try a different word.";
    } else {
      $("count").textContent = "Showing " + offset + " of " + total + (total === 1 ? " term" : " terms");
    }
    $("moreBtn").hidden = offset >= total;
  } catch (err) {
    $("count").textContent = "Couldn't load the glossary. Refresh and try again.";
  }
}

$("q").addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(() => load(true), 200);
});
$("cat").addEventListener("change", () => load(true));
$("moreBtn").addEventListener("click", () => load(false));

load(true);
