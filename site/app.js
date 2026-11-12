(async function () {
  const runMeta = document.getElementById("run-meta");
  const filters = document.getElementById("filters");
  const categoryRows = document.getElementById("category-rows");
  const itemRows = document.getElementById("item-rows");

  let payload = null;
  let active = "all";

  function pct(value) {
    return `${(Number(value) * 100).toFixed(1)}%`;
  }

  function label(name) {
    return name.replace(/_/g, " ");
  }

  function cell(text, className) {
    const td = document.createElement("td");
    td.textContent = text;
    if (className) td.className = className;
    return td;
  }

  function messageRow(text) {
    const tr = document.createElement("tr");
    const td = cell(text);
    td.colSpan = 4;
    tr.appendChild(td);
    return tr;
  }

  function renderMeta() {
    runMeta.replaceChildren();
    const parts = [
      ["provider", payload.provider],
      ["model", payload.model],
      ["overall", `${payload.passed}/${payload.total} (${pct(payload.accuracy)})`],
      ["generated", payload.generated_at],
      ["mock", payload.is_mock ? "yes" : "no"],
    ];
    parts.forEach(([name, value]) => {
      const span = document.createElement("span");
      const strong = document.createElement("strong");
      strong.textContent = value;
      span.append(`${name}: `, strong);
      runMeta.appendChild(span);
    });
  }

  function renderTables() {
    categoryRows.replaceChildren();
    const entries = Object.entries(payload.by_category || {}).filter(
      ([name]) => active === "all" || name === active,
    );
    if (!entries.length) categoryRows.appendChild(messageRow("No rows for this filter."));
    entries.forEach(([name, stats]) => {
      const tr = document.createElement("tr");
      tr.append(
        cell(label(name)),
        cell(String(stats.passed), "num"),
        cell(String(stats.total), "num"),
        cell(pct(stats.accuracy), "num"),
      );
      categoryRows.appendChild(tr);
    });

    itemRows.replaceChildren();
    (payload.items || [])
      .filter((item) => active === "all" || item.category === active)
      .forEach((item) => {
        const tr = document.createElement("tr");
        const id = document.createElement("td");
        const code = document.createElement("code");
        code.textContent = item.id;
        id.appendChild(code);
        tr.append(
          id,
          cell(label(item.category)),
          cell(item.scoring),
          cell(item.passed ? "pass" : "fail", item.passed ? "pass" : "fail"),
        );
        itemRows.appendChild(tr);
      });
  }

  function setFilter(next) {
    active = next;
    filters.querySelectorAll("button").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.filter === next));
    });
    renderTables();
  }

  function buildFilters() {
    ["all", ...Object.keys(payload.by_category || {})].forEach((name) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "chip";
      button.dataset.filter = name;
      button.textContent = name === "all" ? "All" : label(name);
      button.setAttribute("aria-pressed", String(name === active));
      button.addEventListener("click", () => setFilter(name));
      filters.appendChild(button);
    });
  }

  try {
    const response = await fetch("results.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    payload = await response.json();
  } catch (error) {
    categoryRows.replaceChildren(
      messageRow(`Could not load results.json (${error.message}). Reload to try again.`),
    );
    return;
  }

  document.getElementById("fact-items").textContent = String(payload.total);
  document.getElementById("fact-categories").textContent = String(
    Object.keys(payload.by_category || {}).length,
  );
  document.querySelectorAll("[data-count]").forEach((td) => {
    td.textContent = String(
      (payload.items || []).filter((item) => item.scoring === td.dataset.count).length,
    );
  });

  renderMeta();
  buildFilters();
  renderTables();
})();
