const categoryBody = document.getElementById("category-body");
const itemsBody = document.getElementById("items-body");
const runMeta = document.getElementById("run-meta");
const mockBanner = document.getElementById("mock-banner");
const chips = [...document.querySelectorAll(".chip")];

let payload = null;
let activeFilter = "all";

function pct(n) {
  return `${(Number(n) * 100).toFixed(1)}%`;
}

function renderCategory() {
  if (!payload) return;
  const entries = Object.entries(payload.by_category || {});
  const filtered =
    activeFilter === "all" ? entries : entries.filter(([k]) => k === activeFilter);
  if (!filtered.length) {
    categoryBody.innerHTML = `<tr><td colspan="4">No rows for this filter.</td></tr>`;
    return;
  }
  categoryBody.innerHTML = filtered
    .map(
      ([name, stats]) =>
        `<tr>
          <td>${name}</td>
          <td>${stats.passed}</td>
          <td>${stats.total}</td>
          <td>${pct(stats.accuracy)}</td>
        </tr>`
    )
    .join("");
}

function renderItems() {
  if (!payload) return;
  const rows = (payload.items || []).filter(
    (row) => activeFilter === "all" || row.category === activeFilter
  );
  itemsBody.innerHTML = rows
    .map(
      (row) =>
        `<tr>
          <td><code>${row.id}</code></td>
          <td>${row.category}</td>
          <td>${row.scoring}</td>
          <td class="${row.passed ? "pass-yes" : "pass-no"}">${row.passed ? "yes" : "no"}</td>
        </tr>`
    )
    .join("");
}

function renderMeta() {
  runMeta.innerHTML = `
    <span>provider: ${payload.provider}</span>
    <span>model: ${payload.model}</span>
    <span>overall: ${payload.passed}/${payload.total} (${pct(payload.accuracy)})</span>
    <span>generated: ${payload.generated_at}</span>
  `;
  mockBanner.hidden = !payload.is_mock;
}

function setFilter(next) {
  activeFilter = next;
  chips.forEach((chip) => {
    chip.classList.toggle("is-active", chip.dataset.filter === next);
  });
  renderCategory();
  renderItems();
}

chips.forEach((chip) => {
  chip.addEventListener("click", () => setFilter(chip.dataset.filter));
});

document.querySelectorAll("[data-copy]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const text = btn.getAttribute("data-copy") || "";
    try {
      await navigator.clipboard.writeText(text.replace(/&#10;/g, "\n"));
      btn.textContent = "Copied";
      setTimeout(() => {
        btn.textContent = "Copy";
      }, 1200);
    } catch {
      btn.textContent = "Failed";
    }
  });
});

try {
  const res = await fetch("results.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  payload = await res.json();
  renderMeta();
  renderCategory();
  renderItems();
} catch (err) {
  categoryBody.innerHTML = `<tr><td colspan="4">Could not load results.json (${err.message}).</td></tr>`;
}
