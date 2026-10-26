const $ = id => document.getElementById(id);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function decode() {
  const word = $("wordInput").value.trim();
  const box = $("decodeOut");
  box.textContent = "";
  if (!word) return;

  try {
    const response = await fetch("/api/decode?word=" + encodeURIComponent(word));
    const data = await response.json();
    const wrap = el("div", "decode-result");

    if (data.error) {
      wrap.appendChild(el("p", "message", data.error));
      box.appendChild(wrap);
      return;
    }

    wrap.appendChild(el("h3", "", data.word));

    if (!data.parts || data.parts.length === 0) {
      wrap.appendChild(el("p", "muted", data.message));
      box.appendChild(wrap);
      return;
    }

    const row = el("div", "decode-parts");
    data.parts.forEach(p => {
      const label = p.kind === "prefix" ? p.text + "-" : p.kind === "suffix" ? "-" + p.text : p.text;
      const piece = el("div", "part-box " + p.kind);
      piece.appendChild(el("strong", "", label));
      piece.appendChild(el("span", "", p.meaning));
      row.appendChild(piece);
    });
    wrap.appendChild(row);
    wrap.appendChild(el("p", "fine", "This is a best guess from common word parts. Real meanings can be a little different, so check important words with the lookup."));
    box.appendChild(wrap);
  } catch (err) {
    box.appendChild(el("p", "message", "Something went wrong. Try again."));
  }
}

$("decodeBtn").addEventListener("click", decode);
$("wordInput").addEventListener("keydown", e => { if (e.key === "Enter") decode(); });

$("partFilter").addEventListener("input", () => {
  const q = $("partFilter").value.trim().toLowerCase();
  document.querySelectorAll(".parts-table tbody tr").forEach(row => {
    row.hidden = q !== "" && !row.dataset.search.toLowerCase().includes(q);
  });
});
