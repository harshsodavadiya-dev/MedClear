(function () {
  var button = document.getElementById("sizeBtn");
  if (!button) return;

  function apply(large) {
    document.body.classList.toggle("large", large);
    button.setAttribute("aria-pressed", String(large));
    button.textContent = large ? "Normal text" : "Larger text";
  }

  var saved = false;
  try {
    saved = window.localStorage.getItem("medclear-large") === "1";
  } catch (err) {
    saved = false;
  }
  apply(saved);

  button.addEventListener("click", function () {
    var large = !document.body.classList.contains("large");
    apply(large);
    try {
      window.localStorage.setItem("medclear-large", large ? "1" : "0");
    } catch (err) {
      return;
    }
  });
})();
