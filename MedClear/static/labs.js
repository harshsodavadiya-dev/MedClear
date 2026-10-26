const $ = id => document.getElementById(id);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function syncInputs() {
  const select = $("labSelect");
  const isBp = select.value === "bp";
  const unit = select.options[select.selectedIndex].dataset.unit;
  $("value2Field").hidden = !isBp;
  $("labValueLabel").textContent = isBp ? "Top number" : "Your number (" + unit + ")";
  $("labOut").textContent = "";
}

async function check() {
  const box = $("labOut");
  box.textContent = "";

  const params = new URLSearchParams({
    lab: $("labSelect").value,
    value: $("labValue").value,
    value2: $("labValue2").value
  });

  try {
    const response = await fetch("/api/lab-check?" + params.toString());
    const data = await response.json();

    if (data.error) {
      box.appendChild(el("p", "message", data.error));
      return;
    }

    const card = el("div", "lab");
    const top = el("div", "lab-top");
    const left = el("div");
    left.appendChild(el("span", "lab-name", data.label + ": "));
    left.appendChild(el("span", "lab-value", data.value_text));
    top.appendChild(left);
    top.appendChild(el("span", "badge " + data.status, data.status_text));
    card.appendChild(top);
    if (data.range_text) card.appendChild(el("div", "lab-note", data.range_text));
    if (data.note) card.appendChild(el("div", "lab-note", data.note));
    box.appendChild(card);
  } catch (err) {
    box.appendChild(el("p", "message", "Something went wrong. Try again."));
  }
}

$("labSelect").addEventListener("change", syncInputs);
$("labCheckBtn").addEventListener("click", check);
["labValue", "labValue2"].forEach(id => {
  $(id).addEventListener("keydown", e => { if (e.key === "Enter") check(); });
});

syncInputs();
