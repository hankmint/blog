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
    if (location.pathname.indexOf("/admin") === 0) {
      // Never let the worker control the editor. The editor signs in through a
      // popup that posts a message back to this page, and a service worker in
      // the middle of that handoff is exactly how you get a blank screen that
      // only fixes itself on refresh. Unregister any worker that already
      // claimed this page from an earlier visit.
      navigator.serviceWorker.getRegistrations().then(function (rs) {
        rs.forEach(function (r) { r.unregister(); });
      }).catch(function () {});
    } else {
      window.addEventListener("load", function () {
        navigator.serviceWorker.register("/sw.js").catch(function () {});
      });
    }
  }



  /* Share: one icon, a popover, a copy button.
     Where the browser has a native share sheet the icon opens that instead —
     it reaches every app the reader has, which two hard-coded networks cannot.
     Falls back to the popover everywhere else, including desktop. */
  var shareBtn = document.querySelector(".mint-share-btn");
  var sharePop = document.querySelector(".mint-share-pop");
  var copyBtn = document.querySelector(".mint-share-copy");

  function flash(btn, word) {
    var was = btn.textContent;
    btn.textContent = word;
    btn.classList.add("copied");
    setTimeout(function () {
      btn.textContent = was;
      btn.classList.remove("copied");
    }, 1600);
  }

  function copyText(text, btn) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { flash(btn, "Copied"); },
                                               function () { flash(btn, "Press \u2318C"); });
      return;
    }
    // Older Safari, and anything not on https.
    var t = document.createElement("textarea");
    t.value = text;
    t.setAttribute("readonly", "");
    t.style.cssText = "position:absolute;left:-9999px";
    document.body.appendChild(t);
    t.select();
    try { document.execCommand("copy"); flash(btn, "Copied"); } catch (e) { flash(btn, "Press \u2318C"); }
    document.body.removeChild(t);
  }

  if (shareBtn && sharePop) {
    shareBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      if (navigator.share) {
        navigator.share({ title: shareBtn.dataset.title, url: shareBtn.dataset.url })
          .catch(function () {});
        return;
      }
      var open = !sharePop.hidden;
      sharePop.hidden = open;
      shareBtn.setAttribute("aria-expanded", String(!open));
      if (!open) {
        var f = sharePop.querySelector(".mint-share-url");
        if (f) { f.focus(); f.select(); }
      }
    });
    // Click away, or Escape, closes it.
    document.addEventListener("click", function (e) {
      if (!sharePop.hidden && !sharePop.contains(e.target) && e.target !== shareBtn) {
        sharePop.hidden = true;
        shareBtn.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !sharePop.hidden) {
        sharePop.hidden = true;
        shareBtn.setAttribute("aria-expanded", "false");
        shareBtn.focus();
      }
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener("click", function () { copyText(copyBtn.dataset.url, copyBtn); });
  }


  /* ---------- Gallery carousels and lightbox ----------
     The gallery has rendered arrows, dots and a "1/2" counter since it was
     built, and nothing ever wired them up. They looked like controls and did
     nothing, and on a tile whose first photograph had not loaded you saw a
     counter floating over blank space. */
  var shots = document.querySelectorAll(".mint-shot.mint-set");
  Array.prototype.forEach.call(shots, function (shot) {
    var slides = shot.querySelectorAll(".mint-slide");
    var dots = shot.querySelectorAll(".mint-dot");
    var count = shot.querySelector(".mint-count");
    var n = slides.length;
    if (n < 2) return;
    var at = 0;

    function show(i) {
      at = (i + n) % n;
      Array.prototype.forEach.call(slides, function (s, k) {
        s.classList.toggle("is-on", k === at);
      });
      Array.prototype.forEach.call(dots, function (d, k) {
        d.classList.toggle("is-on", k === at);
        d.setAttribute("aria-selected", k === at ? "true" : "false");
      });
      if (count) count.textContent = at + 1 + "/" + n;
    }

    var prev = shot.querySelector(".mint-prev");
    var next = shot.querySelector(".mint-next");
    if (prev) prev.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); show(at - 1); });
    if (next) next.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); show(at + 1); });
    Array.prototype.forEach.call(dots, function (d, k) {
      d.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); show(k); });
    });

    /* A phone has no arrows to hover. */
    var x0 = null;
    shot.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    shot.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 40) show(at + (dx < 0 ? 1 : -1));
      x0 = null;
    }, { passive: true });

    shot.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); show(at + 1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); show(at - 1); }
    });
  });

  /* The tiles have said cursor: zoom-in from the beginning. Now they zoom. */
  var box = null;
  function lightbox(src, cap) {
    if (!box) {
      box = document.createElement("div");
      box.className = "mint-lightbox";
      box.setAttribute("role", "dialog");
      box.setAttribute("aria-modal", "true");
      box.innerHTML = '<button type="button" class="mint-lightbox-close" aria-label="Close">&times;</button>' +
                      '<img alt="" /><figcaption></figcaption>';
      document.body.appendChild(box);
      box.addEventListener("click", function (e) {
        if (e.target === box || e.target.classList.contains("mint-lightbox-close")) close();
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && box.classList.contains("is-on")) close();
      });
    }
    box.querySelector("img").src = src;
    box.querySelector("figcaption").textContent = cap || "";
    box.classList.add("is-on");
    document.body.style.overflow = "hidden";
  }
  function close() {
    if (!box) return;
    box.classList.remove("is-on");
    box.querySelector("img").removeAttribute("src");
    document.body.style.overflow = "";
  }
  document.addEventListener("click", function (e) {
    var img = e.target.closest && e.target.closest(".mint-slide");
    if (!img) return;
    e.preventDefault();
    lightbox(img.dataset.full || img.src, img.dataset.cap);
  });

})();
