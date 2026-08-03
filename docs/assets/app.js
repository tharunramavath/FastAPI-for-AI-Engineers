/* FastAPI for AI Engineers — site behavior */
(function () {
  "use strict";

  var PAGES = {
    learning: { md: "LEARNING_PATH.md", title: "Learning Path", toc: "toc-learning", body: "learning-body" },
    concepts: { md: "CONCEPTS.md",        title: "Core Concepts", toc: "toc-concepts", body: "concepts-body" },
    map:      { md: "MAP.md",             title: "Project Map",   toc: "toc-map",      body: "map-body" }
  };

  var cache = {};
  var current = "home";
  var sections = {};     // page -> array of h2 elements
  var sidebar, progress, topBtn, searchEl;

  function $(s, r) { return (r || document).querySelector(s); }
  function $all(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  document.addEventListener("DOMContentLoaded", function () {
    sidebar = $("#sidebar");
    progress = $("#progress");
    topBtn = $("#to-top");
    searchEl = $("#search");

    $all("#nav .nav-item, a[data-page-link]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var page = btn.getAttribute("data-page") || btn.getAttribute("data-page-link");
        if (page) { navigate(page); closeSidebar(); }
      });
    });

    $("#nav-toggle").addEventListener("click", function () {
      var open = sidebar.classList.toggle("open");
      this.setAttribute("aria-expanded", open ? "true" : "false");
      $("#backdrop").classList.toggle("show", open);
    });
    $("#backdrop").addEventListener("click", closeSidebar);

    // clicking a parent opens its sub-TOC accordion
    $all(".nav-parent").forEach(function (n) {
      n.addEventListener("click", function () {
        var page = n.getAttribute("data-page");
        if (PAGES[page]) {
          var toc = $("#" + PAGES[page].toc);
          var open = toc.classList.toggle("open");
          n.classList.toggle("open", open || true);
        }
      });
    });

    var m = (location.hash || "").match(/page=(home|learning|concepts|map)/);
    navigate(m ? m[1] : "home");

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    topBtn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });

    document.addEventListener("keydown", function (e) {
      var tag = (document.activeElement && document.activeElement.tagName || "").toLowerCase();
      if (e.key === "/" && !/^(input|textarea)$/.test(tag)) { e.preventDefault(); searchEl.focus(); }
    });

    searchEl.addEventListener("input", filterToc);
  });

  function closeSidebar() {
    sidebar.classList.remove("open");
    var t = $("#nav-toggle"); if (t) t.setAttribute("aria-expanded", "false");
    var b = $("#backdrop"); if (b) b.classList.remove("show");
  }

  function navigate(page) {
    current = page;
    $all(".page").forEach(function (p) { p.hidden = true; });
    var el = page === "home" ? $("#page-home") : $("#page-" + page);
    if (!el) return;
    el.hidden = false;
    window.scrollTo(0, 0);

    $all("#nav .nav-item").forEach(function (n) {
      n.classList.toggle("active", n.getAttribute("data-page") === page);
    });
    $("#page-crumb").textContent = page === "home" ? "Home" : (PAGES[page] ? PAGES[page].title : page);

    if (page !== "home") {
      var parent = $(".nav-parent[data-page='" + page + "']");
      if (parent) parent.classList.add("open");
      $("#" + PAGES[page].toc).classList.add("open");
      loadDoc(page);
    } else {
      sections = {};
      $all(".toc a").forEach(function (a) { a.classList.remove("active"); });
    }
    onScroll();
  }

  function loadDoc(page) {
    var cfg = PAGES[page];
    var target = $("#" + cfg.body);
    var render = function (text) {
      target.innerHTML = '<article class="prose"></article>';
      var art = $("article", target);
      art.innerHTML = marked.parse(text, { gfm: true });

      // overflow-safe tables
      $all("table", art).forEach(function (t) {
        var w = document.createElement("div"); w.className = "table-wrap";
        t.parentNode.insertBefore(w, t); w.appendChild(t);
      });

      // heading anchors
      $all("h1,h2,h3,h4", art).forEach(function (h, i) { h.id = "s-" + page + "-" + i; });

      // sidebar sub-navigation = h2 headings
      var h2 = $all("h2", art);
      $("#" + cfg.toc).innerHTML = h2.map(function (h) {
        return '<li><a class="pl" href="#' + h.id + '">' + h.textContent + "</a></li>";
      }).join("");
      sections[page] = h2;

      highlightCode();
      addCopyButtons();
    };
    if (cache[page]) { render(cache[page]); return; }
    fetch(cfg.md, { headers: { Accept: "text/plain" } })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.text(); })
      .then(function (t) { cache[page] = t; render(t); })
      .catch(function () {
        target.innerHTML = "<div class='prose'><h2>Could not load " + cfg.md + "</h2>" +
          "<p>This GitHub Pages site is published from the <code>docs/</code> folder. " +
          "Run: Settings → Pages → Source → <code>GitHub Actions</code>.</p></div>";
      });
  }

  function highlightCode() {
    if (window.hljs) $all("pre code").forEach(function (b) {
      try { hljs.highlightElement(b); } catch (e) {}
    });
  }

  function addCopyButtons() {
    $all("pre code").forEach(function (code) {
      var pre = code.parentNode;
      if (pre.querySelector(".copy")) return;
      var btn = document.createElement("button");
      btn.className = "copy"; btn.textContent = "Copy";
      btn.addEventListener("click", function () {
        var text = code.innerText;
        var done = function () { btn.textContent = "Copied ✔"; setTimeout(function () { btn.textContent = "Copy"; }, 1400); };
        if (navigator.clipboard) navigator.clipboard.writeText(text).then(done);
        else { var ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); ta.remove(); done(); }
      });
      pre.appendChild(btn);
    });
  }

  function onScroll() {
    var y = window.scrollY;
    var h = document.documentElement.scrollHeight - window.innerHeight;
    progress.style.width = (h > 0 ? (y / h) * 100 : 0) + "%";
    topBtn.classList.toggle("show", y > 220);
    if (current !== "home" && sections[current]) spy(current, y + 130);
  }

  function spy(page, offset) {
    var els = sections[page] || [];
    if (!els.length) return;
    var activeId = null;
    for (var i = 0; i < els.length; i++) {
      var top = els[i].getBoundingClientRect().top + window.scrollY;
      if (top <= offset) activeId = els[i].id;
    }
    $all("#" + PAGES[page].toc + " a").forEach(function (a) {
      a.classList.toggle("active", activeId !== null && a.getAttribute("href") === "#" + activeId);
    });
  }

  function filterToc() {
    var q = searchEl.value.trim().toLowerCase();
    $all(".toc a").forEach(function (a) {
      var show = !q || a.textContent.toLowerCase().indexOf(q) !== -1;
      a.style.display = show ? "" : "none";
    });
  }
})();