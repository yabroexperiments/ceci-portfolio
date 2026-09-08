/* Archive wrapper — renders a preserved IM Creator project page inside the
   v2026 nav + footer.  Injected by integrate_2026.py, replacing the wrapper
   script in Ceci's legacy-project.html export.

   Three things her export got wrong, each measured on this build:
     1. iframe src was hardcoded to https://changhsiju.xyz, making the frame
        CROSS-ORIGIN in local preview so none of the restyling could run.
        Relative paths are same-origin everywhere.
     2. the chrome-hiding selectors (nav/.navbar/.site-nav/.site-header) match
        ZERO elements in an IM Creator page — its header is div.header-box —
        so the old HOME/ABOUT bar and PREVIOUS/NEXT/Copyright block showed
        through underneath the new nav.
     3. auto-height read Math.max(documentElement.scrollHeight, ...), which is
        circular: documentElement.scrollHeight is at least the iframe's own
        height, so the frame stayed pinned at its 5200px CSS default against
        2815px of real content.  body.scrollHeight is the true content height.

   The restyle logic below is ported from her own coinful.html, which is the
   better-engineered of her two wrappers, with the local (not Google) Inter
   stylesheet so the page keeps its zero-external-request guarantee. */
(function () {
  var projects = {
    'coinful':               { title: 'Coinful Trading Platform',      path: '/coinful/' },
    'icardai':               { title: 'iCard.AI',                      path: '/icardai/' },
    'acadine_watch':         { title: 'Smart Watch Concepts',          path: '/acadine_watch/' },
    'acadine_smart-home':    { title: 'Smart Home — H5OS',             path: '/acadine_smart-home/' },
    'acadine_feature-phone': { title: 'H5OS Feature Phone',            path: '/acadine_feature-phone/' },
    'mozilla_smart-tv':      { title: 'Smart TV Tutorial',             path: '/mozilla_smart-tv/' },
    'mozilla_feature-phone': { title: 'Future Feature Phone',          path: '/mozilla_feature-phone/' },
    'mozilla_car-ui':        { title: 'Car UI Concept',                path: '/mozilla_car-ui/' },
    'htc_phone-app':         { title: 'HTC Core Apps',                 path: '/htc_phone-app/' },
    'htc_dot-view':          { title: 'HTC Dot View',                  path: '/htc_dot-view/' },
    'htc_cos-wallpaper':     { title: 'HTC COS Wallpaper',             path: '/htc_cos-wallpaper/' },
    'htc_message':           { title: 'HTC Message Themes',            path: '/htc_message/' },
    'htc_clock':             { title: 'Clock & Calculator Widgets',    path: '/htc_clock/' },
    'htc_scribble':          { title: 'HTC Scribble',                  path: '/htc_scribble/' },
    'htc_lifeme':            { title: 'HTC Life.me',                   path: '/htc_lifeme/' },
    'htc_mini':              { title: 'HTC Mini',                      path: '/htc_mini/' },
    'htc_tablet':            { title: 'HTC Tablet',                    path: '/htc_tablet/' }
  };

  var key = new URLSearchParams(location.search).get('project');
  var p = projects[key] || projects.coinful;
  document.title = p.title + ' — Ceci Chang';

  var f = document.getElementById('legacyFrame');
  if (!f) return;
  f.setAttribute('title', p.title);
  f.src = p.path;

  function restyle() {
    var d;
    try { d = f.contentDocument || f.contentWindow.document; } catch (e) { return; }
    if (!d || !d.body) return;

    if (!d.querySelector('link[data-portfolio-inter]')) {
      var font = d.createElement('link');
      font.rel = 'stylesheet';
      font.href = '/assets/fonts/inter/inter.css';   /* self-hosted: no external request */
      font.setAttribute('data-portfolio-inter', '');
      d.head.appendChild(font);
    }

    if (!d.querySelector('style[data-portfolio-style]')) {
      var style = d.createElement('style');
      style.setAttribute('data-portfolio-style', '');
      style.textContent =
        'html,body{margin:0!important;padding:0!important;background:#fff!important;' +
        'overflow-x:hidden!important;overflow-y:hidden!important;' +
        'font-family:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;' +
        '-webkit-font-smoothing:antialiased!important}' +
        'body,body *:not(svg):not(path){font-family:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important}' +
        'h1,h2,h3,h4,h5,h6{font-weight:600!important;letter-spacing:-.02em!important}' +
        'p,li,span,a{font-weight:400!important}' +
        /* IM Creator page chrome: .header-box/.header-wrapper is its nav; there
           is no <nav> or <footer> element on these pages at all. */
        'header,nav,footer,.header-box,.header-wrapper{display:none!important}';
      d.head.appendChild(style);
    }

    /* Hide the archive page's own "PREVIOUS / NEXT / Copyright" strip.
       This is the part of her coinful.html logic that does not generalise, and
       it blanked three pages before this rewrite. Two failure modes, both
       measured on this build:
         a) the matcher tested textContent, so on a sparse, image-led page
            (acadine_watch, mozilla_smart-tv, mozilla_car-ui) the element whose
            text is "PREVIOUS NEXT Copyright..." under 180 chars is the ENTIRE
            div.xprs-holder — the whole page matched;
         b) the ancestor walk then hid it, and the "does it contain an <img>"
            guard could not save it because IM Creator renders those pages with
            CSS background-image, not <img>.
       So: refuse anything taller than a strip can plausibly be, never touch a
       known page container, and hide the OUTERMOST surviving match. Height is
       the honest signal here — a footer strip is short, a page is not. */
    var NEVER_HIDE = '.xprs-holder,.main-page,.light-box-wrapper,#content,.container,body,html';
    var STRIP_MAX_H = 400;
    var isStrip = function (el) {
      if (el.matches && el.matches(NEVER_HIDE)) return false;
      var h = el.getBoundingClientRect().height;
      return h > 0 && h <= STRIP_MAX_H;
    };

    /* The pager reads "PREVIOUS NEXT" mid-sequence but "PREVIOUS HOME" on the
       last page (htc_tablet), so match any combination of those words — but
       require at least TWO of them: a lone "HOME" is real content on
       mozilla_car-ui, whose screens are literally labelled HOME / Dashboard /
       Climate. */
    var RE_PAGER = /^(PREVIOUS|NEXT|HOME)(\s+(PREVIOUS|NEXT|HOME))+$/i;
    var RE_STRIP = [/NEXT PROJECT/i, RE_PAGER, /Copyright\s*©?\s*\d{4}\s*Ceci Chang/i];
    var matched = Array.prototype.filter.call(d.querySelectorAll('body *'), function (el) {
      var txt = (el.textContent || '').replace(/\s+/g, ' ').trim();
      if (!txt || txt.length >= 180) return false;
      return RE_STRIP.some(function (re) { return re.test(txt); });
    });

    /* Hide the OUTERMOST band that is still small enough to be chrome, not the
       leaf. Hiding only the leaf (the first version) removed the words but left
       the band's own container standing — its height and background survived,
       so every wrapped page carried ~330px of dead space above our footer
       (a 68px pager band, visibly BLUE on htc_dot-view, plus a 262px copyright
       band). It passed an innerText check because innerText excludes hidden
       descendants: the words were gone, the box was not.
       The <=400px ceiling is what makes going outermost safe — on a sparse,
       image-led page the whole document also matches the text test, but it is
       thousands of pixels tall and is refused. */
    var candidates = matched.filter(function (el) {
      return isStrip(el) && el.offsetHeight > 0;
    });
    candidates
      .filter(function (el) {
        return !candidates.some(function (o) { return o !== el && o.contains(el); });
      })
      .forEach(function (el) { el.style.setProperty('display', 'none', 'important'); });

    var resize = function () {
      d.documentElement.style.height = 'auto';
      d.body.style.height = 'auto';
      /* body.scrollHeight ONLY — documentElement.scrollHeight is floored by the
         iframe's own height, which makes the measurement circular. */
      var h = Math.ceil(Math.max(
        d.body.scrollHeight,
        d.body.getBoundingClientRect().height,
        /* last resort: the tallest visible top-level block */
        Array.prototype.reduce.call(d.body.children, function (m, e) {
          return Math.max(m, e.getBoundingClientRect().bottom);
        }, 0)));
      /* A zero/absurd reading must never collapse the page to nothing — better a
         little extra white space than a blank archive entry. */
      if (h > 200) f.style.height = h + 'px';
    };
    resize();
    [100, 300, 700, 1400, 2600].forEach(function (ms) { setTimeout(resize, ms); });
    if ('MutationObserver' in window) {
      new MutationObserver(function () { setTimeout(resize, 0); })
        .observe(d.body, { subtree: true, childList: true, attributes: true });
    }
    Array.prototype.forEach.call(d.images, function (img) {
      if (!img.complete) img.addEventListener('load', resize, { once: true });
    });
    if (d.fonts && d.fonts.ready) d.fonts.ready.then(resize);
  }

  f.addEventListener('load', restyle);
})();
