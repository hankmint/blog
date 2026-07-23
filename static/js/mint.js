/* MINT by Nana Kofi. Dark-mode toggle and gallery lightbox. No dependencies. */
(function () {
  "use strict";

  /* ---------- Dark mode ---------- */
  var root = document.documentElement;
  var toggle = document.getElementById("mint-theme-toggle");

  function isDark() {
    var t = root.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function syncLabel() {
    if (toggle) toggle.textContent = isDark() ? "Light" : "Dark";
  }
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = isDark() ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("mint-theme", next); } catch (e) {}
      syncLabel();
    });
  }
  syncLabel();

  /* ---------- Lightbox ---------- */
  var lb = document.getElementById("mint-lightbox");
  if (!lb) return;
  var lbImg = document.getElementById("mint-lb-img");
  var lbCap = document.getElementById("mint-lb-cap");
  var btnClose = lb.querySelector(".lb-close");
  var btnPrev = lb.querySelector(".lb-prev");
  var btnNext = lb.querySelector(".lb-next");
  var focusable = [btnClose, btnPrev, btnNext];
  var shots = [];
  var idx = 0;
  var lastFocus = null;

  function collect() {
    shots = Array.prototype.slice.call(document.querySelectorAll(".mint-shot"));
  }
  function open(i) {
    if (!shots.length) return;
    idx = (i + shots.length) % shots.length;
    var el = shots[idx];
    lbImg.src = el.getAttribute("data-full") || el.getAttribute("href") || "";
    lbImg.alt = el.getAttribute("data-cap") || "";
    lbCap.textContent = el.getAttribute("data-cap") || "";
    lastFocus = document.activeElement;
    lb.classList.add("on");
    lb.setAttribute("aria-hidden", "false");
    btnClose.focus();
  }
  function close() {
    lb.classList.remove("on");
    lb.setAttribute("aria-hidden", "true");
    lbImg.src = "";
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function step(d) { open(idx + d); }

  collect();
  document.addEventListener("click", function (e) {
    var shot = e.target.closest ? e.target.closest(".mint-shot") : null;
    if (shot) {
      e.preventDefault();
      if (!shots.length) collect();
      open(shots.indexOf(shot));
    }
  });
  btnClose.addEventListener("click", close);
  btnPrev.addEventListener("click", function (e) { e.stopPropagation(); step(-1); });
  btnNext.addEventListener("click", function (e) { e.stopPropagation(); step(1); });
  lb.addEventListener("click", function (e) { if (e.target === lb) close(); });
  document.addEventListener("keydown", function (e) {
    if (!lb.classList.contains("on")) return;
    if (e.key === "Escape") { close(); }
    else if (e.key === "ArrowRight") { step(1); }
    else if (e.key === "ArrowLeft") { step(-1); }
    else if (e.key === "Tab") {
      // trap focus within the three controls
      var i = focusable.indexOf(document.activeElement);
      if (i === -1) { e.preventDefault(); focusable[0].focus(); return; }
      e.preventDefault();
      var dir = e.shiftKey ? -1 : 1;
      focusable[(i + dir + focusable.length) % focusable.length].focus();
    }
  });
})();
