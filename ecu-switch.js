/**
 * Multi-ECU switch for chercheur-maps.
 * PCR 2.1 = atelier embarqué (index.html).
 * MEVD 17.2.5 = catalogue maps depuis data/*.json (import .kp).
 */
(function () {
  const LS_ECU = "chercheur-ecu";
  const PAGE_IDS_PCR = [
    "home",
    "composer",
    "maps-prio",
    "all-maps",
    "valeurs",
    "view2d",
    "view3d",
    "hexdump",
    "dump2d",
    "dtc-atlas",
    "guide",
    "vcds",
    "log-compare",
    "downloads",
  ];
  const PAGE_IDS_MEVD = ["ecu-maps", "guide-ecu"];

  let ecus = [];
  let currentId = null;
  let catalog = null;

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function toast(msg) {
    const el = $("#toast");
    if (!el) return;
    el.textContent = msg;
    el.style.display = "block";
    setTimeout(() => {
      el.style.display = "none";
    }, 1600);
  }

  function copyAddr(addr) {
    if (!addr) return;
    navigator.clipboard.writeText(addr).then(() => {
      toast("Copié : " + addr + "  →  WinOLS Ctrl+G");
    });
  }

  const FALLBACK = {
    default: "pcr21-9979",
    ecus: [
      {
        id: "pcr21-9979",
        label: "PCR 2.1",
        short: "PCR 2.1",
        vehicle: "VW Caddy CAYE",
        soft: "9979",
        mode: "atelier",
        subtitle: "ORI · ACE Tuning · V2 · V3 ITALIE · PCR2.1 · SW 9979",
        maps_url: null,
        note: "Atelier complet ORI / ACE / V2 / V3 ITALIE + VCDS.",
      },
      {
        id: "mevd1725-531049",
        label: "MEVD 17.2.5",
        short: "MEVD 17.2.5",
        vehicle: "BMW 1 Series",
        soft: "531049",
        mode: "catalog",
        subtitle: "BMW 1 Series · Bosch MEVD17.2.5 · SW 531049",
        maps_url: "data/mevd1725-531049/maps.json",
        note: "Mappack WinOLS importé. Catalogue maps (pas encore de compare Stage).",
      },
    ],
  };

  async function loadEcus() {
    try {
      const res = await fetch("data/ecus.json", { cache: "no-store" });
      if (!res.ok) throw new Error("ecus.json " + res.status);
      const data = await res.json();
      ecus = data.ecus || [];
      return data;
    } catch (err) {
      console.warn("ecus.json fallback", err);
      ecus = FALLBACK.ecus;
      return FALLBACK;
    }
  }

  function renderSwitcher() {
    const host = $("#ecu-switch");
    if (!host) return;
    host.innerHTML = "";
    ecus.forEach((ecu) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ecu-btn" + (ecu.id === currentId ? " on" : "");
      btn.dataset.ecu = ecu.id;
      btn.title = ecu.note || ecu.subtitle || "";
      btn.innerHTML =
        '<span class="ecu-btn-label">' +
        ecu.short +
        '</span><span class="ecu-btn-meta">' +
        (ecu.vehicle || "") +
        " · " +
        (ecu.soft || "") +
        "</span>";
      btn.addEventListener("click", () => setEcu(ecu.id, { persist: true, navigate: true }));
      host.appendChild(btn);
    });
  }

  function setSubtitle(ecu) {
    const sub = $("#ecu-subtitle");
    if (sub) {
      sub.innerHTML =
        (ecu.subtitle || "") +
        (ecu.mode === "atelier"
          ? ' · clic adresse = Ctrl+G · <kbd>/</kbd> chercher'
          : ' · clic adresse = Ctrl+G · <kbd>/</kbd> chercher');
    }
    const title = document.querySelector(".brand-text h1");
    if (title) {
      title.textContent =
        ecu.mode === "atelier"
          ? "Chercheur maps · ORI / ACE Tuning / V2 / V3 ITALIE"
          : "Chercheur maps · " + (ecu.short || ecu.label);
    }
    document.title =
      "SAVAGESEAR · " +
      (ecu.short || ecu.id) +
      (ecu.soft ? " " + ecu.soft : "") +
      " — Chercheur maps";
  }

  function setNavVisibility(ecu) {
    const isAtelier = ecu.mode === "atelier";
    document.body.dataset.ecuMode = ecu.mode;
    document.body.dataset.ecuId = ecu.id;

    document.querySelectorAll(".nav-jump a[data-nav]").forEach((a) => {
      const nav = a.getAttribute("data-nav");
      if (nav === "ecu-maps" || nav === "guide-ecu") {
        a.hidden = isAtelier;
      } else if (PAGE_IDS_PCR.includes(nav)) {
        a.hidden = !isAtelier;
      }
    });

    document.querySelectorAll(".nav-group").forEach((g) => {
      g.hidden = !isAtelier;
    });

    const pair = $(".pair-bar");
    const stats = $(".stats");
    const chips = $("#quick-chips");
    if (pair) pair.hidden = !isAtelier;
    if (stats) stats.hidden = !isAtelier;
    if (chips) chips.hidden = !isAtelier;
  }

  async function loadCatalog(ecu) {
    if (!ecu.maps_url) {
      catalog = null;
      return null;
    }
    const res = await fetch(ecu.maps_url, { cache: "no-store" });
    if (!res.ok) throw new Error(ecu.maps_url + " " + res.status);
    catalog = await res.json();
    return catalog;
  }

  function folderOptions(maps) {
    const set = new Set();
    maps.forEach((m) => {
      if (m.folder) set.add(m.folder);
    });
    return [...set].sort();
  }

  function renderCatalog() {
    const meta = $("#ecu-maps-meta");
    const tbody = $("#ecu-rows");
    const folderSel = $("#ecu-folder");
    const count = $("#ecu-count");
    if (!tbody || !catalog) return;

    const maps = catalog.maps || [];
    if (meta) {
      meta.innerHTML =
        "<b>" +
        (catalog.ecu || "") +
        "</b> · soft <b>" +
        (catalog.soft || "") +
        "</b> · " +
        (catalog.vehicle || "") +
        " · " +
        (catalog.map_count || maps.length) +
        " maps" +
        (catalog.maps_with_addr != null
          ? " · " + catalog.maps_with_addr + " avec adresse"
          : "") +
        (catalog.note ? "<br><span class='muted'>" + catalog.note + "</span>" : "");
    }

    if (folderSel) {
      const cur = folderSel.value;
      folderSel.innerHTML = '<option value="">Toutes familles</option>';
      folderOptions(maps).forEach((f) => {
        const opt = document.createElement("option");
        opt.value = f;
        opt.textContent = f;
        folderSel.appendChild(opt);
      });
      if ([...folderSel.options].some((o) => o.value === cur)) folderSel.value = cur;
    }

    tbody.innerHTML = "";
    maps.forEach((m) => {
      const tr = document.createElement("tr");
      const text = [m.id, m.name, m.folder, m.addr, m.end].filter(Boolean).join(" ").toLowerCase();
      tr.dataset.text = text;
      tr.dataset.folder = m.folder || "";
      const addrCell = m.addr
        ? '<button type="button" class="addr" data-addr="' + m.addr + '">' + m.addr + "</button>"
        : "<span class='muted'>—</span>";
      const endCell = m.end || "—";
      const dims =
        m.cols && m.rows ? m.cols + "×" + m.rows : m.cols || m.rows ? String(m.cols || m.rows) : "—";
      tr.innerHTML =
        "<td>" +
        addrCell +
        "</td><td class='mono'>" +
        endCell +
        "</td><td>" +
        (m.id || "") +
        "</td><td>" +
        (m.name || "") +
        "</td><td>" +
        (m.folder || "") +
        "</td><td>" +
        dims +
        "</td><td><span class='badge'>KP</span></td>";
      tbody.appendChild(tr);
    });

    filterCatalog();
  }

  function filterCatalog() {
    const q = $("#ecu-q");
    const folder = $("#ecu-folder");
    const count = $("#ecu-count");
    const rows = [...document.querySelectorAll("#ecu-rows tr")];
    const text = (q?.value || "").trim().toLowerCase();
    const fam = folder?.value || "";
    let n = 0;
    rows.forEach((tr) => {
      const okText = !text || (tr.dataset.text || "").includes(text);
      const okFam = !fam || tr.dataset.folder === fam;
      const show = okText && okFam;
      tr.style.display = show ? "" : "none";
      if (show) n++;
    });
    if (count) {
      count.textContent =
        (!text && !fam ? rows.length + " maps" : n + " / " + rows.length + " maps") +
        (catalog?.maps_with_addr != null ? " · " + catalog.maps_with_addr + " addr" : "");
    }
  }

  function currentModePages() {
    const ecu = ecus.find((e) => e.id === currentId);
    return ecu && ecu.mode === "catalog" ? PAGE_IDS_MEVD : PAGE_IDS_PCR;
  }

  function showEcuPage(id) {
    const pages = currentModePages();
    if (!pages.includes(id)) id = pages[0];
    if (typeof window.showPage === "function") window.showPage(id);
  }

  async function setEcu(id, opts) {
    opts = opts || {};
    const ecu = ecus.find((e) => e.id === id) || ecus[0];
    if (!ecu) return;
    currentId = ecu.id;
    if (opts.persist) {
      try {
        localStorage.setItem(LS_ECU, currentId);
      } catch (_) {}
    }
    renderSwitcher();
    setSubtitle(ecu);
    setNavVisibility(ecu);

    if (ecu.mode === "catalog") {
      try {
        await loadCatalog(ecu);
        renderCatalog();
      } catch (err) {
        const meta = $("#ecu-maps-meta");
        if (meta) meta.textContent = "Erreur chargement catalogue : " + err.message;
      }
      if (opts.navigate !== false) showEcuPage("ecu-maps");
    } else {
      catalog = null;
      if (opts.navigate !== false) {
        if (typeof window.showPage === "function") window.showPage("home");
      }
    }
  }

  function wireCatalogUi() {
    $("#ecu-q")?.addEventListener("input", filterCatalog);
    $("#ecu-folder")?.addEventListener("change", filterCatalog);
    document.addEventListener("click", (e) => {
      const b = e.target.closest("#ecu-rows button.addr");
      if (b) copyAddr(b.dataset.addr);
    });
  }

  async function boot() {
    try {
      const data = await loadEcus();
      let want = null;
      try {
        want = localStorage.getItem(LS_ECU);
      } catch (_) {}
      if (!want || !ecus.some((e) => e.id === want)) want = data.default || ecus[0]?.id;
      wireCatalogUi();
      await setEcu(want, { persist: false, navigate: false });
      const hash = (location.hash || "").replace(/^#/, "").split("?")[0];
      const ecu = ecus.find((e) => e.id === currentId);
      if (ecu?.mode === "catalog") {
        if (PAGE_IDS_MEVD.includes(hash)) showEcuPage(hash);
        else showEcuPage("ecu-maps");
      }
    } catch (err) {
      console.warn("ecu-switch boot failed", err);
    }
  }

  window.ChercheurEcu = { setEcu, getCurrent: () => currentId, getCatalog: () => catalog };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
