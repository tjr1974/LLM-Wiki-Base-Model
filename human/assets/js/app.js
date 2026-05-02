(() => {
  /** Search index tokenizer contract */
  const SEARCH_TOKENIZE_CONTRACT = "cjk_singleton_v1";

  const state = {
    version: "v1",
    theme: "dark",
    searchIndex: null,
    searchIndexLoaded: false,
    sourceCiteLabelsMap: null,
    sourceCiteLabelsLoaded: false,
  };
  window.__researchWikiShell = state;

  /** Resolve `/…/assets/<path>` for fetch(); works from nested paths (e.g. /entities/foo/). */
  function resolveAssetsHref(pathUnderAssets) {
    const scripts = document.getElementsByTagName("script");
    for (let i = scripts.length - 1; i >= 0; i -= 1) {
      const raw = scripts[i].src;
      if (!raw) {
        continue;
      }
      const u = new URL(raw, window.location.href);
      const fromJs = u.pathname.match(/^(.*\/assets)\/js\//);
      if (fromJs) {
        return new URL(`${fromJs[1]}/${pathUnderAssets}`, u.origin).href;
      }
    }
    const css =
      document.querySelector('link[rel="stylesheet"][href*="/assets/css/"]')
      || document.querySelector('link[rel="stylesheet"][href*="assets/css/"]');
    if (css && css.href) {
      const u = new URL(css.href);
      const fromCss = u.pathname.match(/^(.*\/assets)\/css\//);
      if (fromCss) {
        return new URL(`${fromCss[1]}/${pathUnderAssets}`, u.origin).href;
      }
    }
    return new URL(`assets/${pathUnderAssets}`, window.location.href).href;
  }

  async function loadSearchIndex() {
    if (state.searchIndexLoaded) {
      return state.searchIndex;
    }
    if (window.__researchSearchIndexEmbed && Array.isArray(window.__researchSearchIndexEmbed.pages)) {
      state.searchIndex = window.__researchSearchIndexEmbed;
      state.searchIndexLoaded = true;
      return state.searchIndex;
    }
    try {
      const res = await fetch(resolveAssetsHref("search-index.json"), { credentials: "same-origin" });
      if (!res.ok) {
        throw new Error(String(res.status));
      }
      const data = await res.json();
      if (
        data &&
        data.client &&
        data.client.search_tokenize &&
        data.client.search_tokenize !== SEARCH_TOKENIZE_CONTRACT
      ) {
        console.warn(
          "Wiki search index tokenize mismatch. Expected ",
          SEARCH_TOKENIZE_CONTRACT,
          " got ",
          data.client.search_tokenize,
        );
      }
      state.searchIndex = data;
    } catch (_) {
      state.searchIndex = null;
    }
    state.searchIndexLoaded = true;
    return state.searchIndex;
  }

  /** Mirrors search_index_contract.SEARCH_TOKENIZE_CONTRACT and tests/test_search_tokenize_mirror.py */
  function tokenize(q) {
    return q
      .toLowerCase()
      .split(/[^a-z0-9\u4e00-\u9fff]+/)
      .filter((t) => {
        if (!t) {
          return false;
        }
        if (t.length > 1) {
          return true;
        }
        return /[\u4e00-\u9fff]/.test(t);
      });
  }

  function scoreRow(row, terms) {
    if (!terms.length) {
      return 0;
    }
    const hay = `${row.t || ""} ${row.k || ""}`.toLowerCase();
    let s = 0;
    for (const t of terms) {
      if (hay.includes(t)) {
        s += 2 + Math.min(4, Math.floor(t.length / 4));
      }
    }
    return s;
  }

  function renderHits(rows, limit) {
    if (!rows.length) {
      return "<p class=\"search-empty\">No matches in the static index.</p>";
    }
    const lis = rows.slice(0, limit).map((r) => {
      const u = r.u || "";
      const t = r.t || u;
      return `<li><a href="${u}">${escapeHtml(t)}</a></li>`;
    });
    return `<ol class="search-hit-list">${lis.join("")}</ol>`;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function runSearchIntoResults(q, resultsEl) {
    const trimmed = q.trim();
    if (!trimmed) {
      resultsEl.innerHTML = "<p class=\"search-hint\">Enter a query to search the static index.</p>";
      return;
    }
    const terms = tokenize(trimmed);
    if (!terms.length) {
      resultsEl.innerHTML = "<p class=\"search-empty\">No searchable tokens in that query yet. Try a longer Latin phrase or Chinese characters.</p>";
      return;
    }
    const data = await loadSearchIndex();
    if (!data || !Array.isArray(data.pages)) {
      resultsEl.innerHTML = "<p class=\"search-error\">Search index not available.</p>";
      return;
    }
    const ranked = data.pages
      .map((row) => ({ row, score: scoreRow(row, terms) }))
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score || (a.row.t || "").localeCompare(b.row.t || ""));
    resultsEl.innerHTML = renderHits(
      ranked.map((x) => x.row),
      60,
    );
  }

  function initSearchPage() {
    const form = document.querySelector(".page-search form.search-form");
    const input = form && form.querySelector('input[type="search"]');
    const results = document.querySelector(".page-search .results");
    if (!form || !input || !results) {
      return;
    }

    const params = new URLSearchParams(window.location.search || "");
    const initial = params.get("q") || "";
    if (initial) {
      input.value = initial;
      loadSearchIndex().then(() => runSearchIntoResults(initial, results));
    }

    form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      const q = input.value || "";
      const next = q.trim() ? `?q=${encodeURIComponent(q.trim())}` : "";
      window.history.replaceState({}, "", `${window.location.pathname}${next}`);
      runSearchIntoResults(q, results);
    });
  }

  function insertSpaceBetweenTocTriggerAndTitle(trigger, heading) {
    if (!(heading instanceof HTMLElement) || !(trigger instanceof HTMLElement) || trigger.parentElement !== heading) {
      return;
    }
    const next = trigger.nextSibling;
    if (!next || next.nodeType !== Node.TEXT_NODE) {
      return;
    }
    const raw = next.textContent || "";
    if (raw.length > 0 && !/^\s/.test(raw)) {
      next.textContent = ` ${raw}`;
    }
  }

  function initTocToggle() {
    const toc = document.querySelector(".wiki-toc");
    const trigger = document.querySelector(".toc-trigger");
    const floatingTrigger = document.querySelector(".toc-floating-toggle");
    const pageHeading = document.querySelector(".wiki-body h1");
    const hideBtn = toc && toc.querySelector(".wiki-toc-hide");
    const moveBtn = toc && toc.querySelector(".wiki-toc-move");
    const leftRail = document.getElementById("toc-left-rail");
    const anchor = document.getElementById("wiki-inline-toc-anchor");
    if (!toc || !trigger || !hideBtn || !moveBtn) {
      return;
    }

    // Single source of truth for TOC behavior.
    // placement: where TOC DOM lives; visible: whether TOC is rendered.
    const ui = { placement: "overlay", visible: false };
    const buildTocFromHeadings = () => {
      const sourceRoot = document.querySelector(".wiki-body");
      if (!sourceRoot) {
        return;
      }
      const headings = Array.from(sourceRoot.querySelectorAll("h2[id], h3[id], h4[id], h5[id], h6[id]"));
      const rootList = document.createElement("ol");
      rootList.className = "wiki-toc-list";

      const topItem = document.createElement("li");
      topItem.className = "toc-level-1";
      const topLink = document.createElement("a");
      topLink.href = "#wiki-primary-content";
      topLink.textContent = "(top)";
      topItem.appendChild(topLink);
      rootList.appendChild(topItem);

      /** @type {Record<number, HTMLLIElement>} */
      const itemByLevel = {};
      itemByLevel[1] = topItem;

      headings.forEach((heading) => {
        const level = Number(heading.tagName.slice(1));
        if (!Number.isFinite(level)) {
          return;
        }

        for (let l = level; l <= 6; l += 1) {
          if (l > level) {
            delete itemByLevel[l];
          }
        }

        let parentList = rootList;
        if (level > 2) {
          const parentItem = itemByLevel[level - 1];
          if (parentItem) {
            let sublist = parentItem.querySelector(":scope > .toc-sublist");
            if (!(sublist instanceof HTMLOListElement)) {
              sublist = document.createElement("ol");
              sublist.className = "toc-sublist";
              parentItem.appendChild(sublist);
            }
            parentList = sublist;
          }
        }

        const li = document.createElement("li");
        li.className = `toc-level-${level}`;
        const link = document.createElement("a");
        link.href = `#${heading.id}`;
        link.textContent = heading.textContent ? heading.textContent.trim() : heading.id;
        li.appendChild(link);
        parentList.appendChild(li);
        itemByLevel[level] = li;
      });

      const existingList = toc.querySelector(".wiki-toc-list");
      if (existingList && existingList.parentNode) {
        existingList.parentNode.replaceChild(rootList, existingList);
      } else {
        toc.appendChild(rootList);
      }
    };

    state.ui = state.ui || {};
    state.ui.toc = ui;
    let isBelowPageTitle = false;

    [trigger, floatingTrigger].filter(Boolean).forEach((btn) => {
      btn.setAttribute("aria-haspopup", "true");
    });

    const normalizeTopToggles = () => {
      [trigger, floatingTrigger].filter(Boolean).forEach((btn) => {
        const existingIcon = btn.querySelector(".toc-toggle-icon");
        if (!existingIcon) {
          btn.textContent = "";
          const icon = document.createElement("span");
          icon.className = "toc-toggle-icon";
          icon.setAttribute("aria-hidden", "true");
          icon.textContent = "≡";
          btn.appendChild(icon);
        }
        const sr = btn.querySelector(".visually-hidden");
        if (!sr) {
          const hiddenLabel = document.createElement("span");
          hiddenLabel.className = "visually-hidden";
          hiddenLabel.textContent = "Toggle the table of contents";
          btn.appendChild(hiddenLabel);
        }
      });
    };

    const normalizeSubsectionToggles = () => {
      const tocItems = toc.querySelectorAll(".wiki-toc-list li");
      tocItems.forEach((item) => {
        const sublist = item.querySelector(":scope > .toc-sublist");
        if (!sublist) {
          return;
        }
        item.classList.add("toc-has-children");
        let btn = item.querySelector(":scope > .toc-subtoggle");
        if (!btn) {
          btn = document.createElement("button");
          btn.type = "button";
          btn.className = "toc-subtoggle";
          btn.setAttribute("aria-expanded", "false");
          const firstLink = item.querySelector(":scope > a");
          if (firstLink) {
            firstLink.insertAdjacentElement("beforebegin", btn);
          } else {
            item.insertAdjacentElement("afterbegin", btn);
          }
        }
        if (!item) {
          return;
        }
        const sectionLink = item.querySelector(":scope > a");
        const sectionName = sectionLink ? sectionLink.textContent.trim() : "section";
        if (!sublist.id) {
          const seed = sectionName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
          sublist.id = `toc-sublist-${seed || "section"}`;
        }
        btn.setAttribute("aria-controls", sublist.id);
        btn.setAttribute("aria-label", `Toggle ${sectionName} subsection`);
      });
    };

    const render = () => {
      const inSidebar = ui.placement === "sidebar";
      if (inSidebar) {
        if (leftRail) {
          leftRail.appendChild(toc);
        }
        toc.classList.add("is-sidebar");
        toc.classList.remove("is-overlay");
      } else {
        if (anchor && anchor.parentNode) {
          anchor.parentNode.insertBefore(toc, anchor.nextSibling);
        }
        toc.classList.remove("is-sidebar");
        toc.classList.add("is-overlay");
      }
      const showRail = inSidebar && ui.visible;
      document.body.classList.toggle("has-left-toc", showRail);
      toc.classList.toggle("is-collapsed", !ui.visible);
      document.body.classList.toggle("toc-open", ui.visible);
      document.body.classList.toggle("toc-collapsed", !ui.visible);
      document.body.classList.toggle("toc-below-page-title", isBelowPageTitle);
      [trigger, floatingTrigger].filter(Boolean).forEach((btn) => {
        btn.setAttribute("aria-expanded", ui.visible ? "true" : "false");
        btn.classList.toggle("is-quiet", !isBelowPageTitle);
      });
      hideBtn.setAttribute("aria-label", ui.visible ? "Hide table of contents" : "Show table of contents");
      hideBtn.textContent = ui.visible ? "hide" : "show";
      moveBtn.textContent = inSidebar ? "move to article" : "move to sidebar";
      moveBtn.hidden = !ui.visible;
      refreshFloatingToggle();
    };

    const closeHeaderMenu = () => {
      const navBtn = document.querySelector(".header-nav-toggle");
      document.body.classList.remove("nav-open");
      if (navBtn) {
        navBtn.setAttribute("aria-expanded", "false");
      }
      state.ui = state.ui || {};
      state.ui.headerNavOpen = false;
    };

    [trigger, floatingTrigger].filter(Boolean).forEach((btn) => {
      btn.addEventListener("click", () => {
        // Wikipedia-like exclusivity: opening TOC closes main menu.
        closeHeaderMenu();
        ui.visible = !ui.visible;
        render();
      });
    });

    hideBtn.addEventListener("click", () => {
      ui.visible = !ui.visible;
      render();
    });

    moveBtn.addEventListener("click", () => {
      // Placement toggle never leaves TOC hidden after explicit move.
      closeHeaderMenu();
      ui.placement = ui.placement === "sidebar" ? "inline" : "sidebar";
      ui.visible = true;
      render();
    });

    toc.addEventListener("click", (ev) => {
      const target = ev.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const btn = target.closest(".toc-subtoggle");
      if (!(btn instanceof HTMLButtonElement)) {
        return;
      }
      const item = btn.closest("li");
      const sublist = item ? item.querySelector(":scope > .toc-sublist") : null;
      if (!item || !sublist) {
        return;
      }
      const expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", expanded ? "false" : "true");
      item.classList.toggle("toc-level-expanded", !expanded);
      sublist.hidden = expanded;
    });

    const initializeSubsectionState = () => {
      const toggles = toc.querySelectorAll(".toc-subtoggle");
      toggles.forEach((btn) => {
        const item = btn.closest("li");
        if (!item) {
          return;
        }
        const sublist = item.querySelector(":scope > .toc-sublist");
        if (!sublist) {
          return;
        }
        // Vector-like default: collapsed on page load.
        btn.setAttribute("aria-expanded", "false");
        item.classList.remove("toc-level-expanded");
        sublist.hidden = true;
      });
    };

    const closeOverlay = () => {
      if (!ui.visible) {
        return;
      }
      ui.visible = false;
      render();
    };

    const syncHeaderToggleStyle = () => {
      if (!pageHeading) {
        return;
      }
      const headingRect = pageHeading.getBoundingClientRect();
      const nextBelowPageTitle = headingRect.bottom < 12;
      if (nextBelowPageTitle !== isBelowPageTitle) {
        isBelowPageTitle = nextBelowPageTitle;
        render();
      }
    };

    if (pageHeading) {
      if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
          (entries) => {
            const [entry] = entries;
            const nextBelowPageTitle = !entry.isIntersecting;
            if (nextBelowPageTitle !== isBelowPageTitle) {
              isBelowPageTitle = nextBelowPageTitle;
              render();
            }
          },
          { rootMargin: "-12px 0px 0px 0px", threshold: 0 },
        );
        observer.observe(pageHeading);
      } else {
        window.addEventListener("scroll", syncHeaderToggleStyle, { passive: true });
        syncHeaderToggleStyle();
      }
    }

    const refreshFloatingToggle = () => {
      const y = window.scrollY || document.documentElement.scrollTop || 0;
      const stickyCollapsed = !ui.visible && y > 120;
      document.body.classList.toggle("toc-sticky-trigger-visible", stickyCollapsed);
      if (trigger) {
        trigger.classList.toggle("is-sticky", stickyCollapsed);
      }
      if (floatingTrigger) {
        floatingTrigger.style.display = (stickyCollapsed || ui.visible) ? "inline-flex" : "none";
      }
    };
    window.addEventListener("scroll", refreshFloatingToggle, { passive: true });
    refreshFloatingToggle();

    document.addEventListener("click", (ev) => {
      const target = ev.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const clickedToc = !!target.closest(".wiki-toc");
      const clickedTrigger = !!target.closest(".toc-trigger, .toc-floating-toggle");
      if (!clickedToc && !clickedTrigger) {
        closeOverlay();
      }
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        closeOverlay();
      }
    });

    insertSpaceBetweenTocTriggerAndTitle(trigger, pageHeading);
    buildTocFromHeadings();
    normalizeTopToggles();
    normalizeSubsectionToggles();
    initializeSubsectionState();
    render();
  }

  function initHeaderNavToggle() {
    const btn = document.querySelector(".header-nav-toggle");
    if (!btn) {
      return;
    }
    btn.addEventListener("click", () => {
      const next = !document.body.classList.contains("nav-open");
      if (next) {
        const toc = document.querySelector(".wiki-toc");
        const trigger = document.querySelector(".toc-trigger");
        const floatingTrigger = document.querySelector(".toc-floating-toggle");
        if (toc) {
          toc.classList.add("is-collapsed");
        }
        document.body.classList.remove("has-left-toc");
        [trigger, floatingTrigger].filter(Boolean).forEach((control) => {
          control.setAttribute("aria-expanded", "false");
        });
        if (state.ui && state.ui.toc) {
          state.ui.toc.visible = false;
        }
      }
      document.body.classList.toggle("nav-open", next);
      btn.setAttribute("aria-expanded", next ? "true" : "false");
      state.ui = state.ui || {};
      state.ui.headerNavOpen = next;
    });
  }

  /** Map site pathname (`/entities/foo/` ) to wiki id (`wiki/entities/foo`) for Related links. */
  function pathnameToWikiId(pathname) {
    const pathPart = String(pathname || "")
      .replace(/\/index\.html?$/iu, "")
      .replace(/^\/+|\/+$/gu, "");
    return pathPart ? `wiki/${pathPart}` : "";
  }

  async function loadSourceCiteLabels() {
    if (state.sourceCiteLabelsLoaded) {
      return state.sourceCiteLabelsMap;
    }
    try {
      const res = await fetch(resolveAssetsHref("data/source-cite-labels.min.json"), {
        credentials: "same-origin",
      });
      if (!res.ok) {
        throw new Error(String(res.status));
      }
      const data = await res.json();
      if (!data || data.v !== 1 || !data.l || typeof data.l !== "object") {
        throw new Error("source cite labels mismatch");
      }
      state.sourceCiteLabelsMap = data.l;
    } catch (_) {
      state.sourceCiteLabelsMap = null;
    }
    state.sourceCiteLabelsLoaded = true;
    return state.sourceCiteLabelsMap;
  }

  /** Normalize pathname to url-paths.txt keys (trailing slash except root). */
  function siteInboundPathKey(pathname) {
    const raw = String(pathname || "");
    if (raw === "/" || raw === "") {
      return "/";
    }
    return raw.endsWith("/") ? raw : `${raw}/`;
  }

  /** Underscores to spaces; keeps author intent from wiki source frontmatter. */
  function humanizeSourceTitle(t) {
    return String(t || "")
      .replace(/_/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function parseSourcesHref(rawHref, baseHref) {
    try {
      const u = new URL(rawHref || "", baseHref || window.location.href);
      const m = u.pathname.match(/\/sources\/([^/]+)/);
      if (!m) {
        return null;
      }
      const anchor = u.hash ? u.hash.replace(/^#/, "") : "";
      return { sid: m[1], anchor };
    } catch (_) {
      return null;
    }
  }

  function composeEvidenceLinkText(labelsMap, sid, anchor) {
    const entry = labelsMap && typeof labelsMap[sid] === "object" ? labelsMap[sid] : null;
    const rawTtl =
      entry && typeof entry.ttl === "string" && entry.ttl.trim()
        ? entry.ttl.trim()
        : sid;
    const base = humanizeSourceTitle(rawTtl);
    if (!anchor) {
      return base;
    }
    const chunkMatch = /^c-(\d+)$/i.exec(anchor);
    if (chunkMatch) {
      return `${base} (chunk ${chunkMatch[1]})`;
    }
    return `${base} (${anchor})`;
  }

  /** Improve reference list link text, Related navigation labels; dedupe corpus Works cited row. */
  async function initWikiCitationUi() {
    const body = document.querySelector(".wiki-body");
    if (!(body instanceof HTMLElement)) {
      return;
    }
    const targets = body.querySelector("section.wiki-references, section.wiki-sources, h2#related");
    if (!(targets instanceof Element)) {
      return;
    }
    await Promise.all([loadSearchIndex(), loadSourceCiteLabels()]);
    const labelsMap =
      state.sourceCiteLabelsMap && typeof state.sourceCiteLabelsMap === "object"
        ? state.sourceCiteLabelsMap
        : null;
    /** @type {Record<string, string>} */
    const pageTitles = {};
    const si = state.searchIndex;
    if (si && Array.isArray(si.pages)) {
      for (const p of si.pages) {
        if (!p || typeof p.u !== "string" || typeof p.t !== "string") {
          continue;
        }
        try {
          const pathname = new URL(p.u, window.location.href).pathname;
          const wid = pathnameToWikiId(pathname);
          const title = p.t.trim();
          if (wid && title) {
            pageTitles[wid] = title;
          }
        } catch (_) {
          /* ignore bad rows */
        }
      }
    }

    body.querySelectorAll("section.wiki-references ol li").forEach((li) => {
      const linkEl = Array.from(li.querySelectorAll(":scope > a")).find(
        (a) =>
          !(a instanceof HTMLElement && a.classList.contains("ref-backlink")) &&
          a instanceof HTMLAnchorElement,
      );
      if (!(linkEl instanceof HTMLAnchorElement)) {
        return;
      }
      const parsed = parseSourcesHref(linkEl.getAttribute("href") || "", window.location.href);
      if (!parsed) {
        return;
      }
      linkEl.textContent = composeEvidenceLinkText(labelsMap, parsed.sid, parsed.anchor);
    });

    const relH = body.querySelector("h2#related");
    const relUl =
      relH && relH.nextElementSibling instanceof HTMLUListElement ? relH.nextElementSibling : null;
    if (relUl instanceof HTMLUListElement) {
      relUl.querySelectorAll("sup.reference").forEach((sup) => sup.remove());
      relUl.querySelectorAll("a.wiki-link[href]").forEach((nav) => {
        if (!(nav instanceof HTMLAnchorElement)) {
          return;
        }
        const pathMatch = /^\/+|\/+$/u;
        let pathPart = "";
        try {
          const nu = new URL(nav.href);
          pathPart = nu.pathname.replace(/\/index\.html?$/iu, "").replace(/^\/+|\/+$/gu, "");
        } catch (_) {
          pathPart = (nav.getAttribute("href") || "").replace(/^[./]+/, "").replace(/\/+$/gu, "");
        }
        pathPart = pathPart.replace(/^\/+|\/+$/gu, "");
        const wid = pathPart ? `wiki/${pathPart}` : "";
        if (wid && pageTitles[wid]) {
          nav.textContent = pageTitles[wid];
        }
      });
    }

    const works = body.querySelector("section.wiki-sources");
    const refOl = body.querySelector("section.wiki-references ol");
    if (works instanceof HTMLElement && refOl instanceof HTMLOListElement && !works.dataset.wikiWorksDeduped) {
      works.dataset.wikiWorksDeduped = "1";
      const h2 = works.querySelector("h2#sources") || works.querySelector("h2");
      const oldUl = works.querySelector("ul");
      let replacedWorksCited = false;
      if (h2 instanceof HTMLElement && oldUl instanceof HTMLUListElement) {
        const seenSid = new Set();
        /** @type {string[]} */
        const order = [];
        refOl.querySelectorAll(":scope > li").forEach((li) => {
          const linkEl =
            Array.from(li.querySelectorAll(":scope > a")).find(
              (a) =>
                !(a instanceof HTMLElement && a.classList.contains("ref-backlink")) &&
                a instanceof HTMLAnchorElement,
            ) || li.querySelector("a");
          if (!(linkEl instanceof HTMLAnchorElement)) {
            return;
          }
          const parsed = parseSourcesHref(linkEl.getAttribute("href") || "", window.location.href);
          if (!parsed || seenSid.has(parsed.sid)) {
            return;
          }
          seenSid.add(parsed.sid);
          order.push(parsed.sid);
        });

        const introClass = "wiki-works-cited-intro";
        if (!works.querySelector(`.${introClass}`)) {
          const hint = document.createElement("p");
          hint.className = introClass;
          hint.textContent =
            "In-repo dossiers cited on this page (one row per imported source record). Links open each source dossier (metadata and anchors). Raw files remain local to this repository.";
          works.insertBefore(hint, oldUl);
        }

        const ul = document.createElement("ul");
        order.forEach((sid) => {
          const li = document.createElement("li");
          const a = document.createElement("a");
          a.className = "wiki-link";
          a.href = `/sources/${sid}/`;
          const entry =
            labelsMap && typeof labelsMap[sid] === "object"
              ? labelsMap[sid]
              : null;
          const ttl =
            entry && typeof entry.ttl === "string" && entry.ttl.trim()
              ? humanizeSourceTitle(entry.ttl.trim())
              : humanizeSourceTitle(sid.replace(/_/g, " "));
          a.textContent = ttl;
          li.appendChild(a);
          ul.appendChild(li);
        });
        works.replaceChild(ul, oldUl);
        replacedWorksCited = true;
      }
      if (
        replacedWorksCited &&
        h2 instanceof HTMLElement &&
        h2.id === "sources" &&
        /^sources$/iu.test(String(h2.textContent || "").trim())
      ) {
        h2.textContent = "Works cited";
      }
    }
  }

  async function initInboundWikiLinks() {
    const body = document.querySelector(".wiki-body");
    if (!(body instanceof HTMLElement) || body.querySelector("#wiki-inbound-links")) {
      return;
    }
    const pathKey = siteInboundPathKey(window.location.pathname);

    let blob;
    try {
      const res = await fetch(resolveAssetsHref("data/site-backlinks.min.json"), {
        credentials: "same-origin",
      });
      if (!res.ok) {
        return;
      }
      blob = await res.json();
    } catch (_) {
      return;
    }
    if (!blob || blob.v !== 1 || !blob.by_u || typeof blob.by_u !== "object") {
      return;
    }
    const rows = blob.by_u[pathKey];
    if (!Array.isArray(rows) || rows.length === 0) {
      return;
    }

    await loadSearchIndex();
    const si = state.searchIndex;
    /** @type {Record<string, string>} */
    const pageTitles = {};
    if (si && Array.isArray(si.pages)) {
      for (const p of si.pages) {
        if (!p || typeof p.u !== "string" || typeof p.t !== "string") {
          continue;
        }
        try {
          const pathname = new URL(p.u, window.location.href).pathname;
          pageTitles[siteInboundPathKey(pathname)] = p.t.trim();
        } catch (_) {
          /* ignore */
        }
      }
    }

    const refBlock = body.querySelector("section.wiki-references, section.wiki-sources");
    const sec = document.createElement("section");
    sec.id = "wiki-inbound-links";
    sec.className = "wiki-inbound-links";
    sec.setAttribute("aria-labelledby", "wiki-inbound-links-heading");

    const h = document.createElement("h2");
    h.id = "wiki-inbound-links-heading";
    h.textContent = "Pages in this bundle that link here";
    sec.appendChild(h);

    const pIntro = document.createElement("p");
    pIntro.className = "wiki-inbound-intro";
    pIntro.textContent =
      "Derived from the repository wikilink graph. Listed pages are limited to routes present in this static export.";
    sec.appendChild(pIntro);

    const ul = document.createElement("ul");
    ul.className = "wiki-inbound-list";
    for (const row of rows) {
      if (!row || typeof row.u !== "string") {
        continue;
      }
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.className = "wiki-link";
      a.href = row.u;
      const lk = siteInboundPathKey(row.u);
      const label =
        (typeof row.t === "string" && row.t.trim()) || pageTitles[lk] || row.u;
      a.textContent = label;
      li.appendChild(a);
      ul.appendChild(li);
    }
    sec.appendChild(ul);

    if (refBlock instanceof HTMLElement) {
      body.insertBefore(sec, refBlock);
    } else {
      body.appendChild(sec);
    }
  }

  function initLastEditedFooter() {
    const timeEl = document.getElementById("page-last-edited-time");
    if (!timeEl) {
      return;
    }
    const raw = document.lastModified;
    const parsed = raw ? new Date(raw) : new Date();
    const date = Number.isNaN(parsed.getTime()) ? new Date() : parsed;
    const yyyy = String(date.getFullYear());
    const mm = String(date.getMonth() + 1).padStart(2, "0");
    const dd = String(date.getDate()).padStart(2, "0");
    const hh = String(date.getHours()).padStart(2, "0");
    const min = String(date.getMinutes()).padStart(2, "0");
    const value = `${yyyy}-${mm}-${dd} at ${hh}:${min}`;
    timeEl.textContent = value;
    timeEl.setAttribute("datetime", `${yyyy}-${mm}-${dd}T${hh}:${min}`);
  }

  function bootResearchWikiFrontend() {
    const chain = Promise.resolve()
      .then(() => initWikiCitationUi())
      .then(() => initInboundWikiLinks())
      .catch(() => {});
    chain.finally(() => {
      initSearchPage();
      initTocToggle();
      initHeaderNavToggle();
      initLastEditedFooter();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootResearchWikiFrontend);
  } else {
    bootResearchWikiFrontend();
  }
})();
