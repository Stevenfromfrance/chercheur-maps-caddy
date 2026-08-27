function amazonUrl(item) {
  if (item.asin) return `https://www.amazon.fr/dp/${item.asin}`;
  return `https://www.amazon.fr/s?k=${encodeURIComponent(item.search)}`;
}

function amazonImg(item) {
  if (!item.asin) return "";
  return `https://images-eu.ssl-images-amazon.com/images/P/${item.asin}.01._SX300_.jpg`;
}

function needClass(needed) {
  if (needed === "yes") return "need-yes";
  if (needed === "no") return "need-no";
  return "need-optional";
}

function needLabel(needed) {
  if (needed === "yes") return "Needed: yes";
  if (needed === "no") return "Needed: no";
  if (needed === "later") return "Needed: later";
  return "Needed: optional";
}

function verdictLabel(verdict) {
  return { keep: "Keep", skip: "Skip", later: "Later", compare: "Compare" }[verdict] || verdict;
}

function cardHTML(item) {
  const url = amazonUrl(item);
  const image = amazonImg(item);
  const fallback = item._icon || "🛒";
  const thumb = image
    ? `<img src="${image}" alt="" onerror="this.style.display='none';this.nextElementSibling.style.display='grid'"><span class="thumb-fallback" style="display:none">${fallback}</span>`
    : `<span>${fallback}</span>`;

  return `
    <article class="card" data-verdict="${item.verdict}">
      <div class="thumb">${thumb}</div>
      <div class="meta">
        <div class="badges">
          <span class="badge ${item.verdict}">${verdictLabel(item.verdict)}</span>
          <span class="badge ${needClass(item.needed)}">${needLabel(item.needed)}</span>
        </div>
        <p class="brand">${item.brand}</p>
        <h3 class="title">${item.title}</h3>
        <p class="price">${item.price}</p>
        <p class="note">${item.note}</p>
        <p class="compare-line">${item.compare}</p>
        <a class="amazon-btn" href="${url}" target="_blank" rel="noopener">Open on Amazon.fr</a>
      </div>
    </article>
  `;
}

function renderPage(kind) {
  const root = document.getElementById("catalog");
  const missingBox = document.getElementById("missing");
  const groups = window.PRODUCTS[kind];
  const missing = window.MISSING[kind];

  root.innerHTML = groups.map((group) => {
    const cards = group.items.map((item) => {
      item._icon = group.icon;
      return cardHTML(item);
    }).join("");
    return `<section data-group>
      <h2 class="group-title">${group.icon} ${group.group}</h2>
      <div class="list">${cards}</div>
    </section>`;
  }).join("");

  missingBox.innerHTML = `
    <h2>Still missing from this Amazon list</h2>
    <ul>${missing.map((x) => `<li>${x}</li>`).join("")}</ul>
  `;

  const chips = document.querySelectorAll(".chip");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.classList.remove("is-on"));
      chip.classList.add("is-on");
      const filter = chip.dataset.filter;
      document.querySelectorAll(".card").forEach((card) => {
        card.style.display = filter === "all" || card.dataset.verdict === filter ? "" : "none";
      });
      document.querySelectorAll("[data-group]").forEach((section) => {
        const visible = [...section.querySelectorAll(".card")].some((c) => c.style.display !== "none");
        section.style.display = visible ? "" : "none";
      });
    });
  });
}

window.renderPage = renderPage;
