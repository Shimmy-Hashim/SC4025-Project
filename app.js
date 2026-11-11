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
  // A warn factor may carry severity "alert": serious, cannot be outweighed, shown prominently.
  const isAlert = (f) => f.status === "warn" && f.severity === "alert";
  const factorIcon = (f) => (isAlert(f) ? "fail" : f.status);
  const factorWord = (f) => (isAlert(f) ? "Serious alert" : STATUS_WORD[f.status]);
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
    need(d.weights == null || (Array.isArray(d.weights) && d.weights.every((w) => FACTOR_ORDER.includes(w.factor) && typeof w.weight === "number" && typeof w.why === "string")),
      "weights must list factors with a number weight and a why text.");
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
        need(!f || !("severity" in f) || (f.status === "warn" && ["concern", "alert"].includes(f.severity)),
          at + ".factors." + k + ".severity must be concern or alert, on a warn status only.");
      });
      (s.inline || []).forEach((k) => need(FACTOR_ORDER.includes(k), at + ".inline has unknown key \"" + k + "\"."));
      need(s.alert == null || typeof s.alert === "string", at + ".alert must be text or null.");
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
    setupEditor();
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
    // US8: how much each factor counts, as exported by the backend (highest first)
    if (Array.isArray(DATA.weights) && DATA.weights.length) {
      $("howWeights").replaceChildren(...DATA.weights.map((w) => {
        const bar = el("span", { cls: "weight-bar", attrs: { "aria-hidden": "true" } }, [el("span", { cls: "weight-fill" })]);
        bar.firstChild.style.width = w.weight + "%";
        return el("li", { cls: "weight-row" }, [
          el("div", { cls: "weight-top" }, [el("strong", { text: FACTOR_NAMES[w.factor] }), el("span", { cls: "weight-pct", text: w.weight + "%" })]),
          bar,
          el("p", { cls: "small muted", text: w.why })
        ]);
      }));
      $("howWeightsSection").hidden = false;
    }
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

    // Serious alert: shown above everything else, even when the offer is not scored.
    const ab = $("alertBanner");
    if (s.alert) {
      ab.replaceChildren(icon("fail"), el("span", null, [el("strong", { text: s.alert }),
        el("span", { text: " Verify this offer before buying." })]));
      ab.hidden = false;
    } else ab.hidden = true;

    // Price warning (US4): shown when the price factor raises a concern (an alert uses the banner).
    const pw = $("priceWarning");
    if (s.factors.price.status === "warn" && !isAlert(s.factors.price)) {
      // US4: state the usual range from the other sellers' prices, leaving out extreme offers
      const others = sellers.filter((o) => o.id !== s.id && !isAlert(o.factors.price)).map((o) => o.price);
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
      return el("li", null, [icon(factorIcon(f)), el("span", { text: f.short })]);
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
    ["whyDrawer", "compareDrawer", "howDrawer", "inputsDrawer"].forEach((id) => { $(id).hidden = true; });
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
        el("div", { cls: "factor-head" }, [icon(factorIcon(f)), el("strong", { text: FACTOR_NAMES[k] }),
          el("span", { cls: "status st-" + factorIcon(f), text: factorWord(f) })]),
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

  // ---------- Demo: edit seller inputs ----------
  // Only appears when the backend demo server is running (python -m trust_score.cli serve).
  // The backend re-scores with its real rules and returns a new data.json document.
  let editable = null;
  let originalInputs = null;
  let editingId = null;
  let baseline = null;     // the original scored document, for "compared with original"
  let rescoreTimer = null;
  let latestRequest = 0;   // responses from older requests are ignored
  const RESCORE_DELAY_MS = 350;

  async function setupEditor() {
    try {
      const res = await fetch("api/inputs", { cache: "no-store" });
      if (!res.ok || !(res.headers.get("Content-Type") || "").includes("json")) return;
      editable = await res.json();
    } catch (e) {
      return; // static hosting: no backend, so no editor
    }
    originalInputs = JSON.parse(JSON.stringify(editable));
    baseline = DATA;
    $("inSeller").replaceChildren(...editable.sellers.map((s) =>
      el("option", { text: "Seller " + s.id + " · " + s.name, attrs: { value: s.id } })));
    $("inSeller").addEventListener("change", () => {
      if (readForm()) {
        fillForm($("inSeller").value);
        selectSeller(editingId);
        renderLiveResult();
      } else $("inSeller").value = editingId;
    });
    $("editInputs").hidden = false;
    $("editInputs").addEventListener("click", () => {
      fillForm(current.id);
      $("inputsError").hidden = true;
      renderLiveResult();
      renderChanges();
      openDrawer("inputsDrawer");
    });
    // Live re-score: any edit to a seller field schedules one backend call after a short pause.
    $("inputsForm").addEventListener("input", (e) => {
      if (e.target.id === "inSeller") return;
      if (e.target.id === "inComplaintsData") syncComplaintFields();
      scheduleRescore();
    });
    $("inputsForm").addEventListener("submit", (e) => { e.preventDefault(); scheduleRescore(); });
    $("resetInputs").addEventListener("click", () => {
      editable = JSON.parse(JSON.stringify(originalInputs));
      fillForm(editingId);
      $("inputsError").hidden = true;
      rescore();
    });
  }

  function scheduleRescore() {
    clearTimeout(rescoreTimer);
    if (!readForm()) return;
    $("liveResult").classList.add("busy");
    rescoreTimer = setTimeout(rescore, RESCORE_DELAY_MS);
  }

  function editableSeller(id) { return editable.sellers.find((s) => s.id === id); }

  function fillForm(id) {
    const s = editableSeller(id);
    editingId = id;
    $("inSeller").value = id;
    $("inPrice").value = s.price;
    $("inDays").value = s.daysSelling;
    $("inPct").value = s.positiveFeedbackPct == null ? "" : s.positiveFeedbackPct;
    $("inRatings").value = s.feedbackCount;
    $("inOdr").value = s.odrPct == null ? "" : s.odrPct;
    $("inBrand").value = s.brandStatus;
    $("inComplaintsData").value = String(s.complaintsAvailable);
    $("inComplaints").value = s.recentComplaints;
    $("inOrders").value = s.ordersInWindow == null ? "" : s.ordersInWindow;
    $("inConfirmed").checked = s.confirmedCounterfeit;
    $("inFakeReviews").value = s.extraFakeReviews;
    syncComplaintFields();
  }

  // Complaint fields mean nothing when there is no complaints data.
  function syncComplaintFields() {
    const available = $("inComplaintsData").value === "true";
    ["inComplaints", "inOrders", "inConfirmed"].forEach((id) => { $(id).disabled = !available; });
  }

  // Copies the form into the seller being edited. Returns false and shows why if a value is invalid.
  function readForm() {
    const whole = (id, label, min, max) => {
      const v = Number($(id).value);
      if ($(id).value === "" || !Number.isInteger(v) || v < min || v > max) throw new Error(label + " must be a whole number from " + min + " to " + max + ".");
      return v;
    };
    const optional = (id, label, min, max) => {
      const raw = $(id).value.trim();
      if (raw === "") return null;
      const v = Number(raw);
      if (Number.isNaN(v) || v < min || v > max) throw new Error(label + " must be " + min + " to " + max + ", or blank.");
      return v;
    };
    try {
      const s = editableSeller(editingId);
      s.price = whole("inPrice", "Price", 1, 10000000);
      s.daysSelling = whole("inDays", "Days selling", 0, 10950);
      s.positiveFeedbackPct = optional("inPct", "Positive feedback", 0, 100);
      s.feedbackCount = whole("inRatings", "Number of ratings", 0, 10000000);
      s.odrPct = optional("inOdr", "Order defect rate", 0, 100);
      s.brandStatus = $("inBrand").value;
      s.complaintsAvailable = $("inComplaintsData").value === "true";
      s.recentComplaints = whole("inComplaints", "Complaints", 0, 20);
      const orders = optional("inOrders", "Orders in the last 90 days", 1, 10000000);
      if (orders !== null && !Number.isInteger(orders)) throw new Error("Orders in the last 90 days must be a whole number.");
      s.ordersInWindow = orders;
      s.confirmedCounterfeit = $("inConfirmed").checked;
      s.extraFakeReviews = whole("inFakeReviews", "New 1★ reviews", 0, 20);
      $("inputsError").hidden = true;
      return true;
    } catch (e) {
      $("inputsError").textContent = e.message;
      $("inputsError").hidden = false;
      return false;
    }
  }

  async function rescore() {
    const requestId = ++latestRequest;
    const previousBand = current.band;
    try {
      const res = await fetch("api/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sellers: editable.sellers })
      });
      const doc = await res.json();
      if (requestId !== latestRequest) return; // a newer edit is already being scored
      if (!res.ok) throw new Error(doc.error || "The backend returned " + res.status + ".");
      const errs = validate(doc);
      if (errs.length) throw new Error("The backend returned an invalid document: " + errs.join(" "));
      DATA = doc;
      sellers = DATA.sellers;
      renderStatic();
      selectSeller(editingId);
      renderLiveResult();
      renderChanges();
      if (current.band !== previousBand) announce("Seller " + current.id + " is now rated " + current.band + ".");
    } catch (e) {
      if (requestId !== latestRequest) return;
      $("inputsError").textContent = "Could not re-score: " + e.message;
      $("inputsError").hidden = false;
    } finally {
      if (requestId === latestRequest) $("liveResult").classList.remove("busy");
    }
  }

  // The edited seller's current result: band, score and every factor's status.
  function renderLiveResult() {
    const s = sellers.find((o) => o.id === editingId);
    const score = s.score == null ? "Not scored" : "Score " + s.score + " / 100";
    $("liveResult").replaceChildren(
      el("div", { cls: "live-head" }, [el("strong", { text: "Seller " + s.id + " now" }), bandChip(s.band),
        el("span", { cls: "muted", text: score })]),
      s.reason ? el("p", { cls: "reason", text: s.reason }) : null,
      el("ul", { cls: "live-factors" }, FACTOR_ORDER.map((k) => el("li", null, [
        icon(s.factors[k].status),
        el("span", null, [el("strong", { text: FACTOR_NAMES[k] + ": " }), document.createTextNode(s.factors[k].short)])
      ])))
    );
  }

  // Every seller compared with the original inputs.
  function renderChanges() {
    const scoreText = (v) => (v == null ? "not scored" : "score " + v);
    const rows = sellers.map((s) => {
      const b = baseline.sellers.find((o) => o.id === s.id);
      const changed = b.band !== s.band || b.score !== s.score;
      return el("li", { cls: "change-row" }, [
        el("strong", { text: "Seller " + s.id }),
        changed ? bandChip(b.band) : null,
        changed ? el("span", { text: "→" }) : null,
        bandChip(s.band),
        el("span", { cls: "muted", text: changed ? scoreText(b.score) + " → " + scoreText(s.score) : "unchanged" })
      ]);
    });
    $("rescoreResult").replaceChildren(el("strong", { text: "Compared with the original inputs" }), el("ul", null, rows));
    $("rescoreResult").hidden = false;
  }

  start();
})();
