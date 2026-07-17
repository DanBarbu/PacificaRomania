// PacificaRomania — click any essay image to view the full, uncropped picture.
(function () {
  function init() {
    var imgs = document.querySelectorAll(".essay-lead img, .essay-body img");
    if (!imgs.length) return;

    var overlay = document.createElement("div");
    overlay.className = "lightbox-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Image viewer / Vizualizare imagine");
    var close = document.createElement("button");
    close.className = "lightbox-close";
    close.setAttribute("aria-label", "Close / Închide");
    close.innerHTML = "&times;";
    var big = document.createElement("img");
    big.alt = "";
    overlay.appendChild(close);
    overlay.appendChild(big);
    document.body.appendChild(overlay);

    function open(src, alt) {
      big.src = src;
      big.alt = alt || "";
      overlay.classList.add("open");
      document.body.style.overflow = "hidden";
    }
    function hide() {
      overlay.classList.remove("open");
      document.body.style.overflow = "";
      big.src = "";
    }

    for (var i = 0; i < imgs.length; i++) {
      imgs[i].addEventListener("click", function () {
        open(this.currentSrc || this.src, this.alt);
      });
    }
    overlay.addEventListener("click", hide);
    close.addEventListener("click", hide);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && overlay.classList.contains("open")) hide();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
