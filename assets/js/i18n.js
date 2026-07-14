// PacificaRomania — EN/RO language toggle.
// Choice persists across pages via localStorage. Default: English.
(function () {
  var KEY = "pr-lang";
  function get() { try { return localStorage.getItem(KEY) || "en"; } catch (e) { return "en"; } }
  function set(l) { try { localStorage.setItem(KEY, l); } catch (e) {} }

  function apply(l) {
    var root = document.documentElement;
    root.classList.toggle("lang-ro", l === "ro");
    root.setAttribute("lang", l);
    var btns = document.querySelectorAll("[data-setlang]");
    for (var i = 0; i < btns.length; i++) {
      btns[i].classList.toggle("active", btns[i].getAttribute("data-setlang") === l);
      btns[i].setAttribute("aria-pressed", btns[i].getAttribute("data-setlang") === l ? "true" : "false");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    apply(get());
    var btns = document.querySelectorAll("[data-setlang]");
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener("click", function () {
        var l = this.getAttribute("data-setlang");
        set(l);
        apply(l);
      });
    }
  });
})();
