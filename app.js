/*
 * Product Trustworthiness Score prototype.
 * One frontend for every seller state: everything shown comes from data.json,
 * which the backend produces (see README "For the backend team").
 * Load a different file with ?data=other.json, and pick the starting offer
 * with ?seller=C.
 * Data text is always inserted with textContent, never innerHTML, so backend
 * output cannot inject markup.
 */
(function () {
  "use strict";

  // ---------- Constants ----------
  const FACTOR_ORDER = ["history", "brand", "price", "reviews", "complaints"]; // fixed order (US3)
  const FACTOR_NAMES = {
    history: "Seller history",
    brand: "Brand authorisation",
    price: "Price against other sellers",
    reviews: "Review patterns",
    complaints: "Past complaints"
  };
  const STATUS_WORD = { pass: "Pass", warn: "Warning", na: "Not available" };
  const BANDS = {
    High: { rank: 3, cls: "high", icon: "pass", meaning: "Factors are consistent with a genuine product from a reliable seller." },
    Medium: { rank: 2, cls: "medium", icon: "warn", meaning: "Some factors need your attention. Open \"Why this score\" to see which." },
    Low: { rank: 1, cls: "low", icon: "fail", meaning: "Several warning signs. Compare offers from higher-scoring sellers before buying." },
    "Not enough data": { rank: 0, cls: "none", icon: "na", meaning: "The seller is too new or has too few reviews to assess. This is not a warning." }
  };
  // Icon shapes differ by status so meaning never depends on colour alone (WCAG 2.1).
  const ICONS = {
    pass: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/></svg>',
    warn: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
    fail: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/></svg>',
    na: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/></svg>',
    shield: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>'
  };

  // ---------- Helpers ----------
  const $ = (id) => document.getElementById(id);
  const inr = (n) => "₹" + new Intl.NumberFormat("en-IN").format(n);
  const rank = (s) => BANDS[s.band].rank;
  const scored = (s) => s.band !== "Not enough data";

  function el(tag, opts, children) {
    const node = document.createElement(tag);
    if (opts) {
      if (opts.cls) node.className = opts.cls;
      if (opts.text != null) node.textContent = opts.text;
      if (opts.attrs) Object.entries(opts.attrs).forEach(([k, v]) => node.setAttribute(k, v));
    }
    (children || []).forEach((c) => c && node.appendChild(c));
    return node;
  }
  function icon(name, cls) {
    const span = el("span", { cls: "icon " + (cls || "") + " st-" + name });
    span.innerHTML = ICONS[name]; // constant markup only
    return span;
  }
  function bandChip(band) {
    const b = BANDS[band];
    return el("span", { cls: "band band-" + b.cls }, [icon(b.icon), el("span", { text: band })]);
  }
  function announce(msg) { $("announcer").textContent = msg; }

  // ---------- State ----------
  let DATA = null;
  let sellers = [];
  let current = null;
  let lastFocus = null;

  // ---------- Loading and checking data.json ----------
  // Returns a list of problems so the backend team can see exactly what to fix.
  function validate(d) {
    const errs = [];
    const need = (cond, msg) => { if (!cond) errs.push(msg); };
    need(d && typeof d === "object", "File is not a JSON object.");
    if (errs.length) return errs;
    need(d.product && typeof d.product.title === "string", "product.title is missing.");
    need(d.product && typeof d.product.shortTitle === "string", "product.shortTitle is missing.");
    need(Array.isArray(d.sellers) && d.sellers.length > 0, "sellers must be a non-empty list.");
    (d.sellers || []).forEach((s, i) => {
      const at = "sellers[" + i + "]";
      need(s.id, at + ".id is missing.");
      need(typeof s.price === "number", at + ".price must be a number in rupees.");
      need(Object.prototype.hasOwnProperty.call(BANDS, s.band), at + ".band must be High, Medium, Low or Not enough data.");
      need(s.band === "Not enough data" ? s.score === null : typeof s.score === "number",
        at + ".score must be a number, or null when band is Not enough data.");
      need(s.band !== "Not enough data" || typeof s.reason === "string", at + ".reason is required when band is Not enough data.");
      need(Array.isArray(s.inline) && s.inline.length === 3, at + ".inline must list exactly 3 factor keys.");
      FACTOR_ORDER.forEach((k) => {
        const f = s.factors && s.factors[k];
        need(f && ["pass", "warn", "na"].includes(f.status), at + ".factors." + k + ".status must be pass, warn or na.");
        need(f && f.short && f.text && f.source, at + ".factors." + k + " needs short, text and source.");
      });
      (s.inline || []).forEach((k) => need(FACTOR_ORDER.includes(k), at + ".inline has unknown key \"" + k + "\"."));
    });
    return errs;
  }

  function showLoadError(title, lines) {
    const box = el("section", { cls: "load-error", attrs: { role: "alert" } }, [
      el("h1", { text: title }),
      el("ul", null, lines.map((l) => el("li", { text: l })))
    ]);
    $("productView").replaceChildren(box);
  }

  async function start() {
    const params = new URLSearchParams(location.search);
    const file = params.get("data") || "data.json";
    if (location.protocol === "file:") {
      showLoadError("Open this page through a local server", [
        "Browsers block reading data.json when index.html is opened by double-clicking.",
        "VS Code: install the Live Server extension, right-click index.html, choose \"Open with Live Server\".",
        "Or in this folder run: python -m http.server 8000, then open http://localhost:8000",
        "On GitHub Pages it works with no extra steps."
      ]);
      return;
    }
    try {
      const res = await fetch(file, { cache: "no-store" });
      if (!res.ok) throw new Error(file + " returned " + res.status);
      DATA = await res.json();
    } catch (e) {
      showLoadError("Could not load " + file, [String(e.message || e), "Check the file exists next to index.html and is valid JSON."]);
      return;
    }
    const errs = validate(DATA);
    if (errs.length) { showLoadError(file + " does not match the expected format", errs); return; }
    sellers = DATA.sellers;
    current = sellers.find((s) => s.id === (params.get("seller") || sellers[0].id)) || sellers[0];
    renderStatic();
    wire();
    renderOffer();
  }

  // Offers with a higher band than the current one (for Medium/Low only).
  function higherOffers(s) {
    if (!scored(s)) return [];
    return sellers.filter((o) => o.id !== s.id && scored(o) && rank(o) > rank(s));
  }
  function sortOffers(list) {
    return list.slice().sort((a, b) => rank(b) - rank(a) || a.price - b.price);
  }

  // ---------- Product page ----------
  function renderStatic() {
    const p = DATA.product;
    document.title = "Product Trustworthiness Score · Prototype";
    $("breadcrumb").textContent = p.breadcrumb.join(" › ");
    $("title").textContent = p.title;
    $("store").textContent = p.store;
    const full = Math.floor(p.rating);
    const stars = "★".repeat(full) + "☆".repeat(5 - full);
    $("starsRow").replaceChildren(
      el("span", { text: String(p.rating) }),
      el("span", { cls: "stars", text: stars, attrs: { "aria-label": p.rating + " out of 5 stars" } }),
      el("a", { cls: "link", text: p.ratingCount.toLocaleString("en-IN") + " ratings", attrs: { href: "#" } })
    );
    $("bullets").replaceChildren(...p.bullets.map((b) => el("li", { text: b })));
    const img = $("productImage");
    img.onload = () => { img.hidden = false; $("imagePlaceholder").hidden = true; };
    img.src = p.image;
    $("bandMeanings").replaceChildren(...Object.keys(BANDS).map((b) =>
      el("li", { cls: "band-meaning" }, [bandChip(b), el("span", { text: BANDS[b].meaning })])));
    $("demoButtons").replaceChildren(...sellers.map((s) => {
      const btn = el("button", { cls: "demo-btn", text: "Seller " + s.id + " · " + s.band });
      btn.addEventListener("click", () => { selectSeller(s.id); showProduct(); });
      return btn;
    }));
  }

  function renderOffer() {
    const s = current;
    $("priceBig").textContent = inr(s.price);
    $("priceBox").textContent = inr(s.price);
    $("delivery").textContent = s.delivery;
    $("sellerName").textContent = s.name;

    // Price warning (US4): shown only when the price factor warns.
    const pw = $("priceWarning");
    if (s.factors.price.status === "warn") {
      // US4: state the usual range from the other sellers' prices
      const others = sellers.filter((o) => o.id !== s.id).map((o) => o.price);
      const range = others.length ? " (usually " + inr(Math.min(...others)) + " to " + inr(Math.max(...others)) + ")" : "";
      pw.replaceChildren(icon("warn"), el("span", { text: s.factors.price.short + range }));
      pw.hidden = false;
    } else pw.hidden = true;

    // Band (US1, US2)
    $("bandChip").replaceChildren(bandChip(s.band));
    $("bandChip").setAttribute("aria-label", "Authenticity check: " + s.band + ". Show why this score");
    const reason = $("reason");
    reason.hidden = !s.reason;
    reason.textContent = s.reason || "";

    // Three inline factors
    $("inlineFactors").replaceChildren(...s.inline.map((k) => {
      const f = s.factors[k];
      return el("li", null, [icon(f.status), el("span", { text: f.short })]);
    }));

    // Compare link (US5): Medium/Low with at least one higher-scoring offer; other offers for Not enough data.
    const cl = $("compareLink");
    const higher = higherOffers(s);
    if (higher.length) {
      cl.textContent = higher.length + (higher.length === 1 ? " offer" : " offers") + " with a higher score ›";
      cl.hidden = false;
    } else if (!scored(s)) {
      cl.textContent = (sellers.length - 1) + " other offers ›";
      cl.hidden = false;
    } else cl.hidden = true;

    const others = sellers.filter((o) => o.id !== s.id);
    $("otherSellers").textContent = others.length + " other sellers from " + inr(Math.min(...others.map((o) => o.price)));

    document.querySelectorAll(".demo-btn").forEach((b, i) =>
      b.setAttribute("aria-pressed", String(sellers[i].id === s.id)));
  }

  function selectSeller(id) {
    current = sellers.find((s) => s.id === id) || current;
    const url = new URL(location.href);
    url.searchParams.set("seller", current.id);
    history.replaceState(null, "", url);
    renderOffer();
  }

  // ---------- Drawers ----------
  function openDrawer(id) {
    closeDrawers(true);
    lastFocus = document.activeElement;
    $("scrim").hidden = false;
    const d = $(id);
    d.hidden = false;
    d.querySelector("[data-close]").focus();
  }
  function closeDrawers(silent) {
    ["whyDrawer", "compareDrawer", "howDrawer"].forEach((id) => { $(id).hidden = true; });
    $("scrim").hidden = true;
    if (!silent && lastFocus) lastFocus.focus();
  }

  // US3, US7: Why this score
  function openWhy() {
    const s = current;
    $("whySubtitle").textContent = DATA.product.shortTitle + " from " + s.name;
    $("whyScore").replaceChildren(bandChip(s.band),
      el("span", { cls: "muted small", text: s.score == null ? "Not scored yet" : "Guidance only, not a guarantee" }));
    const updated = new Date(DATA.updated + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
    $("whyFactors").replaceChildren(...FACTOR_ORDER.map((k) => {
      const f = s.factors[k];
      const card = el("li", { cls: "factor-card" }, [
        el("div", { cls: "factor-head" }, [icon(f.status), el("strong", { text: FACTOR_NAMES[k] }),
          el("span", { cls: "status st-" + f.status, text: STATUS_WORD[f.status] })]),
        el("p", { text: f.text }),
        el("p", { cls: "source", text: "Source: " + f.source + " · Updated " + updated })
      ]);
      if (k === "reviews" && f.flagged && f.flagged.length) {
        const list = el("ul", { cls: "flagged" }, f.flagged.map((r) => el("li", null, [
          el("div", { cls: "flag-top" }, [el("span", { cls: "tag", text: r.tag }),
            el("span", { cls: "stars", text: "★".repeat(r.stars) + "☆".repeat(5 - r.stars), attrs: { "aria-label": r.stars + " out of 5 stars" } })]),
          el("p", { text: "“" + r.text + "”" })
        ])));
        list.id = "flaggedList";
        list.hidden = true;
        const toggle = el("button", { cls: "text-button", text: "Show " + f.flagged.length + " flagged reviews",
          attrs: { "aria-expanded": "false", "aria-controls": "flaggedList" } });
        toggle.addEventListener("click", () => {
          const open = list.hidden;
          list.hidden = !open;
          toggle.setAttribute("aria-expanded", String(open));
          toggle.textContent = (open ? "Hide " : "Show ") + f.flagged.length + " flagged reviews";
        });
        card.append(toggle, list);
        if (f.excludedDuplicates) card.append(el("p", { cls: "source", text: f.excludedDuplicates + " near-duplicate reviews were excluded from the score." }));
      }
      return card;
    }));
    const higher = higherOffers(s);
    const wc = $("whyCompare");
    wc.hidden = !higher.length;
    wc.textContent = "Compare " + higher.length + (higher.length === 1 ? " offer" : " offers") + " with a higher score";
    openDrawer("whyDrawer");
  }

  // US5: compare offers for the same product
  function openCompare() {
    const s = current;
    const groups = [
      ["Higher-scoring offers", sortOffers(higherOffers(s))],
      ["Current offer", [s]],
      ["Other offers", sortOffers(sellers.filter((o) => o.id !== s.id && scored(o) && (!scored(s) || rank(o) <= rank(s))))],
      ["Not yet scored", sellers.filter((o) => o.id !== s.id && !scored(o))]
    ];
    const list = $("compareList");
    list.replaceChildren();
    groups.forEach(([label, offers]) => {
      if (!offers.length) return;
      list.append(el("h3", { cls: "group-label", text: label }));
      offers.forEach((o) => {
        const isCurrent = o.id === s.id;
        const diff = o.price - s.price;
        const card = el("div", { cls: "offer" + (isCurrent ? " current" : "") }, [
          el("div", { cls: "offer-top" }, [el("strong", { text: o.name }), bandChip(o.band)]),
          el("div", { cls: "offer-price" }, [el("span", { cls: "price", text: inr(o.price) }),
            isCurrent ? null : el("span", { cls: "muted small", text: (diff >= 0 ? "+" : "−") + inr(Math.abs(diff)) + " vs current offer" })]),
          el("div", { cls: "small", text: o.delivery })
        ]);
        if (isCurrent) card.append(el("div", { cls: "viewing", text: "You are viewing this offer" }));
        else {
          const b = el("button", { cls: "btn btn-cart", text: "Choose this offer", attrs: { "aria-label": "Choose offer from " + o.name } });
          b.addEventListener("click", () => {
            selectSeller(o.id);
            closeDrawers(true);
            $("addToCart").focus();
            announce("Now viewing the offer from " + o.name + ", rated " + o.band + ".");
          });
          card.append(b);
        }
        list.append(card);
      });
    });
    openDrawer("compareDrawer");
  }

  // ---------- Cart ----------
  function showCart() {
    const s = current;
    $("cartTitle").textContent = DATA.product.shortTitle;
    $("cartImage").src = DATA.product.image;
    $("cartImage").alt = DATA.product.shortTitle;
    $("cartSeller").textContent = "Sold by " + s.name;
    $("cartBand").replaceChildren(bandChip(s.band));
    $("cartSubtotal").textContent = "Cart subtotal (1 item): " + inr(s.price);
    $("productView").hidden = true;
    $("cartView").hidden = false;
    $("cartCount").textContent = "Cart (1)";
    $("cartHeading").focus();
  }
  function showProduct() {
    $("cartView").hidden = true;
    $("productView").hidden = false;
  }

  // ---------- Wiring ----------
  function wire() {
    $("whyButton").addEventListener("click", openWhy);
    $("bandChip").addEventListener("click", openWhy); // US1: tapping the band opens the explanation
    $("compareLink").addEventListener("click", openCompare);
    $("whyCompare").addEventListener("click", openCompare);
    $("howLink").addEventListener("click", () => openDrawer("howDrawer"));
    $("addToCart").addEventListener("click", showCart);
    $("buyNow").addEventListener("click", showCart);
    $("backToProduct").addEventListener("click", showProduct);
    $("homeLink").addEventListener("click", (e) => { e.preventDefault(); showProduct(); });
    $("scrim").addEventListener("click", () => closeDrawers());
    document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => closeDrawers()));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawers(); });
    $("cartHeading").setAttribute("tabindex", "-1");
    document.querySelectorAll(".icon[data-icon]").forEach((n) => { n.innerHTML = ICONS[n.dataset.icon]; n.classList.add("st-" + n.dataset.icon); });
  }

  start();
})();
