/*
 * engagement.js
 * -------------
 * Lightweight "quality of life" layer on top of the static site -- no
 * backend, no accounts, nothing but localStorage plus two small JSON files
 * build_site.py already writes at the site root (card-index.json and
 * snapshot-summary.json). Everything here degrades to a silent no-op if
 * localStorage or fetch is unavailable -- none of this is load-bearing for
 * the rest of the site.
 *
 * Three independent features:
 *   1. "Since Your Last Visit" banner        (every page, via #cp-visit-banner)
 *   2. Watchlist heart buttons                (homepage mover/quick-hit cards)
 *   3. "Cards You're Watching" strip           (homepage only, #watchlist-section)
 *
 * Root-relative fetches use window.CARDPULSE_ROOT (set in base.html) --
 * NOT a leading "/" -- because this site is served from a GitHub Pages
 * project subpath (proxylair.github.io/cardpulse/), not the domain root.
 * A hardcoded "/card-index.json" would 404 there. (This exact class of bug
 * bit the push-notification service worker once already -- see subscribe.js.)
 */
(function () {
  "use strict";

  var ROOT = window.CARDPULSE_ROOT || "";
  var LAST_VISIT_KEY = "cp_last_visit";
  var WATCHLIST_KEY = "cp_watchlist";

  // ---------- tiny localStorage helpers (all fail silently) ----------

  function readWatchlist() {
    try {
      var raw = localStorage.getItem(WATCHLIST_KEY);
      var list = raw ? JSON.parse(raw) : [];
      return Array.isArray(list) ? list : [];
    } catch (e) {
      return [];
    }
  }

  function writeWatchlist(list) {
    try {
      localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
    } catch (e) {
      /* private browsing / storage disabled -- feature just won't persist */
    }
  }

  function isWatched(key) {
    return readWatchlist().indexOf(key) !== -1;
  }

  // Returns true if the card is now watched (false if it was just removed).
  function toggleWatch(key) {
    var list = readWatchlist();
    var idx = list.indexOf(key);
    if (idx === -1) {
      list.push(key);
    } else {
      list.splice(idx, 1);
    }
    writeWatchlist(list);
    return idx === -1;
  }

  function fetchJson(path) {
    return fetch(ROOT + path, { cache: "no-store" }).then(function (res) {
      if (!res.ok) throw new Error("fetch failed: " + path);
      return res.json();
    });
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // ---------- 1. Since Your Last Visit ----------

  function initVisitBanner() {
    var container = document.getElementById("cp-visit-banner");
    if (!container) return;

    var lastVisit;
    try {
      lastVisit = localStorage.getItem(LAST_VISIT_KEY);
    } catch (e) {
      return; // no localStorage -- nothing to compare against, skip entirely
    }

    fetchJson("snapshot-summary.json").then(function (summary) {
      var today = summary.last_updated;
      if (today && lastVisit && lastVisit !== today && summary.mover_count > 0) {
        var topBits = (summary.top_movers || []).slice(0, 3).map(function (t) {
          var pct = typeof t.pct === "number" ? t.pct : 0;
          return escapeHtml(t.name) + " (" + (pct > 0 ? "+" : "") + pct.toFixed(0) + "%)";
        }).join(", ");
        var plural = summary.mover_count === 1 ? "" : "s";
        container.innerHTML =
          '<div class="visit-banner">' +
          "<span>👋 Welcome back — since your last visit on " + escapeHtml(lastVisit) + ", " +
          summary.mover_count + " card" + plural + " moved" + (topBits ? ": " + topBits : "") + ".</span>" +
          '<a href="' + ROOT + 'index.html#movers">See what moved</a>' +
          '<button type="button" class="visit-banner-close" aria-label="Dismiss">×</button>' +
          "</div>";
        var closeBtn = container.querySelector(".visit-banner-close");
        if (closeBtn) {
          closeBtn.addEventListener("click", function () {
            container.innerHTML = "";
          });
        }
      }
      try {
        localStorage.setItem(LAST_VISIT_KEY, today || lastVisit || "");
      } catch (e) { /* ignore */ }
    }).catch(function () {
      /* summary.json missing/unreachable -- nice-to-have, fail quiet */
    });
  }

  // ---------- 2. Watchlist heart buttons ----------

  function paintButton(btn, watching) {
    btn.setAttribute("aria-pressed", watching ? "true" : "false");
    btn.classList.toggle("watching", watching);
    var icon = btn.querySelector(".watch-icon");
    if (icon) icon.textContent = watching ? "♥" : "♡";
    var name = btn.getAttribute("data-card-name") || "this card";
    btn.setAttribute(
      "aria-label",
      watching ? "Remove " + name + " from your watchlist" : "Add " + name + " to your watchlist"
    );
  }

  function wireWatchButton(btn) {
    var key = btn.getAttribute("data-card-key");
    if (!key || btn.__cpWired) return;
    btn.__cpWired = true;
    paintButton(btn, isWatched(key));
    btn.addEventListener("click", function (evt) {
      evt.preventDefault();
      evt.stopPropagation();
      var nowWatching = toggleWatch(key);
      // Sync every button for this card on the page (a mover-grid card and
      // its quick-hit twin can both reference the same key).
      document.querySelectorAll('.watch-btn[data-card-key="' + key + '"]').forEach(function (b) {
        paintButton(b, nowWatching);
      });
      refreshWatchlistSection();
    });
  }

  function initWatchButtons() {
    document.querySelectorAll(".watch-btn[data-card-key]").forEach(wireWatchButton);
  }

  // ---------- 3. "Cards You're Watching" strip ----------

  function renderWatchCard(key, card) {
    var hasPct = typeof card.pct === "number";
    var direction = hasPct ? (card.pct >= 0 ? "up" : "down") : "";
    var arrow = direction === "up" ? "▲" : direction === "down" ? "▼" : "";
    var pctHtml = hasPct
      ? '<span class="quick-hit-pct ' + direction + '">' + arrow + " " +
        (card.pct > 0 ? "+" : "") + card.pct.toFixed(0) + "%</span>"
      : "";
    var img = card.image
      ? '<img src="' + escapeHtml(card.image) + '" alt="' + escapeHtml(card.name) + '" loading="lazy">'
      : '<div class="quick-hit-noimg">🃏</div>';
    var linkOpen = card.url
      ? '<a href="' + escapeHtml(card.url) + '" target="_blank" rel="noopener nofollow">'
      : "<div>";
    var linkClose = card.url ? "</a>" : "</div>";
    var priceText = typeof card.price === "number" ? "$" + card.price.toFixed(2) : "--";
    return (
      '<div class="quick-hit" data-card-key="' + escapeHtml(key) + '">' +
      '<button type="button" class="watch-btn watching" data-card-key="' + escapeHtml(key) +
      '" data-card-name="' + escapeHtml(card.name) + '" aria-pressed="true" ' +
      'aria-label="Remove ' + escapeHtml(card.name) + ' from your watchlist">' +
      '<span class="watch-icon">♥</span></button>' +
      linkOpen + img +
      '<div class="quick-hit-body">' + pctHtml +
      "<strong>" + escapeHtml(card.name) + "</strong>" +
      '<span class="quick-hit-price">' + priceText + "</span>" +
      "</div>" + linkClose +
      "</div>"
    );
  }

  function refreshWatchlistSection() {
    var section = document.getElementById("watchlist-section");
    var strip = document.getElementById("watchlist-strip");
    if (!section || !strip) return; // not the homepage -- nothing to do

    var keys = readWatchlist();
    if (!keys.length) {
      section.hidden = true;
      strip.innerHTML = "";
      return;
    }

    fetchJson("card-index.json").then(function (index) {
      var html = keys
        .map(function (key) {
          var card = index[key];
          return card ? renderWatchCard(key, card) : "";
        })
        .join("");
      if (!html) {
        section.hidden = true;
        strip.innerHTML = "";
        return;
      }
      strip.innerHTML = html;
      section.hidden = false;
      strip.querySelectorAll(".watch-btn[data-card-key]").forEach(wireWatchButton);
    }).catch(function () {
      // card-index.json missing/unreachable -- hide rather than show a
      // broken/empty section.
      section.hidden = true;
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initVisitBanner();
    initWatchButtons();
    refreshWatchlistSection();
  });
})();
