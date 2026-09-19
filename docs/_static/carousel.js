/* The rotating screenshot panel written by the `carousel` directive.
 *
 * Each panel carries its records as JSON.  The next picture is loaded while
 * the current one is showing, so the change is a fade rather than a gap, and
 * a picture that fails to load is dropped from the rotation instead of
 * leaving the panel blank.
 */
(function () {
  'use strict';

  function preload(url) {
    return new Promise(function (resolve, reject) {
      var img = new Image();
      img.onload = function () { resolve(img); };
      img.onerror = function () { reject(url); };
      img.src = url;
    });
  }

  function start(panel) {
    var holder = panel.querySelector('script.carousel-records');
    if (!holder) { return; }
    var records;
    try {
      records = JSON.parse(holder.textContent);
    } catch (err) {
      return;
    }
    if (!records.length) { return; }

    var frame = panel.querySelector('.carousel-frame');
    var caption = panel.querySelector('.carousel-caption');
    var noscript = panel.querySelector('noscript');
    if (noscript) { noscript.remove(); }

    var interval = parseInt(panel.dataset.interval, 10) || 5000;
    var index = -1;
    var timer = null;

    function step(delta) {
      if (!records.length) { return Promise.resolve(); }
      index = (index + delta + records.length) % records.length;
      var record = records[index];
      return preload(record.url).then(function (img) {
        img.alt = record.description || '';
        img.className = 'carousel-image';
        frame.replaceChildren(img);
        // Force the transition to run on the freshly inserted element.
        requestAnimationFrame(function () { img.classList.add('shown'); });
        caption.replaceChildren(captionFor(record));
        if (records.length > 1) {
          preload(records[(index + 1) % records.length].url).catch(function () {});
        }
      }, function () {
        // A picture that will not load is not worth trying again.
        records.splice(index, 1);
        index -= 1;
        return step(delta);
      });
    }

    function captionFor(record) {
      var text = record.description || '';
      if (record.link) {
        var anchor = document.createElement('a');
        anchor.href = record.link;
        anchor.textContent = text;
        anchor.rel = 'noopener';
        return anchor;
      }
      return document.createTextNode(text);
    }

    function advance() {
      step(1);
    }

    function resume() {
      if (timer === null && records.length > 1) {
        timer = window.setInterval(advance, interval);
      }
    }

    function pause() {
      if (timer !== null) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    panel.addEventListener('mouseenter', pause);
    panel.addEventListener('mouseleave', resume);
    panel.addEventListener('focusin', pause);
    panel.addEventListener('focusout', resume);
    frame.addEventListener('click', function () { pause(); advance(); resume(); });

    // A reader who has asked for less motion gets the pictures without the
    // rotation; the panel still advances when they click it.
    var still = window.matchMedia('(prefers-reduced-motion: reduce)');
    step(1).then(function () {
      if (!still.matches) { resume(); }
    });
    still.addEventListener('change', function (event) {
      if (event.matches) { pause(); } else { resume(); }
    });

    // Rotating a panel nobody is looking at burns a timer and, on a long
    // page, bandwidth.
    if (typeof IntersectionObserver !== 'undefined') {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !still.matches) { resume(); } else { pause(); }
        });
      }).observe(panel);
    }
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { pause(); } else if (!still.matches) { resume(); }
    });
  }

  function init() {
    document.querySelectorAll('.pyopengl-carousel').forEach(start);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
