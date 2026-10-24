/* The rotating screenshot panel written by the `carousel` directive.
 *
 * Each panel carries its records as JSON.  The next picture is loaded while
 * the current one is showing, so the change is a fade rather than a gap, and
 * a picture that fails to load is dropped from the rotation instead of
 * leaving the panel blank.
 *
 * The reader steps through the pictures with the previous and next buttons,
 * by clicking the left or right half of the picture, or with the arrow keys
 * once the panel has focus.  Any of these restarts the rotation's timer.
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

    // A reader who has asked for less motion gets the pictures without the
    // rotation; the controls still step through them.
    var still = window.matchMedia('(prefers-reduced-motion: reduce)');
    var interval = parseInt(panel.dataset.interval, 10) || 5000;
    // The picture last asked for, which a step moves on from even while that
    // picture is still loading, so two quick clicks go two pictures on.
    var position = -1;
    var timer = null;
    var held = false;          // the pointer or the focus is on the panel
    // Each step is numbered, so a picture that arrives after a later step
    // was asked for is not shown over the later one.
    var requested = 0;

    var controls = document.createElement('div');
    controls.className = 'carousel-controls';
    var counter = document.createElement('span');
    counter.className = 'carousel-counter';

    function button(label, title, delta) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.title = title;
      b.setAttribute('aria-label', title);
      b.addEventListener('click', function () { navigate(delta); });
      return b;
    }

    controls.append(
      button('‹', 'Previous picture', -1),
      counter,
      button('›', 'Next picture', 1)
    );
    caption.after(controls);
    panel.setAttribute('role', 'region');
    panel.setAttribute('aria-label', 'Screenshots of programs using PyOpenGL');
    panel.tabIndex = 0;

    function step(delta) {
      if (!records.length) { return Promise.resolve(); }
      var target = (position + delta + records.length) % records.length;
      position = target;
      var record = records[target];
      var ticket = ++requested;
      return preload(record.url).then(function (img) {
        if (ticket !== requested) { return; }
        img.alt = record.description || '';
        img.className = 'carousel-image';
        frame.replaceChildren(img);
        // Force the transition to run on the freshly inserted element.
        requestAnimationFrame(function () { img.classList.add('shown'); });
        caption.replaceChildren(captionFor(record));
        counter.textContent = (target + 1) + ' / ' + records.length;
        controls.hidden = records.length < 2;
        if (records.length > 1) {
          preload(records[(target + delta + records.length) % records.length].url)
            .catch(function () {});
        }
      }, function () {
        if (ticket !== requested) { return; }
        // A picture that will not load is not worth trying again.  Going
        // forward, the picture after it has taken its place, so the next
        // step starts from one place earlier and lands there.
        records.splice(target, 1);
        if (delta > 0) { position = target - 1; }
        if (!records.length) { panel.remove(); return; }
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

    function navigate(delta) {
      pause();
      step(delta);
      resume();
    }

    function resume() {
      if (timer === null && !held && !still.matches && records.length > 1) {
        timer = window.setInterval(function () { step(1); }, interval);
      }
    }

    function pause() {
      if (timer !== null) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    function hold() { held = true; pause(); }
    function release() { held = false; resume(); }

    panel.addEventListener('mouseenter', hold);
    panel.addEventListener('mouseleave', release);
    panel.addEventListener('focusin', hold);
    panel.addEventListener('focusout', release);
    // The left half of the picture goes back and the right half forward.
    frame.addEventListener('click', function (event) {
      var box = frame.getBoundingClientRect();
      navigate(event.clientX < box.left + box.width / 2 ? -1 : 1);
    });
    panel.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowLeft') {
        navigate(-1);
        event.preventDefault();
      } else if (event.key === 'ArrowRight') {
        navigate(1);
        event.preventDefault();
      }
    });

    step(1).then(resume);
    still.addEventListener('change', function (event) {
      if (event.matches) { pause(); } else { resume(); }
    });

    // Rotating a panel nobody is looking at burns a timer and, on a long
    // page, bandwidth.
    if (typeof IntersectionObserver !== 'undefined') {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) { resume(); } else { pause(); }
        });
      }).observe(panel);
    }
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { pause(); } else { resume(); }
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
