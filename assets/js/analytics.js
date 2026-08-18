/* PacificaRomania — consent-gated analytics (EU/UK GDPR + ePrivacy).
 *
 * Drives Google Analytics 4 (Consent Mode v2) and/or self-hosted Matomo. No
 * analytics cookies or personal data are stored until the visitor opts in;
 * Reject is as easy as Accept, Do-Not-Track is honoured as a refusal, and the
 * choice can be withdrawn any time via the "Cookie settings" control.
 *
 * Config is emitted into <head> by tools/build_seo.py as:
 *   window.PR_GA     = { id: "G-XXXXXXXXXX" }         // Google Analytics 4
 *   window.PR_MATOMO = { url: "https://…/", siteId: "1" }  // Matomo
 * For GA, the <head> also loads gtag.js and sets Consent Mode defaults to
 * DENIED; this script flips analytics_storage to GRANTED on opt-in. If neither
 * config is present, nothing happens.
 */
(function () {
  var GA = window.PR_GA && window.PR_GA.id ? window.PR_GA : null;
  var MT = (window.PR_MATOMO && window.PR_MATOMO.url && window.PR_MATOMO.siteId)
    ? window.PR_MATOMO : null;
  if (!GA && !MT) return;

  var KEY = "pr-consent";                 // "granted" | "denied"
  var stored = null;
  try { stored = localStorage.getItem(KEY); } catch (e) {}
  var dnt = (navigator.doNotTrack === "1" || window.doNotTrack === "1" ||
             navigator.doNotTrack === "yes");

  // ---- Google Analytics 4 (Consent Mode v2) --------------------------------
  function gtag() { (window.dataLayer = window.dataLayer || []).push(arguments); }
  function gaGrant() {
    if (!GA) return;
    gtag("consent", "update", { analytics_storage: "granted" });
    gtag("event", "page_view");           // count this page now that we may
  }
  function gaDeny() {
    if (!GA) return;
    gtag("consent", "update", { analytics_storage: "denied" });
  }

  // ---- Matomo (self-hosted) ------------------------------------------------
  var _paq = MT ? (window._paq = window._paq || []) : null;
  var matomoLoaded = false;
  function matomoBootstrap() {
    if (!MT) return;
    _paq.push(["requireConsent"]);
    _paq.push(["requireCookieConsent"]);
    _paq.push(["enableLinkTracking"]);
    _paq.push(["setTrackerUrl", MT.url + "matomo.php"]);
    _paq.push(["setSiteId", MT.siteId]);
  }
  function matomoLoadJs() {
    if (!MT || matomoLoaded) return;
    matomoLoaded = true;
    var g = document.createElement("script");
    g.async = true;
    g.src = MT.url + "matomo.js";
    var s = document.getElementsByTagName("script")[0];
    s.parentNode.insertBefore(g, s);
  }
  function matomoGrant() {
    if (!MT) return;
    _paq.push(["setConsentGiven"]);
    _paq.push(["setCookieConsentGiven"]);
    _paq.push(["trackPageView"]);
    matomoLoadJs();
  }
  function matomoDeny() {
    if (!MT) return;
    _paq.push(["forgetConsentGiven"]);
  }

  function grant() {
    try { localStorage.setItem(KEY, "granted"); } catch (e) {}
    gaGrant(); matomoGrant();
  }
  function deny() {
    try { localStorage.setItem(KEY, "denied"); } catch (e) {}
    gaDeny(); matomoDeny();
  }

  // Human-readable provider name for the banner copy.
  function providerEN() {
    if (GA && MT) return "Google Analytics and Matomo";
    return GA ? "Google Analytics" : "Matomo";
  }
  function providerRO() {
    if (GA && MT) return "Google Analytics și Matomo";
    return GA ? "Google Analytics" : "Matomo";
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
          '<span data-l="en">We use <strong>' + providerEN() + '</strong> to understand site traffic. It sets cookies and records visit data only if you agree; nothing is stored until then. See our <a href="' + rel() + 'privacy.html">Privacy &amp; Cookie Policy</a>.</span>' +
          '<span data-l="ro">Folosim <strong>' + providerRO() + '</strong> pentru a înțelege traficul. Plasează cookie-uri și înregistrează date despre vizită doar dacă sunteți de acord; până atunci nu se stochează nimic. Vedeți <a href="' + rel() + 'privacy.html">Politica de confidențialitate și cookie</a>.</span>' +
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
    var depth = location.pathname.split("/").filter(Boolean).length;
    return depth > 1 ? "../" : "";
  }

  // Expose for a footer "Cookie settings" link if present.
  window.PRConsent = {
    open: function () { buildBanner(); banner.hidden = false; if (settingsLink) settingsLink.hidden = true; },
    reset: function () { try { localStorage.removeItem(KEY); } catch (e) {} }
  };

  function start() {
    matomoBootstrap();
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
