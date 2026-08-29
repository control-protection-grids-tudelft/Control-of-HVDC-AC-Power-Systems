/**
 * components.js — shared layout injection + card templates
 *
 * Header and footer are embedded as template strings (no fetch, no CORS).
 * Card grids are rendered from inline JSON via data-component attributes.
 */

(function () {
  "use strict";

  /* ------------------------------------------------------------------ */
  /*  Base-path helper                                                   */
  /* ------------------------------------------------------------------ */

  function getBasePath() {
    var parts = location.pathname.replace(/\/+$/, "").split("/").filter(Boolean);
    parts.pop(); // remove filename
    var depth = 0;
    var knownDirs = ["team", "projects", "publications", "portfolio", "news"];
    for (var i = parts.length - 1; i >= 0; i--) {
      if (knownDirs.indexOf(parts[i]) !== -1) {
        depth++;
      } else {
        break;
      }
    }
    return depth === 0 ? "./" : "../".repeat(depth);
  }

  var B = getBasePath();

  /* ------------------------------------------------------------------ */
  /*  Shared fragments (edit header / footer here)                      */
  /* ------------------------------------------------------------------ */

  var HEADER = '<a class="skip-link" href="#main-content">Skip to content</a>' +
    '<header class="site-header">' +
      '<div class="wrap nav-inner">' +
        '<a class="logo" href="' + B + 'index.html">Control of HVDC/AC Power Systems<span>TU Delft · IEPG</span></a>' +
        '<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>' +
        '<ul class="site-nav" id="site-nav">' +
          '<li><a href="' + B + 'index.html">Home</a></li>' +
          '<li><a href="' + B + 'team/index.html">Team</a></li>' +
          '<li><a href="' + B + 'projects/index.html">Projects</a></li>' +
          '<li><a href="' + B + 'publications/index.html">Publications</a></li>' +
          '<li><a href="' + B + 'portfolio/index.html">Portfolio</a></li>' +
          '<li><a href="' + B + 'contact.html">Contact</a></li>' +
        '</ul>' +
      '</div>' +
    '</header>';

  var FOOTER =
    '<footer class="site-footer">' +
      '<div class="wrap footer-grid">' +
        '<div>' +
          '<div class="brand-font">Control of HVDC/AC Power Systems</div>' +
          'Intelligent Electrical Power Grids · Electrical Sustainable Energy · TU Delft' +
        '</div>' +
        '<div>' +
          '<h3>Explore</h3>' +
          '<ul>' +
            '<li><a href="' + B + 'team/index.html">Team</a></li>' +
            '<li><a href="' + B + 'projects/index.html">Projects</a></li>' +
            '<li><a href="' + B + 'publications/index.html">Publications</a></li>' +
            '<li><a href="' + B + 'teaching.html">Teaching &amp; education</a></li>' +
            '<li><a href="' + B + 'portfolio/index.html">Open-source portfolio</a></li>' +
            '<li><a href="' + B + 'news/index.html">News</a></li>' +
          '</ul>' +
        '</div>' +
        '<div>' +
          '<h3>Contact</h3>' +
          '<ul>' +
            '<li><a href="mailto:A.Lekic@tudelft.nl">A.Lekic@tudelft.nl</a></li>' +
            '<li>+31 15 27 82461</li>' +
            '<li>Room 36.LB 03.210</li>' +
            '<li><a href="https://github.com/control-protection-grids-tudelft" target="_blank" rel="noopener">GitHub org</a></li>' +
          '</ul>' +
        '</div>' +
      '</div>' +
    '</footer>';

  /* ------------------------------------------------------------------ */
  /*  Inject header + footer                                            */
  /* ------------------------------------------------------------------ */

  function injectShell() {
    var h = document.getElementById("site-header");
    var f = document.getElementById("site-footer");
    if (h) h.outerHTML = HEADER;
    if (f) f.outerHTML = FOOTER;
  }

  /* ------------------------------------------------------------------ */
  /*  Nav: set aria-current and mobile toggle                           */
  /* ------------------------------------------------------------------ */

  function activateNav() {
    var path = location.pathname;
    var links = document.querySelectorAll(".site-nav a");

    links.forEach(function (a) {
      var href = a.getAttribute("href");
      var hrefTail = href.replace(/^(\.\.\/)+/, "").replace(/^\.\//, "");
      var pathTail = path.replace(/.*?\/(?=(team|projects|publications|portfolio|news|index\.html|contact\.html|teaching\.html|awards\.html))/, "");
      pathTail = pathTail.replace(/^\//, "");

      if (pathTail === hrefTail ||
          (hrefTail.indexOf("/index.html") !== -1 && pathTail.indexOf(hrefTail.split("/")[0] + "/") === 0)) {
        a.setAttribute("aria-current", "page");
      }
    });

    var toggle = document.querySelector(".nav-toggle");
    var nav = document.querySelector("#site-nav");
    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        var open = nav.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }
  }

  /* ------------------------------------------------------------------ */
  /*  Card templates                                                    */
  /* ------------------------------------------------------------------ */

  function escapeHtml(str) {
    if (!str) return "";
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function resolveUrl(url) {
    if (!url) return "";
    if (/^(https?:\/\/|#|mailto:)/.test(url)) return url;
    // Strip any leading ./ or ../ — paths should be root-relative in JSON
    var clean = url.replace(/^(\.\.\/)+/, "").replace(/^\.\//, "");
    return B + clean;
  }

  function personCard(d) {
    var subtitle = escapeHtml(d.role || "");
    if (d.project) subtitle += (subtitle ? " · " : "") + escapeHtml(d.project);
    return '<a class="card person-card" href="' + resolveUrl(d.url) + '">' +
      '<div class="card-media">' +
        '<img src="' + resolveUrl(d.photo) + '" alt="' + escapeHtml(d.name) + '" />' +
      '</div>' +
      '<div class="card-body">' +
        '<h3>' + escapeHtml(d.name) + '</h3>' +
        '<p>' + subtitle + '</p>' +
        '<span class="more">See Profile →</span>' +
      '</div>' +
    '</a>';
  }

  function projectCard(d) {
    var mediaClass = d.logoCard !== false ? "card-media logo-card" : "card-media";
    return '<a class="card" href="' + resolveUrl(d.url) + '">' +
      '<div class="' + mediaClass + '">' +
        '<img src="' + resolveUrl(d.image) + '" alt="' + escapeHtml(d.name) + '" />' +
      '</div>' +
      '<div class="card-body">' +
        '<div class="tag">' + escapeHtml(d.tag || d.period || "") + '</div>' +
        '<h3>' + escapeHtml(d.name) + '</h3>' +
        '<p>' + escapeHtml(d.summary || "") + '</p>' +
        '<span class="more">Learn more →</span>' +
      '</div>' +
    '</a>';
  }

  function portfolioCard(d) {
    var tagLine = escapeHtml(d.tag || "");
    var meta = d.maturity ? '<div class="card-maturity">' + escapeHtml(d.maturity) + '</div>' : "";
    return '<a class="card" href="' + resolveUrl(d.url) + '">' +
      '<div class="card-media">' +
        '<img src="' + resolveUrl(d.image) + '" alt="' + escapeHtml(d.name) + '" />' +
      '</div>' +
      '<div class="card-body">' +
        '<div class="tag">' + tagLine + '</div>' +
        '<h3>' + escapeHtml(d.name) + '</h3>' +
        '<p>' + escapeHtml(d.summary || "") + '</p>' +
        meta +
        '<span class="more">Learn more →</span>' +
      '</div>' +
    '</a>';
  }

  /* ------------------------------------------------------------------ */
  /*  Card renderer                                                     */
  /* ------------------------------------------------------------------ */

  var renderers = {
    "person-cards": personCard,
    "project-cards": projectCard,
    "portfolio-cards": portfolioCard
  };

  function renderCards() {
    Object.keys(renderers).forEach(function (key) {
      var containers = document.querySelectorAll('[data-component="' + key + '"]');
      containers.forEach(function (container) {
        var script = container.querySelector('script[type="application/json"]');
        if (!script) return;
        try {
          var data = JSON.parse(script.textContent);
          var html = data.map(renderers[key]).join("\n");
          script.remove();
          container.insertAdjacentHTML("afterbegin", html);
        } catch (e) {
          console.error("Card render error (" + key + "):", e);
        }
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /*  Section nav — auto-generated from headings with IDs               */
  /* ------------------------------------------------------------------ */

  function buildSectionNav() {
    var nav = document.getElementById("section-nav");
    if (!nav) return;

    // Collect sections: either from <section id="..."> with an h2 inside,
    // or from h2.year-heading[id] (publications)
    var items = [];

    // Mode 1: page sections (homepage, team, portfolio)
    var sections = document.querySelectorAll("section[id]");
    sections.forEach(function (sec) {
      // Use the sec-label or h2 text as the label
      var label = sec.querySelector(".sec-label");
      var h2 = sec.querySelector("h2");
      var text = label ? label.textContent : (h2 ? h2.textContent : "");
      if (text && sec.id && sec.id !== "main-content") {
        items.push({ id: sec.id, text: text.trim() });
      }
    });

    // Mode 2: year headings (publications) — only if no section items found
    if (items.length === 0) {
      var yearHeadings = document.querySelectorAll("h2[id]");
      yearHeadings.forEach(function (h2) {
        items.push({ id: h2.id, text: h2.textContent.trim() });
      });
    }

    if (items.length < 2) {
      nav.remove();
      return;
    }

    var html = items.map(function (item) {
      return '<a href="#' + item.id + '">' + item.text + '</a>';
    }).join("");
    nav.innerHTML = html;

    // If a hero-cta exists, hide section-nav until hero-cta scrolls off-screen
    var heroCta = document.getElementById("hero-cta");
    if (heroCta && "IntersectionObserver" in window) {
      nav.classList.add("section-nav-hidden");
      var observer = new IntersectionObserver(function (entries) {
        nav.classList.toggle("section-nav-hidden", entries[0].isIntersecting);
      }, { threshold: 0 });
      observer.observe(heroCta);
    }

    // Scroll-spy: highlight the nearest section
    var links = nav.querySelectorAll("a");
    var targets = items.map(function (item) {
      return document.getElementById(item.id);
    });

    function onScroll() {
      var offset = window.scrollY + parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-h')) + 60;
      var current = 0;

      // If at bottom of page, highlight the last item
      var atBottom = (window.innerHeight + window.scrollY) >= (document.body.scrollHeight - 10);
      if (atBottom) {
        current = targets.length - 1;
      } else {
        for (var i = targets.length - 1; i >= 0; i--) {
          if (targets[i] && targets[i].offsetTop <= offset) {
            current = i;
            break;
          }
        }
      }
      links.forEach(function (a, idx) {
        a.classList.toggle("active", idx === current);
      });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ------------------------------------------------------------------ */
  /*  Boot                                                              */
  /* ------------------------------------------------------------------ */

  document.addEventListener("DOMContentLoaded", function () {
    injectShell();
    activateNav();
    renderCards();
    buildSectionNav();
    document.body.classList.add("components-loaded");
  });

})();
