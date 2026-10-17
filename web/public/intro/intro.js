// The launch intro, "The Shot" (styles in intro.css). Pictalog makes product photographs, so it opens like a camera:
// focus brackets close in on the name while it hunts into focus, the shutter fires, and the aperture opens onto the
// app. It runs before the app's own code, so the first thing on screen is black and then the name, never a blank page.
// It plays in the phone and desktop apps (index.html gets data-intro="on" from VITE_INTRO) or with ?intro in the URL.
// The shutter only fires once the app has said its first screen is ready (window "pictalog:ready"); until then the
// brackets keep breathing, like a camera waiting for focus.
;(function () {
  var html = document.documentElement
  if (html.getAttribute('data-intro') !== 'on' && !/[?&]intro\b/.test(location.search)) return

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  var SVG = 'http://www.w3.org/2000/svg'

  var intro = document.createElement('div')
  intro.id = 'intro'
  intro.setAttribute('aria-hidden', 'true')
  intro.innerHTML =
    '<div class="intro-scene"><div class="intro-frame"></div>' +
    '<div class="intro-word">P<span class="intro-i">ı<span class="intro-lens"></span></span>ctalog</div></div>' +
    '<svg class="intro-iris" style="display:none"><path fill="#000" fill-rule="evenodd"/>' +
    '<g stroke="#3d3d3d" stroke-width="1.5" stroke-linecap="round"></g></svg>' +
    '<div class="intro-flash"></div>'
  html.classList.add('intro-play')
  document.body.insertBefore(intro, document.body.firstChild)

  var scene = intro.querySelector('.intro-scene')
  var frame = intro.querySelector('.intro-frame')
  var word = intro.querySelector('.intro-word')
  var iris = intro.querySelector('.intro-iris')
  var hole = iris.querySelector('path')
  var edges = iris.querySelector('g')
  var flash = intro.querySelector('.intro-flash')
  for (var e = 0; e < 6; e++) edges.appendChild(document.createElementNS(SVG, 'line'))

  // Six blades leave a hexagonal opening of radius r, turned by `turn` radians. Each blade's edge is one side of the
  // hexagon, carried on past its corner, which is what makes it read as blades rather than a cut-out.
  function drawIris(r, turn) {
    var w = window.innerWidth
    var h = window.innerHeight
    var pts = []
    for (var k = 0; k < 6; k++) {
      var a = turn + (k * Math.PI) / 3
      pts.push([w / 2 + r * Math.cos(a), h / 2 + r * Math.sin(a)])
    }
    hole.setAttribute('d', 'M0 0H' + w + 'V' + h + 'H0Z M' + pts.map(function (p) { return p.join(' ') }).join('L') + 'Z')
    for (var i = 0; i < 6; i++) {
      var p = pts[i]
      var q = pts[(i + 1) % 6]
      var dx = p[0] - q[0]
      var dy = p[1] - q[1]
      var len = Math.hypot(dx, dy) || 1
      var reach = w + h
      var line = edges.childNodes[i]
      line.setAttribute('x1', p[0])
      line.setAttribute('y1', p[1])
      line.setAttribute('x2', p[0] + (dx / len) * reach)
      line.setAttribute('y2', p[1] + (dy / len) * reach)
    }
  }
  // Wide enough that the open hexagon clears the corners of the screen.
  function wideOpen() {
    return Math.hypot(window.innerWidth, window.innerHeight) / 2 / Math.cos(Math.PI / 6) + 4
  }
  function tween(ms, ease, step, done) {
    var start = performance.now()
    function frameStep(now) {
      var t = Math.min(1, (now - start) / ms)
      step(ease(t))
      if (t < 1) requestAnimationFrame(frameStep)
      else if (done) done()
    }
    requestAnimationFrame(frameStep)
  }
  function easeIn(t) {
    return t * t * t
  }
  function easeOut(t) {
    return 1 - Math.pow(1 - t, 3)
  }

  // Focus lock: the brackets close in around the name, then blink twice.
  function lock() {
    var b = word.getBoundingClientRect()
    var pad = Math.max(14, b.height * 0.42)
    frame.style.top = b.top - pad + 'px'
    frame.style.left = b.left - pad * 1.2 + 'px'
    frame.style.width = b.width + pad * 2.4 + 'px'
    frame.style.height = b.height + pad * 2 + 'px'
    setTimeout(function () {
      intro.classList.add('intro-locked')
    }, reduce ? 0 : 380)
  }

  var ready = !!window.__pictalogReady
  var focused = false
  var fired = false
  function done() {
    intro.remove()
  }
  // The shot: the aperture closes, the flash fires, and behind the closed blades the viewfinder gives way to the
  // app, which the aperture then opens onto.
  function shoot() {
    if (fired) return
    fired = true
    intro.classList.remove('intro-waiting')
    if (reduce) {
      html.classList.remove('intro-play')
      intro.classList.add('intro-out')
      setTimeout(done, 450)
      return
    }
    iris.style.display = 'block'
    tween(230, easeIn, function (t) {
      drawIris(wideOpen() * (1 - t), -0.5 + t * 0.6)
    }, function () {
      scene.remove()
      html.classList.remove('intro-play')
      flash.classList.add('intro-fire')
      setTimeout(function () {
        tween(720, easeOut, function (t) {
          drawIris(wideOpen() * t, 0.1 + t * 0.6)
        }, done)
      }, 120)
    })
  }
  function maybeShoot() {
    if (ready && focused) shoot()
    else if (focused) intro.classList.add('intro-waiting')
  }

  setTimeout(lock, reduce ? 200 : 1400)
  setTimeout(function () {
    focused = true
    maybeShoot()
  }, reduce ? 900 : 2100)
  window.addEventListener('pictalog:ready', function () {
    ready = true
    maybeShoot()
  })
  // Tapping takes the shot straight away; and nobody is ever kept waiting long, even if the app is slow to load.
  intro.addEventListener('click', function () {
    focused = true
    maybeShoot()
  })
  setTimeout(function () {
    ready = true
    focused = true
    maybeShoot()
  }, 8000)
})()
