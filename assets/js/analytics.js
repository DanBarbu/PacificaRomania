/* PacificaRomania — consent-gated Matomo analytics (EU GDPR + ePrivacy).
 *
 * Matomo is loaded ONLY after the visitor opts in. Reject is as easy as accept,
 * Do-Not-Track is honoured as a refusal, and the choice can be withdrawn at any
 * time via the "Cookie settings" control. Configuration is provided by an inline
 *   window.PR_MATOMO = { url: "https://…/", siteId: "1" }
 * emitted by tools/build_seo.py. If that config is absent, nothing happens.
 */
(function () {
  var cfg = window.PR_MATOMO;
  if (!cfg || !cfg.url || !cfg.siteId) return;

  var KEY = "pr-consent";                 // "granted" | "denied"
  var stored = null;
  try { stored = localStorage.getItem(KEY); } catch (e) {}
  var dnt = (navigator.doNotTrack === "1" || window.doNotTrack === "1" ||
             navigator.doNotTrack === "yes");

  var _paq = (window._paq = window._paq || []);
  var matomoLoaded = false;

  function bootstrapMatomo() {
    // Require consent up front: no cookies, no tracking until we say so.
    _paq.push(["requireConsent"]);
    _paq.push(["requireCookieConsent"]);
    _paq.push(["enableLinkTracking"]);
    _paq.push(["setTrackerUrl", cfg.url + "matomo.php"]);
    _paq.push(["setSiteId", cfg.siteId]);
  }

  function loadMatomoJs() {
    if (matomoLoaded) return;
    matomoLoaded = true;
    var g = document.createElement("script");
    g.async = true;
    g.src = cfg.url + "matomo.js";
    var s = document.getElementsByTagName("script")[0];
    s.parentNode.insertBefore(g, s);
  }

  function grant() {
    try { localStorage.setItem(KEY, "granted"); } catch (e) {}
    _paq.push(["setConsentGiven"]);
    _paq.push(["setCookieConsentGiven"]);
    _paq.push(["trackPageView"]);
    loadMatomoJs();
  }

  function deny() {
    try { localStorage.setItem(KEY, "denied"); } catch (e) {}
    _paq.push(["forgetConsentGiven"]);
  }

  // ---- consent banner UI (bilingual via existing data-l / .lang-ro CSS) ----
  var banner = null;
  function buildBanner() {
    if (banner) { banner.hidden = false; return; }
    banner = document.createElement("div");
    banner.className = "consent-banner";
    banner.setAttribute("role", "dialog");
    banner.setAttribute("aria-modal", "false");
    banner.setAttribute("aria-label", "Cookie consent / Consimțământ cookie");
    banner.innerHTML =
      '<div class="consent-inner">' +
        '<p class="consent-text">' +
          '<span data-l="en">We use <strong>Matomo</strong> analytics (self-hosted) to understand site traffic. It sets cookies and records visit data, including an anonymised approximate location, only if you agree. See our <a href="' + rel() + 'privacy.html">Privacy &amp; Cookie Policy</a>.</span>' +
          '<span data-l="ro">Folosim analiza <strong>Matomo</strong> (găzduită de noi) pentru a înțelege traficul. Aceasta plasează cookie-uri și înregistrează date despre vizită, inclusiv o localizare aproximativă anonimizată, doar dacă sunteți de acord. Vedeți <a href="' + rel() + 'privacy.html">Politica de confidențialitate și cookie</a>.</span>' +
        '</p>' +
        '<div class="consent-actions">' +
          '<button type="button" class="consent-btn consent-reject" data-act="deny">' +
            '<span data-l="en">Reject</span><span data-l="ro">Refuz</span></button>' +
          '<button type="button" class="consent-btn consent-accept" data-act="grant">' +
            '<span data-l="en">Accept</span><span data-l="ro">Accept</span></button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(banner);
    banner.addEventListener("click", function (e) {
      var b = e.target.closest("[data-act]");
      if (!b) return;
      if (b.getAttribute("data-act") === "grant") grant(); else deny();
      hideBanner();
    });
  }
  function hideBanner() { if (banner) banner.hidden = true; showSettingsLink(); }

  // Persistent "Cookie settings" control so consent is always withdrawable.
  var settingsLink = null;
  function showSettingsLink() {
    if (settingsLink) { settingsLink.hidden = false; return; }
    settingsLink = document.createElement("button");
    settingsLink.type = "button";
    settingsLink.className = "consent-settings";
    settingsLink.innerHTML =
      '<span data-l="en">Cookie settings</span><span data-l="ro">Setări cookie</span>';
    settingsLink.addEventListener("click", function () {
      settingsLink.hidden = true;
      buildBanner();
      banner.hidden = false;
    });
    document.body.appendChild(settingsLink);
  }

  // Relative prefix so links resolve from /journal/ and /collection/ too.
  function rel() {
    // /journal/x.html -> 2 path segments; root pages -> 1.
    var depth = location.pathname.split("/").filter(Boolean).length;
    return depth > 1 ? "../" : "";
  }

  // Expose for a footer "Cookie settings" link if present.
  window.PRConsent = {
    open: function () { buildBanner(); banner.hidden = false; if (settingsLink) settingsLink.hidden = true; },
    reset: function () { try { localStorage.removeItem(KEY); } catch (e) {} }
  };

  function start() {
    bootstrapMatomo();
    if (stored === "granted") {
      grant();
      showSettingsLink();
    } else if (stored === "denied" || dnt) {
      if (dnt && stored !== "denied") deny();
      showSettingsLink();
    } else {
      buildBanner();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
