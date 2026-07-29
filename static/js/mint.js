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


  /* ---------- Install as an app ----------
     Registers the service worker so the blog can be added to a phone home
     screen and survives a dropped connection. Silent if unsupported. */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () {});
    });
  }

  /* ---------- Gallery carousels ----------
     A post with several photographs gets one tile with arrows and dots rather
     than one tile per photograph, which keeps the grid calm. */
  Array.prototype.forEach.call(document.querySelectorAll(".mint-set"), function (set) {
    var slides = set.querySelectorAll(".mint-slide");
    var dots = set.querySelectorAll(".mint-dot");
    var counter = set.querySelector(".mint-count");
    var prev = set.querySelector(".mint-prev");
    var next = set.querySelector(".mint-next");
    var at = 0;

    function show(i) {
      at = (i + slides.length) % slides.length;
      for (var k = 0; k < slides.length; k++) {
        slides[k].classList.toggle("is-on", k === at);
        if (dots[k]) {
          dots[k].classList.toggle("is-on", k === at);
          dots[k].setAttribute("aria-selected", k === at ? "true" : "false");
        }
      }
      if (counter) counter.textContent = (at + 1) + "/" + slides.length;
    }

    if (prev) prev.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); show(at - 1); });
    if (next) next.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); show(at + 1); });
    Array.prototype.forEach.call(dots, function (dot, i) {
      dot.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); show(i); });
    });

    /* Swipe, because this is mostly read on a phone. */
    var x0 = null;
    set.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    set.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 40) show(at + (dx < 0 ? 1 : -1));
      x0 = null;
    }, { passive: true });

    /* Arrow keys when the tile has focus, but not while the lightbox is open. */
    set.addEventListener("keydown", function (e) {
      var open = document.getElementById("mint-lightbox");
      if (open && open.classList.contains("on")) return;
      if (e.key === "ArrowRight") { e.preventDefault(); show(at + 1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); show(at - 1); }
    });

    /* The covering slides are lazy so 30-odd photographs do not all download at
       once. The moment a tile is touched, hovered or focused, load the rest of
       its set so advancing never waits on the network. */
    var warmed = false;
    function warm() {
      if (warmed) return;
      warmed = true;
      for (var k = 1; k < slides.length; k++) slides[k].loading = "eager";
    }
    set.addEventListener("pointerenter", warm);
    set.addEventListener("focusin", warm);
    set.addEventListener("touchstart", warm, { passive: true });

    set.setAttribute("tabindex", "0");
    show(0);
  });

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
    // Every photograph in the grid, in reading order, including the ones
    // currently hidden inside a carousel.
    shots = Array.prototype.slice.call(document.querySelectorAll(".mint-gallery [data-full]"));
  }
  function open(i) {
    if (!shots.length) return;
    idx = (i + shots.length) % shots.length;
    var el = shots[idx];
    lbImg.src = el.getAttribute("data-full") || "";
    lbImg.alt = el.getAttribute("data-cap") || "";
    var cap = el.getAttribute("data-cap") || "";
    var href = el.getAttribute("data-href");
    lbCap.textContent = "";
    lbCap.appendChild(document.createTextNode(cap));
    if (href) {
      var a = document.createElement("a");
      a.href = href;
      a.className = "lb-post";
      a.textContent = "Read the post";
      lbCap.appendChild(document.createTextNode("  "));
      lbCap.appendChild(a);
    }
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
    // Only the photograph opens the lightbox. Arrows, dots and the caption link
    // are controls and must not.
    if (!e.target.classList || !e.target.classList.contains("mint-slide")) return;
    e.preventDefault();
    if (!shots.length) collect();
    var i = shots.indexOf(e.target);
    if (i !== -1) open(i);
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
