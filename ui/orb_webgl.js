/* WebGL hero orb (Three.js r160). Expects global THREE. Attaches to window.__orbWebGL.
   Styles: mystic = cyan filament sphere, aether = fiery plasma, neural = glass bubble, apex = gold data streams. */
(function () {
  const HERO = { mystic: 1, aether: 1, neural: 1, apex: 1 };
  const MAX_MYSTIC_POINTS = 280;
  const MAX_AETHER_POINTS = 400;
  const MAX_NEURAL_POINTS = 360;
  const MAX_AETHER_ARCS = 24;
  const MAX_NEURAL_PANES = 4;
  const MAX_APEX_STREAMS = 12;
  const MAX_APEX_NODES = 72;
  const WHITE = new THREE.Color("#ffffff");

  function hexToColor(hex, fallback) {
    try {
      return new THREE.Color(hex || fallback);
    } catch (err) {
      return new THREE.Color(fallback);
    }
  }

  function readNumAttr(node, name, fallback) {
    const raw = node && node.getAttribute(name);
    if (raw == null || raw === "") return fallback;
    const n = parseFloat(raw);
    return Number.isFinite(n) ? n : fallback;
  }

  function readOrbNode() {
    const node = document.getElementById("orb-config");
    return {
      style: node ? node.getAttribute("data-style") || "lightning" : "lightning",
      calm: node ? node.getAttribute("data-calm-color") || "#50cdff" : "#50cdff",
      thinking: node ? node.getAttribute("data-thinking-color") || "#b388ff" : "#b388ff",
      size: Math.max(200, Math.min(480, parseInt((node && node.getAttribute("data-size")) || "360", 10) || 360)),
      // Allow 0 — previous `|| 1` made the low end of every slider a no-op.
      spin: Math.max(0, Math.min(2, readNumAttr(node, "data-spin-speed", 1))),
      turbulence: Math.max(0, Math.min(2, readNumAttr(node, "data-turbulence", 1))),
      pulse: Math.max(0, Math.min(2, readNumAttr(node, "data-pulse", 1))),
      glow: Math.max(0, Math.min(2, readNumAttr(node, "data-glow", 1))),
    };
  }

  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function makeBucket() {
    const geos = [];
    const mats = [];
    const tex = [];
    return {
      geo: function (g) { geos.push(g); return g; },
      mat: function (m) { mats.push(m); return m; },
      tex: function (t) { tex.push(t); return t; },
      dispose: function () {
        geos.forEach(function (g) { g.dispose(); });
        mats.forEach(function (m) { m.dispose(); });
        tex.forEach(function (t) { t.dispose(); });
      },
    };
  }

  function tagPaint(mat, opts) {
    mat.userData.paint = {
      white: opts.white || 0,
      opacity: opts.opacity,
      mood: opts.mood || 0,
      glow: opts.glow !== false,
    };
    mat.userData.timeScale = opts.timeScale || 1;
    return mat;
  }

  function glowScale(cfg) {
    // Mid (1) stays at 1.0 so the approved mystic look is unchanged.
    // Low drops clearly; high lifts bloom/floor without washing filaments.
    const g = Math.max(0, Math.min(2, Number.isFinite(cfg.glow) ? cfg.glow : 1));
    if (g <= 1) return 0.32 + 0.68 * g; // 0 → 0.32, 1 → 1.0
    return 1.0 + 0.5 * (g - 1); // 2 → 1.5
  }

  function applyPaint(root, color, mood, cfg) {
    const g = glowScale(cfg);
    root.traverse(function (obj) {
      if (!obj.material) return;
      const list = Array.isArray(obj.material) ? obj.material : [obj.material];
      list.forEach(function (m) {
        const p = m.userData && m.userData.paint;
        if (!p) return;
        const c = color.clone().lerp(WHITE, Math.min(0.92, p.white + mood * 0.08));
        const base = p.opacity + p.mood * mood;
        let op = p.glow ? base * g : base;
        // Dense shells already near the shader alpha cap — nudge only, don't multiply to blow-out.
        if (p.glow && g > 1 && p.opacity >= 0.7) {
          op = base + (g - 1) * 0.1;
        }
        if (m.uniforms && m.uniforms.uColor) {
          m.uniforms.uColor.value.copy(c);
          if (m.uniforms.uOpacity) m.uniforms.uOpacity.value = op;
        } else if (m.color) {
          m.color.copy(c);
          m.opacity = Math.max(0, Math.min(1, op));
        }
      });
    });
  }

  function basicMat(bucket, color, opts) {
    const mat = new THREE.MeshBasicMaterial({
      color: color.clone().lerp(WHITE, opts.white || 0),
      transparent: true,
      opacity: opts.opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      toneMapped: false,
      side: opts.side || THREE.DoubleSide,
    });
    return bucket.mat(tagPaint(mat, opts));
  }

  function pointsMat(bucket, color, sprite, opts) {
    const mat = new THREE.PointsMaterial({
      color: color.clone().lerp(WHITE, opts.white || 0),
      map: sprite,
      size: opts.size,
      transparent: true,
      opacity: opts.opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      toneMapped: false,
      sizeAttenuation: true,
    });
    return bucket.mat(tagPaint(mat, opts));
  }

  function softSprite(bucket) {
    const canvas = document.createElement("canvas");
    canvas.width = 64;
    canvas.height = 64;
    const g = canvas.getContext("2d");
    const grd = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    grd.addColorStop(0, "rgba(255,255,255,1)");
    grd.addColorStop(0.28, "rgba(255,255,255,0.65)");
    grd.addColorStop(0.62, "rgba(255,255,255,0.18)");
    grd.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = grd;
    g.fillRect(0, 0, 64, 64);
    const tex = new THREE.CanvasTexture(canvas);
    tex.needsUpdate = true;
    return bucket.tex(tex);
  }

  const VERT_UV = [
    "varying vec2 vUv;",
    "void main() {",
    "  vUv = uv;",
    "  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);",
    "}",
  ].join("\n");

  function shaderMat(bucket, frag, opts) {
    const mat = new THREE.ShaderMaterial({
      uniforms: {
        uColor: { value: new THREE.Color(opts.color || "#50cdff") },
        uOpacity: { value: opts.opacity },
        uPower: { value: opts.power == null ? 2.0 : opts.power },
        uTime: { value: 0 },
        uPhase: { value: opts.phase || 0 },
        uStreak: { value: opts.streaks || 4 },
        uWhite: { value: opts.white || 0 },
        uTurbulence: { value: opts.turbulence == null ? 1.0 : opts.turbulence },
      },
      vertexShader: opts.vertex || VERT_UV,
      fragmentShader: frag,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
      side: opts.side || THREE.DoubleSide,
    });
    return bucket.mat(tagPaint(mat, opts));
  }

  const FRAG_DISC = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uPower;",
    "uniform float uWhite;",
    "varying vec2 vUv;",
    "void main() {",
    "  float d = length(vUv - vec2(0.5)) * 2.0;",
    "  float a = pow(clamp(1.0 - d, 0.0, 1.0), uPower);",
    "  if (a < 0.004) discard;",
    "  vec3 col = mix(uColor, vec3(1.0), uWhite);",
    "  gl_FragColor = vec4(col, a * uOpacity);",
    "}",
  ].join("\n");

  const FRAG_FLARE = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "varying vec2 vUv;",
    "void main() {",
    "  float x = (vUv.x - 0.5) * 2.0;",
    "  float y = (vUv.y - 0.5) * 2.0;",
    "  float reach = exp(-pow(x * 1.25, 2.0));",
    "  float line = exp(-pow(y * 28.0, 2.0)) * reach;",
    "  float bloom = exp(-pow(y * 4.2, 2.0)) * exp(-pow(x * 1.15, 2.0));",
    "  float core = exp(-(x * x) * 14.0) * exp(-(y * y) * 18.0);",
    "  float a = line * 1.25 + bloom * 0.42 + core * 0.95;",
    "  if (a < 0.01) discard;",
    "  vec3 col = mix(uColor, vec3(1.0), clamp(line * 0.85 + core, 0.0, 1.0));",
    "  gl_FragColor = vec4(col, a * uOpacity);",
    "}",
  ].join("\n");

  const FRAG_GLASS = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "void main() {",
    "  vec3 N = normalize(vNormal);",
    "  vec3 V = normalize(vView);",
    "  float fres = pow(1.0 - abs(dot(N, V)), 1.65);",
    "  vec3 L = normalize(vec3(-0.45, 0.62, 0.72));",
    "  float spec = pow(max(dot(N, L), 0.0), 26.0);",
    "  float rim = fres * 0.95;",
    "  float alpha = (0.035 + rim) * uOpacity + spec * 0.9;",
    "  vec3 col = mix(uColor, vec3(1.0), clamp(spec + fres * 0.35, 0.0, 1.0));",
    "  gl_FragColor = vec4(col, alpha);",
    "}",
  ].join("\n");

  const VERT_GLASS = [
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "void main() {",
    "  vec4 mv = modelViewMatrix * vec4(position, 1.0);",
    "  vView = normalize(-mv.xyz);",
    "  vNormal = normalize(normalMatrix * normal);",
    "  gl_Position = projectionMatrix * mv;",
    "}",
  ].join("\n");

  const FRAG_RIBBON = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "uniform float uPhase;",
    "uniform float uStreak;",
    "varying vec2 vUv;",
    "void main() {",
    "  float across = abs(vUv.y - 0.5) * 2.0;",
    "  float edge = pow(clamp(1.0 - across, 0.0, 1.0), 1.15);",
    "  float flow = 0.28 + 0.72 * pow(0.5 + 0.5 * sin(vUv.x * uStreak * 6.28318 - uTime + uPhase), 1.35);",
    "  float fine = 0.62 + 0.38 * sin(vUv.x * 54.0 + vUv.y * 8.0 - uTime * 1.7);",
    "  float vein = smoothstep(0.55, 0.95, flow) * (1.0 - across);",
    "  float a = edge * flow * fine * uOpacity;",
    "  if (a < 0.012) discard;",
    "  vec3 deep = uColor * vec3(0.28, 0.55, 0.85);",
    "  vec3 hot = mix(uColor, vec3(1.0), 0.72);",
    "  vec3 col = mix(deep, hot, clamp(flow * 0.75 + vein, 0.0, 1.0));",
    "  gl_FragColor = vec4(col, a);",
    "}",
  ].join("\n");

  const FRAG_RING = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "varying vec2 vUv;",
    "void main() {",
    "  float streak = 0.4 + 0.6 * pow(0.5 + 0.5 * sin(vUv.x * 26.0 - uTime), 1.5);",
    "  float tube = pow(max(sin(vUv.y * 3.14159), 0.0), 0.55);",
    "  vec3 col = mix(uColor, vec3(1.0), 0.35 + 0.55 * streak);",
    "  gl_FragColor = vec4(col, streak * tube * uOpacity);",
    "}",
  ].join("\n");

  const FRAG_HALO_RING = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "varying vec2 vUv;",
    "void main() {",
    "  float r = length(vUv - vec2(0.5)) * 2.0;",
    "  float band = exp(-pow((r - 0.62) * 2.6, 2.0));",
    "  float outer = exp(-pow((r - 0.78) * 1.35, 2.0));",
    "  float a = (band * 0.85 + outer * 0.4) * smoothstep(0.16, 0.4, r);",
    "  if (a < 0.01) discard;",
    "  gl_FragColor = vec4(uColor, a * uOpacity);",
    "}",
  ].join("\n");

  function addDisc(bucket, parent, radius, frag, opts) {
    const mat = shaderMat(bucket, frag, opts);
    const mesh = new THREE.Mesh(bucket.geo(new THREE.CircleGeometry(radius, 72)), mat);
    mesh.position.z = opts.z || 0;
    parent.add(mesh);
    return mat;
  }

  function buildRibbonGeometry(opts) {
    const seg = opts.segments || 168;
    const positions = new Float32Array((seg + 1) * 6);
    const uvs = new Float32Array((seg + 1) * 4);
    const indices = new Uint16Array(seg * 6);
    const tmp = new THREE.Vector3();
    const ahead = new THREE.Vector3();
    const side = new THREE.Vector3();
    const R = opts.radius;
    const waves = opts.waves || 3;
    const phase = opts.phase || 0;
    const radAmp = opts.radAmp || 0.08;
    const zAmp = opts.zAmp || 0.35;
    const width = opts.width || 0.3;
    const zWaves = opts.zWaves || 2;

    function curvePoint(t, target) {
      const rad = R + Math.sin(t * waves + phase) * radAmp;
      target.set(
        Math.cos(t) * rad,
        Math.sin(t) * rad * 0.97,
        Math.sin(t * zWaves + phase * 1.3) * zAmp + Math.cos(t * waves * 0.5 + phase) * zAmp * 0.25
      );
    }

    for (let i = 0; i <= seg; i++) {
      const t = (i / seg) * Math.PI * 2;
      curvePoint(t, tmp);
      curvePoint(t + 0.025, ahead);
      ahead.sub(tmp);
      side.set(-ahead.y, ahead.x, 0);
      if (side.lengthSq() < 1e-8) side.set(0, 1, 0);
      side.normalize().multiplyScalar(width * 0.5);
      const o = i * 6;
      positions[o] = tmp.x + side.x;
      positions[o + 1] = tmp.y + side.y;
      positions[o + 2] = tmp.z + side.z * 0.35;
      positions[o + 3] = tmp.x - side.x;
      positions[o + 4] = tmp.y - side.y;
      positions[o + 5] = tmp.z - side.z * 0.35;
      const u = i * 4;
      uvs[u] = i / seg;
      uvs[u + 1] = 0;
      uvs[u + 2] = i / seg;
      uvs[u + 3] = 1;
      if (i < seg) {
        const a = i * 2;
        const k = i * 6;
        indices[k] = a;
        indices[k + 1] = a + 2;
        indices[k + 2] = a + 1;
        indices[k + 3] = a + 1;
        indices[k + 4] = a + 2;
        indices[k + 5] = a + 3;
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geo.setAttribute("uv", new THREE.BufferAttribute(uvs, 2));
    geo.setIndex(new THREE.BufferAttribute(indices, 1));
    return geo;
  }

  function buildStrip(points, width) {
    const n = points.length;
    const positions = new Float32Array(n * 6);
    const uvs = new Float32Array(n * 4);
    const indices = [];
    const side = new THREE.Vector3();
    const tangent = new THREE.Vector3();
    const radial = new THREE.Vector3();
    for (let i = 0; i < n; i++) {
      const p = points[i];
      const nxt = points[Math.min(n - 1, i + 1)];
      const prv = points[Math.max(0, i - 1)];
      tangent.subVectors(nxt, prv);
      if (tangent.lengthSq() < 1e-8) tangent.set(0, 1, 0);
      tangent.normalize();
      radial.copy(p).normalize();
      side.crossVectors(tangent, radial);
      if (side.lengthSq() < 1e-8) side.set(0, 0, 1);
      side.normalize().multiplyScalar(width * 0.5);
      const o = i * 6;
      positions[o] = p.x + side.x;
      positions[o + 1] = p.y + side.y;
      positions[o + 2] = p.z + side.z;
      positions[o + 3] = p.x - side.x;
      positions[o + 4] = p.y - side.y;
      positions[o + 5] = p.z - side.z;
      uvs[i * 4] = i / (n - 1);
      uvs[i * 4 + 1] = 0;
      uvs[i * 4 + 2] = i / (n - 1);
      uvs[i * 4 + 3] = 1;
      if (i < n - 1) {
        const a = i * 2;
        indices.push(a, a + 2, a + 1, a + 1, a + 2, a + 3);
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geo.setAttribute("uv", new THREE.BufferAttribute(uvs, 2));
    geo.setIndex(indices);
    return geo;
  }

  function sampleArcPath(major, minor, start, span, tilt, count, wobble, phase, wobbleT) {
    const points = [];
    const rot = new THREE.Matrix4().makeRotationFromEuler(new THREE.Euler(tilt.x, tilt.y, tilt.z));
    const p = new THREE.Vector3();
    const wt = wobbleT || 0;
    for (let i = 0; i < count; i++) {
      const u = i / Math.max(1, count - 1);
      const ang = start + span * u;
      const wob = Math.sin(ang * 3.0 + phase + wt * 0.35) * wobble;
      p.set(
        Math.cos(ang) * (major + wob),
        Math.sin(ang) * (minor + wob * 0.6),
        Math.sin(ang * 1.35 + phase) * minor * 0.22
      );
      p.applyMatrix4(rot);
      points.push(p.clone());
    }
    return points;
  }

  function dashedRingGeometry(radius, width, dashes, gap) {
    const positions = [];
    const indices = [];
    let v = 0;
    const steps = 5;
    for (let d = 0; d < dashes; d++) {
      const a0 = (d / dashes) * Math.PI * 2;
      const a1 = ((d + (1 - gap)) / dashes) * Math.PI * 2;
      for (let s = 0; s < steps; s++) {
        const t0 = a0 + ((a1 - a0) * s) / steps;
        const t1 = a0 + ((a1 - a0) * (s + 1)) / steps;
        const c0 = Math.cos(t0);
        const s0 = Math.sin(t0);
        const c1 = Math.cos(t1);
        const s1 = Math.sin(t1);
        positions.push(
          (radius + width) * c0, (radius + width) * s0, 0,
          (radius - width) * c0, (radius - width) * s0, 0,
          (radius + width) * c1, (radius + width) * s1, 0,
          (radius - width) * c1, (radius - width) * s1, 0
        );
        indices.push(v, v + 2, v + 1, v + 1, v + 2, v + 3);
        v += 4;
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geo.setIndex(indices);
    return geo;
  }

  function fibonacci(count, radius, rng) {
    const pts = [];
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < count; i++) {
      const y = 1 - (i / Math.max(1, count - 1)) * 2;
      const rr = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = golden * i + (rng ? rng() * 0.2 : 0);
      const jitter = rng ? 0.97 + rng() * 0.06 : 1;
      pts.push(new THREE.Vector3(
        Math.cos(theta) * rr * radius * jitter,
        y * radius * jitter,
        Math.sin(theta) * rr * radius * jitter
      ));
    }
    return pts;
  }

  function thickSegments(pairs, width) {
    const positions = [];
    const indices = [];
    let v = 0;
    const side = new THREE.Vector3();
    const tangent = new THREE.Vector3();
    for (let i = 0; i < pairs.length; i++) {
      const a = pairs[i][0];
      const b = pairs[i][1];
      tangent.subVectors(b, a);
      side.set(-tangent.y, tangent.x, 0);
      if (side.lengthSq() < 1e-8) side.set(0, 0, width);
      side.normalize().multiplyScalar(width);
      positions.push(
        a.x + side.x, a.y + side.y, a.z,
        a.x - side.x, a.y - side.y, a.z,
        b.x + side.x, b.y + side.y, b.z,
        b.x - side.x, b.y - side.y, b.z
      );
      indices.push(v, v + 2, v + 1, v + 1, v + 2, v + 3);
      v += 4;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geo.setIndex(indices);
    return geo;
  }

  function surfaceFilament(rng) {
    const pts = [];
    let lon = rng() * Math.PI * 2;
    let lat = -0.35 + rng() * 1.7;
    const n = 14 + Math.floor(rng() * 10);
    const turn = 0.18 + rng() * 0.28;
    const climb = (rng() - 0.45) * 0.22;
    for (let i = 0; i < n; i++) {
      lon += turn + (rng() - 0.5) * 0.08;
      lat += climb + (rng() - 0.5) * 0.06;
      lat = Math.max(-1.15, Math.min(1.15, lat));
      const r = 0.92 + rng() * 0.12;
      const cl = Math.cos(lat);
      pts.push(new THREE.Vector3(Math.cos(lon) * cl * r, Math.sin(lat) * r, Math.sin(lon) * cl * r));
    }
    return pts;
  }

  const VERT_ENERGY = [
    "varying vec3 vObj;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "void main() {",
    "  vec4 mv = modelViewMatrix * vec4(position, 1.0);",
    "  vObj = position;",
    "  vView = normalize(-mv.xyz);",
    "  vNormal = normalize(normalMatrix * normal);",
    "  gl_Position = projectionMatrix * mv;",
    "}",
  ].join("\n");

  const FRAG_PLASMA = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "varying vec3 vObj;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "float hash13(vec3 p) {",
    "  p = fract(p * 0.1031);",
    "  p += dot(p, p.yzx + 33.33);",
    "  return fract((p.x + p.y) * p.z);",
    "}",
    "float noise(vec3 p) {",
    "  vec3 i = floor(p);",
    "  vec3 f = fract(p);",
    "  f = f * f * (3.0 - 2.0 * f);",
    "  return mix(",
    "    mix(mix(hash13(i), hash13(i + vec3(1.0, 0.0, 0.0)), f.x),",
    "        mix(hash13(i + vec3(0.0, 1.0, 0.0)), hash13(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),",
    "    mix(mix(hash13(i + vec3(0.0, 0.0, 1.0)), hash13(i + vec3(1.0, 0.0, 1.0)), f.x),",
    "        mix(hash13(i + vec3(0.0, 1.0, 1.0)), hash13(i + vec3(1.0, 1.0, 1.0)), f.x), f.y),",
    "    f.z);",
    "}",
    "float fbm(vec3 p) {",
    "  float v = 0.0;",
    "  float a = 0.5;",
    "  for (int i = 0; i < 5; i++) {",
    "    v += a * noise(p);",
    "    p = p * 2.07 + vec3(1.7, 9.2, 3.4);",
    "    a *= 0.5;",
    "  }",
    "  return v;",
    "}",
    "void main() {",
    "  vec3 N = normalize(vNormal);",
    "  vec3 V = normalize(vView);",
    "  float facing = abs(dot(N, V));",
    "  float fres = pow(1.0 - facing, 1.7);",
    "  vec3 p = vObj * 6.4 + vec3(uTime * 0.22, uTime * 0.07, -uTime * 0.05);",
    "  float ridge = pow(1.0 - abs(fbm(p) * 2.0 - 1.0), 1.6);",
    "  float veins = smoothstep(0.42, 0.88, ridge);",
    "  float fine = smoothstep(0.62, 0.95, pow(1.0 - abs(fbm(p * 2.15 + 4.0) * 2.0 - 1.0), 2.4));",
    "  float hot = pow(facing, 14.0);",
    "  float equator = exp(-pow(vObj.y * 18.0, 2.0));",
    "  float alpha = veins * 0.42 * (0.35 + 0.65 * facing) + fine * 0.18 * facing + fres * 0.18 + hot * 0.85 + equator * 0.22;",
    "  if (alpha < 0.025) discard;",
    "  vec3 col = mix(uColor, vec3(1.0), clamp(hot * 0.95 + equator * 0.45, 0.0, 1.0));",
    "  gl_FragColor = vec4(col, alpha * uOpacity);",
    "}",
  ].join("\n");

  // Neural only: one thick torus. Facing body stays a translucent veil.
  // Inner and outer rims carry a thin mystic filament: it travels along the
  // ring, cyan with white on the bright crests. No MeshPhysical transmission.
  const FRAG_BUBBLE = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "uniform float uTurbulence;",
    "uniform float uPower;",
    "varying vec3 vObj;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "float hash13(vec3 p) {",
    "  p = fract(p * 0.1031);",
    "  p += dot(p, p.yzx + 33.33);",
    "  return fract((p.x + p.y) * p.z);",
    "}",
    "float noise(vec3 p) {",
    "  vec3 i = floor(p);",
    "  vec3 f = fract(p);",
    "  f = f * f * (3.0 - 2.0 * f);",
    "  return mix(",
    "    mix(mix(hash13(i), hash13(i + vec3(1.0, 0.0, 0.0)), f.x),",
    "        mix(hash13(i + vec3(0.0, 1.0, 0.0)), hash13(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),",
    "    mix(mix(hash13(i + vec3(0.0, 0.0, 1.0)), hash13(i + vec3(1.0, 0.0, 1.0)), f.x),",
    "        mix(hash13(i + vec3(0.0, 1.0, 1.0)), hash13(i + vec3(1.0, 1.0, 1.0)), f.x), f.y),",
    "    f.z);",
    "}",
    "float fbm(vec3 p) {",
    "  float v = 0.0;",
    "  float a = 0.5;",
    "  for (int i = 0; i < 3; i++) {",
    "    v += a * noise(p);",
    "    p = p * 2.03 + vec3(1.7, 9.2, 3.4);",
    "    a *= 0.5;",
    "  }",
    "  return v;",
    "}",
    "float crest(float x, float sharp) {",
    "  return pow(clamp(1.0 - abs(sin(x)), 0.0, 1.0), sharp);",
    "}",
    "void main() {",
    "  vec3 N = normalize(vNormal);",
    "  vec3 V = normalize(vView);",
    "  float ndv = clamp(abs(dot(N, V)), 0.0, 1.0);",
    "  float skin = smoothstep(0.15, 0.85, uPower);",
    "  float turb = clamp(uTurbulence, 0.0, 2.0);",
    "  float grazing = 1.0 - ndv;",
    "  float fres = pow(grazing, mix(1.4, 1.85, skin));",
    "  float body = mix(0.18, 0.26, skin) * (0.55 + 0.45 * pow(ndv, 0.5));",
    "  float lip = fres * mix(0.16, 0.28, skin);",
    "  vec3 L = normalize(vec3(-0.5, 0.78, 0.64));",
    "  vec3 H = normalize(L + V);",
    "  float ndh = max(dot(N, H), 0.0);",
    "  float sheen = pow(ndh, 5.0) * 0.3 * skin;",
    "  float catch = pow(ndh, 22.0) * skin;",
    "  float shim = sin(vObj.x * 2.2 + vObj.y * 1.6 + uTime * (0.32 + 0.26 * turb));",
    "  float wobble = 1.0 + shim * (0.02 + 0.045 * turb);",
    "  float up = clamp(N.y * 0.5 + 0.5, 0.0, 1.0);",
    "  float glass = (body + lip * 0.7 + sheen * 0.35) * wobble * (0.9 + 0.1 * up);",
    "  float alpha = min(glass * uOpacity, mix(0.26, 0.36, skin)) + catch * 0.64;",
    "  float ang = atan(vObj.y, vObj.x);",
    "  float side = step(0.78, length(vObj.xy));",
    "  float t = uTime * (0.34 + 0.22 * turb);",
    "  float w = fbm(vec3(ang * 1.35, side * 2.4 + vObj.z * 1.8, t * 0.42));",
    "  float sharp = mix(3.4, 2.3, clamp(turb * 0.5, 0.0, 1.0));",
    "  float warp = (w - 0.5) * (2.4 + 1.8 * turb);",
    "  float aArc = crest(ang * 2.15 + t * 1.15 + warp + side * 2.1, sharp);",
    "  float bArc = crest(ang * 3.3 - t * 0.8 + warp * 0.65 + 1.1, sharp);",
    "  float flow = clamp(max(aArc, bArc * 0.9), 0.0, 1.0);",
    "  float rimBand = smoothstep(0.64, 0.90, grazing) * skin;",
    "  float rimA = rimBand * (0.16 + 0.84 * pow(flow, 0.6));",
    "  rimA *= clamp(uOpacity / 0.82, 0.3, 1.08);",
    "  alpha += rimA;",
    "  if (alpha < 0.012) discard;",
    "  vec3 filBase = uColor;",
    "  vec3 hot = mix(filBase, vec3(1.0), 0.48);",
    "  float lift = clamp(smoothstep(0.25, 0.85, flow) * 0.7, 0.0, 0.62);",
    "  vec3 filCol = mix(filBase, hot, lift);",
    "  filCol = min(filCol, mix(filBase, vec3(1.0), 0.62));",
    "  vec3 glassCol = uColor;",
    "  glassCol = mix(glassCol, vec3(0.72, 0.97, 1.0), clamp(sheen, 0.0, 0.42));",
    "  glassCol = mix(glassCol, vec3(0.97, 0.99, 1.0), clamp(catch, 0.0, 0.95));",
    "  vec3 col = mix(glassCol, filCol, rimBand);",
    "  gl_FragColor = vec4(col, min(alpha, 0.92));",
    "}",
  ].join("\n");

  const FRAG_PANE = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "varying vec3 vObj;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "void main() {",
    "  vec3 N = normalize(vNormal);",
    "  vec3 V = normalize(vView);",
    "  float fres = pow(1.0 - abs(dot(N, V)), 1.8);",
    "  float band = smoothstep(0.25, 0.85, fres);",
    "  float alpha = band * uOpacity;",
    "  if (alpha < 0.02) discard;",
    "  gl_FragColor = vec4(mix(uColor, vec3(1.0), 0.25), alpha);",
    "}",
  ].join("\n");

  // Mystic only. Thin swirling arcs via warped sin-ridges + FBM ridge extraction.
  // Colour lift is capped so the core cannot mix out to pure white. Do not point aether here.
  const FRAG_MYSTIC = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "uniform float uPhase;",
    "uniform float uPower;",
    "uniform float uTurbulence;",
    "varying vec3 vObj;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "float hash13(vec3 p) {",
    "  p = fract(p * 0.1031);",
    "  p += dot(p, p.yzx + 33.33);",
    "  return fract((p.x + p.y) * p.z);",
    "}",
    "float noise(vec3 p) {",
    "  vec3 i = floor(p);",
    "  vec3 f = fract(p);",
    "  f = f * f * (3.0 - 2.0 * f);",
    "  return mix(",
    "    mix(mix(hash13(i), hash13(i + vec3(1.0, 0.0, 0.0)), f.x),",
    "        mix(hash13(i + vec3(0.0, 1.0, 0.0)), hash13(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),",
    "    mix(mix(hash13(i + vec3(0.0, 0.0, 1.0)), hash13(i + vec3(1.0, 0.0, 1.0)), f.x),",
    "        mix(hash13(i + vec3(0.0, 1.0, 1.0)), hash13(i + vec3(1.0, 1.0, 1.0)), f.x), f.y),",
    "    f.z);",
    "}",
    "float fbm(vec3 p) {",
    "  float v = 0.0;",
    "  float a = 0.5;",
    "  for (int i = 0; i < 4; i++) {",
    "    v += a * noise(p);",
    "    p = p * 2.03 + vec3(1.7, 9.2, 3.4);",
    "    a *= 0.5;",
    "  }",
    "  return v;",
    "}",
    "float crest(float x, float sharp) {",
    "  return pow(1.0 - abs(sin(x)), sharp);",
    "}",
    "void main() {",
    "  vec3 N = normalize(vNormal);",
    "  vec3 V = normalize(vView);",
    "  float facing = abs(dot(N, V));",
    "  vec3 sp = normalize(vObj);",
    "  float lon = atan(sp.z, sp.x);",
    "  float lat = asin(clamp(sp.y, -1.0, 1.0));",
    // turb 0 → calm filaments, 1 → approved look, 2 → livelier warp (not chaos)
    "  float turb = clamp(uTurbulence, 0.0, 2.0);",
    "  float t = uTime * (0.18 + 0.14 * turb) + uPhase;",
    "  float wLon = fbm(vec3(lon * 0.62, lat * 1.05, t * 0.22));",
    "  float wLat = fbm(vec3(lat * 0.74 + 4.2, lon * 0.55, t * 0.16 + 2.0));",
    "  float lonAmp = 0.9 + 1.5 * turb;",
    "  float latAmp = 0.4 + 0.75 * turb;",
    "  float lonW = lon + (wLon - 0.5) * lonAmp + t * 0.18 + uPhase;",
    "  float latW = lat + (wLat - 0.5) * latAmp + (0.12 + 0.16 * turb) * sin(lon * 2.0 - t * 0.65);",
    "  lonW += (0.18 + 0.24 * turb) * sin(latW * 2.6 + t);",
    "  float sharp = mix(12.5, 5.5, clamp(turb * 0.5, 0.0, 1.0));",
    "  float aArc = crest(latW * 5.7 + lonW * 0.42 + wLon * 3.2, sharp);",
    "  float bArc = crest(lonW * 4.55 + latW * 1.25 + wLat * 2.6, sharp);",
    "  float cArc = crest((latW + lonW) * 4.1 + wLon * 2.4, sharp);",
    "  float dArc = crest((latW * 1.7 - lonW) * 3.15 + wLat * 4.0, sharp);",
    "  vec3 rp = vec3(lonW * 1.15, latW * 2.05, t * 0.12);",
    "  float ridgePow = mix(14.0, 8.0, clamp(turb * 0.5, 0.0, 1.0));",
    "  float ridge = pow(clamp(1.0 - abs(fbm(rp) * 2.0 - 1.0), 0.0, 1.0), ridgePow);",
    "  float knots = clamp((aArc * bArc + bArc * cArc + aArc * cArc) * 4.2, 0.0, 1.0);",
    "  float lines = max(max(aArc, bArc), max(cArc, dArc * 0.75));",
    "  lines = max(lines, ridge);",
    "  lines = max(lines, knots * 0.88);",
    "  lines *= 0.32 + 0.68 * smoothstep(0.0, 0.2, facing);",
    "  float front = step(0.5, uPower);",
    "  float core = front * exp(-dot(vObj.xy, vObj.xy) * 7.2) * pow(facing, 0.55);",
    "  float body = 0.07 * (0.45 + 0.55 * facing);",
    "  float feat = max(lines, core * 0.95);",
    "  float limb = smoothstep(0.0, 0.38, facing);",
    "  float alpha = (body + feat * 0.8) * mix(0.22, 1.0, limb);",
    "  alpha *= uOpacity;",
    "  if (alpha < 0.02) discard;",
    "  vec3 hot = mix(uColor, vec3(1.0), 0.48);",
    "  float lift = clamp(core * 0.7 + knots * 0.16, 0.0, 0.58);",
    "  vec3 col = mix(uColor * (0.42 + 0.58 * lines), hot, lift);",
    "  col = min(col, mix(uColor, vec3(1.0), 0.62));",
    "  gl_FragColor = vec4(col, min(alpha, 0.86));",
    "}",
  ].join("\n");

  // Soft atmospheric bloom — radial falloff with no hard rim (mystic only).
  const FRAG_MYSTIC_ATMOS = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uPower;",
    "varying vec2 vUv;",
    "void main() {",
    "  float d = length(vUv - vec2(0.5)) * 2.0;",
    "  float glow = exp(-pow(max(d - 0.22, 0.0) * uPower, 2.0));",
    "  float veil = exp(-pow(max(d - 0.08, 0.0) * (uPower * 0.55), 2.0)) * 0.45;",
    "  float a = (glow + veil) * uOpacity * smoothstep(1.05, 0.42, d);",
    "  if (a < 0.003) discard;",
    "  gl_FragColor = vec4(uColor, a);",
    "}",
  ].join("\n");

  // Neural only: soft haze around the bubble. Monotonic falloff — no peaked ring
  // (stacked peaks read as hard concentric bands). Centre stays dark.
  const FRAG_NEURAL_ATMOS = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uPower;",
    "varying vec2 vUv;",
    "void main() {",
    "  float d = length(vUv - vec2(0.5)) * 2.0;",
    "  float reach = max(d - 0.12, 0.0) * (0.32 + uPower * 0.14);",
    "  float lobe = exp(-reach * reach);",
    "  float hollow = smoothstep(0.14, 0.58, d);",
    "  float fade = smoothstep(1.48, 0.22, d);",
    "  float a = lobe * hollow * fade * uOpacity;",
    "  if (a < 0.004) discard;",
    "  gl_FragColor = vec4(uColor, a);",
    "}",
  ].join("\n");

  // Neural sparkles only. Per-point phase so the field twinkles instead of flashing together.
  const VERT_NEURAL_SPARK = [
    "attribute float aPhase;",
    "attribute float aGain;",
    "uniform float uTime;",
    "uniform float uSize;",
    "varying float vTw;",
    "void main() {",
    "  vec4 mv = modelViewMatrix * vec4(position, 1.0);",
    "  float tw = 0.84 + 0.16 * sin(uTime * 0.55 + aPhase);",
    "  vTw = tw;",
    "  gl_PointSize = clamp(uSize * aGain * tw * (980.0 / max(0.3, -mv.z)), 2.0, 34.0);",
    "  gl_Position = projectionMatrix * mv;",
    "}",
  ].join("\n");

  const FRAG_NEURAL_SPARK = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "varying float vTw;",
    "void main() {",
    "  vec2 p = gl_PointCoord - vec2(0.5);",
    "  float d = length(p);",
    "  float core = smoothstep(0.16, 0.0, d);",
    "  float halo = smoothstep(0.5, 0.08, d);",
    "  float a = (core * 1.0 + halo * 0.55) * uOpacity * vTw;",
    "  if (a < 0.02) discard;",
    "  vec3 col = mix(uColor, vec3(0.96, 0.99, 1.0), 0.9);",
    "  gl_FragColor = vec4(col, a);",
    "}",
  ].join("\n");

function createMystic(scene, color) {
    // Filament sphere: FBM ridges, soft atmospheric bloom, clamped core. No hard rim / equatorial bar.
    const bucket = makeBucket();
    const group = new THREE.Group();
    group.name = "mystic";

    addDisc(bucket, group, 2.75, FRAG_MYSTIC_ATMOS, {
      color: color, opacity: 0.34, power: 1.15, white: 0.0, z: -0.48, mood: 0.05,
    });
    group.children[group.children.length - 1].renderOrder = 0;

    addDisc(bucket, group, 2.15, FRAG_MYSTIC_ATMOS, {
      color: color, opacity: 0.4, power: 1.65, white: 0.0, z: -0.32, mood: 0.05,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    addDisc(bucket, group, 1.55, FRAG_DISC, {
      color: color, opacity: 0.16, power: 2.4, white: 0.0, z: -0.18, mood: 0.03,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    const backMat = shaderMat(bucket, FRAG_MYSTIC, {
      color: color, opacity: 0.78, power: 0.0, phase: 1.85, white: 0.02, mood: 0.05,
      vertex: VERT_ENERGY, side: THREE.BackSide,
    });
    const back = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(0.96, 64, 48)), backMat);
    back.renderOrder = 2;
    group.add(back);

    const frontMat = shaderMat(bucket, FRAG_MYSTIC, {
      color: color, opacity: 0.96, power: 1.0, phase: 0.15, white: 0.04, mood: 0.06,
      vertex: VERT_ENERGY, side: THREE.FrontSide,
    });
    const front = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(1.0, 72, 56)), frontMat);
    front.renderOrder = 3;
    group.add(front);

    const core = new THREE.Group();
    const coreMat = addDisc(bucket, core, 0.13, FRAG_DISC, {
      color: color, opacity: 0.48, power: 1.35, white: 0.18, z: 0.05, mood: 0.02,
    });
    core.renderOrder = 4;
    group.add(core);

    const pedestal = new THREE.Group();
    pedestal.position.y = -1.38;
    const floor = new THREE.Mesh(
      bucket.geo(new THREE.CircleGeometry(1.05, 48)),
      shaderMat(bucket, FRAG_DISC, { color: color, opacity: 0.28, power: 1.55, white: 0.06, mood: 0.03 })
    );
    floor.rotation.x = -Math.PI / 2;
    pedestal.add(floor);
    group.add(pedestal);
    group.position.y = 0.22;

    scene.add(group);
    return {
      group: group,
      bucket: bucket,
      cameraZ: 4.55,
      animate: function (state) {
        // Spin: 0 = still, 1 = prior mid (~0.60), 2 = clearly faster.
        const speed = state.cfg.spin * 0.6;
        const pulse = state.cfg.pulse;
        const turb = state.cfg.turbulence;
        applyPaint(group, state.color, state.mood, state.cfg);
        // Pulse: mid keeps prior 0.018 / 0.08 amplitudes; high is stronger but not manic.
        group.scale.setScalar(1 + 0.018 * Math.sin(state.now * 0.0014) * pulse);
        const swirl = state.now * 0.001 * speed;
        frontMat.uniforms.uTime.value = swirl;
        backMat.uniforms.uTime.value = swirl * 0.82;
        frontMat.uniforms.uTurbulence.value = turb;
        backMat.uniforms.uTurbulence.value = turb;
        core.scale.setScalar(1 + 0.08 * Math.sin(state.now * 0.0028) * pulse);
        if (coreMat.uniforms) {
          const breath = pulse <= 0 ? 1 : 0.92 + 0.08 * Math.sin(state.now * 0.003) * Math.min(pulse, 1.35);
          coreMat.uniforms.uOpacity.value *= breath;
        }
      },
    };
  }

  function neuralSparkMat(bucket, color, opts) {
    const mat = new THREE.ShaderMaterial({
      uniforms: {
        uColor: { value: color.clone() },
        uOpacity: { value: opts.opacity },
        uTime: { value: 0 },
        uSize: { value: opts.size },
      },
      vertexShader: VERT_NEURAL_SPARK,
      fragmentShader: FRAG_NEURAL_SPARK,
      transparent: true,
      depthWrite: false,
      depthTest: false,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    return bucket.mat(tagPaint(mat, opts));
  }

  function fillSparkGeo(bucket, rng, count, place) {
    const pos = [];
    const phase = [];
    const gain = [];
    for (let i = 0; i < count; i++) {
      const p = place(rng);
      pos.push(p[0], p[1], p[2]);
      phase.push(rng() * Math.PI * 2);
      gain.push(0.8 + rng() * 0.45);
    }
    const geo = bucket.geo(new THREE.BufferGeometry());
    geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute("aPhase", new THREE.Float32BufferAttribute(phase, 1));
    geo.setAttribute("aGain", new THREE.Float32BufferAttribute(gain, 1));
    return geo;
  }

function createNeural(scene, color) {
    // Glass torus: one thick hollow shell (front skin + far wall), dark void,
    // wider cyan haze, a sparkle field in the glass. No MeshPhysical transmission.
    const bucket = makeBucket();
    const group = new THREE.Group();
    group.name = "neural";
    const cyanBias = color.clone().lerp(new THREE.Color("#8ef7ff"), 0.74);
    const major = 0.78;
    const tube = 0.24;

    addDisc(bucket, group, 3.4, FRAG_NEURAL_ATMOS, {
      color: cyanBias, opacity: 0.5, power: 0.42, white: 0.08, z: -0.5, mood: 0.04,
    });
    group.children[group.children.length - 1].renderOrder = 0;

    addDisc(bucket, group, 2.15, FRAG_NEURAL_ATMOS, {
      color: cyanBias, opacity: 0.22, power: 0.7, white: 0.04, z: -0.22, mood: 0.03,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    // Occlude the hole so haze cannot fill the void. Stays inside the inner rim.
    const voidMat = bucket.mat(new THREE.MeshBasicMaterial({
      color: new THREE.Color("#000000"),
      transparent: true,
      opacity: 1.0,
      depthWrite: false,
      toneMapped: false,
      side: THREE.FrontSide,
      blending: THREE.NormalBlending,
    }));
    const voidCore = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(major - tube - 0.02, 48, 32)), voidMat);
    voidCore.renderOrder = 2;
    group.add(voidCore);

    const torusGeo = bucket.geo(new THREE.TorusGeometry(major, tube, 64, 160));
    const spin = new THREE.Group();
    group.add(spin);

    // Far wall of the tube — soft fill so the shell has thickness, not a second neon ring.
    const innerMat = shaderMat(bucket, FRAG_BUBBLE, {
      color: cyanBias, opacity: 0.48, power: 0.0, vertex: VERT_ENERGY, side: THREE.BackSide, mood: 0.03,
    });
    const innerShell = new THREE.Mesh(torusGeo, innerMat);
    innerShell.renderOrder = 3;
    spin.add(innerShell);

    const shellMat = shaderMat(bucket, FRAG_BUBBLE, {
      color: cyanBias, opacity: 0.82, power: 1.0, vertex: VERT_ENERGY, side: THREE.FrontSide, mood: 0.04,
    });
    const shell = new THREE.Mesh(torusGeo, shellMat);
    shell.renderOrder = 4;
    spin.add(shell);

    const sparkRng = mulberry32(4401);
    const sparkGeo = fillSparkGeo(bucket, sparkRng, 164, function (rng) {
      const u = rng() * Math.PI * 2;
      const v = rng() * Math.PI * 2;
      const tr = tube * (0.16 + Math.sqrt(rng()) * 0.72);
      const arm = major + tr * Math.cos(v);
      return [arm * Math.cos(u), arm * Math.sin(u), tr * Math.sin(v)];
    });
    const sparkMat = neuralSparkMat(bucket, cyanBias, { opacity: 1.0, white: 0.92, size: 0.08, mood: 0.02 });
    const sparks = new THREE.Points(sparkGeo, sparkMat);
    sparks.renderOrder = 6;
    spin.add(sparks);

    const hazeRng = mulberry32(808);
    const hazeGeo = fillSparkGeo(bucket, hazeRng, 28, function (rng) {
      const u = rng() * Math.PI * 2;
      const radial = major + tube * 0.15 + rng() * 0.52;
      return [radial * Math.cos(u), radial * Math.sin(u), (rng() - 0.5) * 0.42];
    });
    const hazeMat = neuralSparkMat(bucket, cyanBias, { opacity: 0.72, white: 0.78, size: 0.058, mood: 0.02 });
    const hazeSparks = new THREE.Points(hazeGeo, hazeMat);
    hazeSparks.renderOrder = 5;
    spin.add(hazeSparks);

    scene.add(group);
    return {
      group: group,
      bucket: bucket,
      cameraZ: 3.65,
      animate: function (state) {
        const speed = state.cfg.spin * 0.45;
        const pulse = state.cfg.pulse;
        const turb = state.cfg.turbulence;
        applyPaint(group, state.color, state.mood, state.cfg);
        group.scale.setScalar(1 + 0.016 * Math.sin(state.now * 0.0012) * pulse);
        const t = state.now * 0.001 * (0.55 + 0.45 * turb);
        if (shellMat.uniforms) {
          shellMat.uniforms.uTime.value = t;
          shellMat.uniforms.uTurbulence.value = turb;
        }
        if (innerMat.uniforms) {
          innerMat.uniforms.uTime.value = t * 0.85;
          innerMat.uniforms.uTurbulence.value = turb;
        }
        if (sparkMat.uniforms) sparkMat.uniforms.uTime.value = t;
        if (hazeMat.uniforms) hazeMat.uniforms.uTime.value = t * 0.92 + 1.4;
        spin.rotation.z += state.dt * 0.055 * (0.35 + speed);
      },
    };
  }

  const FRAG_APEX_CORE = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uWhite;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "void main() {",
    "  vec3 N = normalize(vNormal);",
    "  vec3 V = normalize(vView);",
    "  float facing = abs(dot(N, V));",
    "  float fres = pow(1.0 - facing, 2.4);",
    "  float body = pow(facing, 0.42);",
    "  float alpha = (body * 0.62 + fres * 0.38) * uOpacity;",
    "  if (alpha < 0.02) discard;",
    "  vec3 champagne = mix(uColor, vec3(1.0, 0.96, 0.86), 0.55 + uWhite * 0.25);",
    "  vec3 col = mix(champagne, vec3(1.0), clamp(fres * 0.55 + body * 0.35, 0.0, 0.72));",
    "  gl_FragColor = vec4(col, min(alpha, 0.92));",
    "}",
  ].join("\n");

  const FRAG_APEX_STREAM = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "uniform float uPhase;",
    "varying vec2 vUv;",
    "void main() {",
    "  float across = abs(vUv.y - 0.5) * 2.0;",
    "  float edge = pow(clamp(1.0 - across, 0.0, 1.0), 2.8);",
    "  float tip = smoothstep(0.0, 0.08, vUv.x) * smoothstep(1.0, 0.68, vUv.x);",
    "  float dash = 0.48 + 0.52 * pow(0.5 + 0.5 * sin(vUv.x * 24.0 - uTime * 0.65 + uPhase), 1.05);",
    "  float pulse = 0.65 + 0.35 * sin(vUv.x * 9.0 + uPhase * 1.7 - uTime * 0.9);",
    "  float a = edge * tip * dash * pulse * uOpacity;",
    "  if (a < 0.012) discard;",
    "  vec3 col = mix(uColor, vec3(1.0, 0.95, 0.82), clamp(edge * 0.5 + pulse * 0.25, 0.0, 1.0));",
    "  gl_FragColor = vec4(col, a);",
    "}",
  ].join("\n");

  function createApex(scene, color) {
    const bucket = makeBucket();
    const group = new THREE.Group();
    group.name = "apex";
    const rng = mulberry32(4141);
    const sprite = softSprite(bucket);

    function apexTint(user) {
      const gold = new THREE.Color("#e6cfa0").lerp(new THREE.Color("#fff0cc"), 0.35);
      const base = { h: 0, s: 0, l: 0 };
      const hue = { h: 0, s: 0, l: 0 };
      gold.getHSL(base);
      (user || gold).getHSL(hue);
      let dh = hue.h - base.h;
      if (dh > 0.5) dh -= 1;
      if (dh < -0.5) dh += 1;
      return new THREE.Color().setHSL((base.h + dh * 0.12 + 1) % 1, Math.min(0.55, base.s * 0.35 + 0.18), 0.72);
    }

    const warm = apexTint(color);

    addDisc(bucket, group, 0.72, FRAG_MYSTIC_ATMOS, {
      color: warm, opacity: 0.28, power: 2.2, white: 0.08, z: -0.12, mood: 0.04,
    });
    group.children[group.children.length - 1].renderOrder = 0;

    addDisc(bucket, group, 0.42, FRAG_DISC, {
      color: warm, opacity: 0.38, power: 1.25, white: 0.22, z: -0.06, mood: 0.03,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    const coreMat = shaderMat(bucket, FRAG_APEX_CORE, {
      color: warm, opacity: 0.88, white: 0.12, mood: 0.04, vertex: VERT_GLASS,
    });
    const coreSphere = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(0.19, 48, 40)), coreMat);
    coreSphere.renderOrder = 3;
    group.add(coreSphere);

    const coreGlowMat = addDisc(bucket, group, 0.16, FRAG_DISC, {
      color: warm, opacity: 0.55, power: 1.1, white: 0.35, z: 0.04, mood: 0.05,
    });
    group.children[group.children.length - 1].renderOrder = 4;

    const streams = new THREE.Group();
    streams.renderOrder = 2;
    const streamList = [];
    const nodePos = [];
    const streamCount = Math.min(10, MAX_APEX_STREAMS);

    for (let i = 0; i < streamCount; i++) {
      const major = 0.52 + rng() * 0.72;
      const minor = major * (0.78 + rng() * 0.22);
      const start = rng() * Math.PI * 2;
      const span = (0.45 + rng() * 0.42) * Math.PI;
      const tilt = { x: (rng() - 0.5) * 1.4, y: rng() * Math.PI * 2, z: (rng() - 0.5) * 0.65 };
      const phase = rng() * 6.2832;
      const wobble = 0.02 + rng() * 0.05;
      const width = 0.003 + rng() * 0.004;
      const pts = sampleArcPath(major, minor, start, span, tilt, 96, wobble, phase, 0);
      const mesh = new THREE.Mesh(
        bucket.geo(buildStrip(pts, width)),
        shaderMat(bucket, FRAG_APEX_STREAM, {
          color: warm,
          opacity: 0.22 + rng() * 0.18,
          white: 0.08,
          phase: phase,
          mood: 0.04,
          timeScale: 0.7 + rng() * 0.8,
        })
      );
      streams.add(mesh);
      const entry = {
        mesh: mesh,
        phase: phase,
        speed: (rng() - 0.5) * 0.55,
        spin: 0.3 + rng() * 0.7,
      };
      streamList.push(entry);

      const nodes = 3 + Math.floor(rng() * 4);
      for (let n = 0; n < nodes; n++) {
        const idx = Math.floor(rng() * (pts.length - 1));
        nodePos.push(pts[idx].x, pts[idx].y, pts[idx].z);
      }

      if (rng() > 0.55) {
        const mid = Math.floor(pts.length * (0.35 + rng() * 0.3));
        const branch = pts[mid].clone();
        branch.lerp(pts[Math.min(pts.length - 1, mid + 8)], 0.35);
        branch.add(new THREE.Vector3((rng() - 0.5) * 0.08, (rng() - 0.5) * 0.08, (rng() - 0.5) * 0.05));
        const spurMesh = new THREE.Mesh(
          bucket.geo(buildStrip([pts[mid], branch], width * 0.85)),
          shaderMat(bucket, FRAG_APEX_STREAM, {
            color: warm,
            opacity: 0.16 + rng() * 0.12,
            white: 0.06,
            phase: phase + 1.2,
            mood: 0.03,
            timeScale: 1.1,
          })
        );
        streams.add(spurMesh);
        streamList.push({ mesh: spurMesh, phase: phase, speed: entry.speed * 0.8, spur: true });
      }
    }
    group.add(streams);

    const nodeCount = Math.min(Math.floor(nodePos.length / 3), MAX_APEX_NODES);
    const nodeGeo = bucket.geo(new THREE.BufferGeometry());
    nodeGeo.setAttribute("position", new THREE.Float32BufferAttribute(nodePos.slice(0, nodeCount * 3), 3));
    const nodes = new THREE.Points(
      nodeGeo,
      pointsMat(bucket, warm, sprite, { opacity: 0.72, white: 0.25, size: 0.045, mood: 0.06 })
    );
    nodes.renderOrder = 3;
    group.add(nodes);

    scene.add(group);
    return {
      group: group,
      bucket: bucket,
      cameraZ: 4.35,
      animate: function (state) {
        const speed = state.cfg.spin * 0.55;
        const pulse = state.cfg.pulse;
        const turb = state.cfg.turbulence;
        const live = apexTint(state.color);
        applyPaint(group, live, state.mood, state.cfg);
        const streamBoost = 1 + state.mood * 0.85;
        const t = state.now * 0.001;

        coreSphere.scale.setScalar(
          (1 + 0.06 * Math.sin(state.now * 0.0016) * pulse) * (0.94 + state.mood * 0.08)
        );
        if (coreMat.uniforms) {
          coreMat.uniforms.uWhite.value = 0.12 + state.mood * 0.18 + (pulse > 0 ? 0.04 * Math.sin(state.now * 0.002) : 0);
          coreMat.uniforms.uOpacity.value = 0.82 + state.mood * 0.12;
        }
        if (coreGlowMat.uniforms) {
          const breath = pulse <= 0 ? 1 : 0.9 + 0.1 * Math.sin(state.now * 0.0024) * Math.min(pulse, 1.35);
          coreGlowMat.uniforms.uOpacity.value = (0.5 + state.mood * 0.15) * breath;
        }

        streams.rotation.y += state.dt * 0.04 * (0.35 + speed) * streamBoost;
        streams.rotation.x = Math.sin(state.now * 0.00025) * 0.12 * turb;
        streams.rotation.z = Math.cos(state.now * 0.00018) * 0.08 * turb;

        streamList.forEach(function (s) {
          s.mesh.rotation.y += state.dt * s.speed * (0.3 + speed) * streamBoost;
          s.mesh.rotation.x += state.dt * s.spin * 0.12 * turb;
          if (s.mesh.material.uniforms) {
            const scale = (s.mesh.material.userData && s.mesh.material.userData.timeScale) || 1;
            if (s.mesh.material.uniforms.uTime) {
              s.mesh.material.uniforms.uTime.value = t * scale * streamBoost;
            }
          }
        });

        nodes.rotation.y += state.dt * 0.05 * (0.35 + speed) * streamBoost;
        nodes.rotation.z -= state.dt * 0.03 * (0.3 + speed);
      },
    };
  }

  // Aether only. Fire filament sphere — ridge crests + warm body; do not route through FRAG_PLASMA.
  const FRAG_AETHER = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "uniform float uPhase;",
    "uniform float uPower;",
    "uniform float uWhite;",
    "uniform float uTurbulence;",
    "varying vec3 vObj;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "float hash13(vec3 p) {",
    "  p = fract(p * 0.1031);",
    "  p += dot(p, p.yzx + 33.33);",
    "  return fract((p.x + p.y) * p.z);",
    "}",
    "float noise(vec3 p) {",
    "  vec3 i = floor(p);",
    "  vec3 f = fract(p);",
    "  f = f * f * (3.0 - 2.0 * f);",
    "  return mix(",
    "    mix(mix(hash13(i), hash13(i + vec3(1.0, 0.0, 0.0)), f.x),",
    "        mix(hash13(i + vec3(0.0, 1.0, 0.0)), hash13(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),",
    "    mix(mix(hash13(i + vec3(0.0, 0.0, 1.0)), hash13(i + vec3(1.0, 0.0, 1.0)), f.x),",
    "        mix(hash13(i + vec3(0.0, 1.0, 1.0)), hash13(i + vec3(1.0, 1.0, 1.0)), f.x), f.y),",
    "    f.z);",
    "}",
    "float fbm(vec3 p) {",
    "  float v = 0.0;",
    "  float a = 0.5;",
    "  for (int i = 0; i < 4; i++) {",
    "    v += a * noise(p);",
    "    p = p * 2.02 + vec3(1.7, 9.2, 2.4);",
    "    a *= 0.5;",
    "  }",
    "  return v;",
    "}",
    "float crest(float x, float sharp) {",
    "  return pow(1.0 - abs(sin(x)), sharp);",
    "}",
    "void main() {",
    "  vec3 N = normalize(vNormal);",
    "  vec3 V = normalize(vView);",
    "  float facing = abs(dot(N, V));",
    "  float rim = pow(1.0 - facing, 1.85);",
    "  vec3 sp = normalize(vObj);",
    "  float lon = atan(sp.z, sp.x);",
    "  float lat = asin(clamp(sp.y, -1.0, 1.0));",
    "  float turb = clamp(uTurbulence, 0.0, 2.0);",
    "  float t = uTime * (0.28 + 0.22 * turb) + uPhase;",
    "  float wLon = fbm(vec3(lon * 0.7, lat * 1.1, t * 0.28));",
    "  float wLat = fbm(vec3(lat * 0.8 + 3.1, lon * 0.6, t * 0.2 + 1.4));",
    "  float lonAmp = 1.0 + 1.65 * turb;",
    "  float latAmp = 0.45 + 0.9 * turb;",
    "  float lonW = lon + (wLon - 0.5) * lonAmp + t * 0.22 + uPhase;",
    "  float latW = lat + (wLat - 0.5) * latAmp + (0.14 + 0.2 * turb) * sin(lon * 2.1 - t * 0.7);",
    "  lonW += (0.2 + 0.28 * turb) * sin(latW * 2.4 + t);",
    "  float sharp = mix(20.0, 10.5, clamp(turb * 0.5, 0.0, 1.0));",
    "  float aArc = crest(latW * 7.4 + lonW * 0.62 + wLon * 3.8, sharp);",
    "  float bArc = crest(lonW * 6.2 + latW * 1.65 + wLat * 3.1, sharp);",
    "  float cArc = crest((latW + lonW) * 5.2 + wLon * 2.8, sharp);",
    "  float dArc = crest((latW * 1.9 - lonW) * 4.1 + wLat * 4.2, sharp);",
    "  vec3 rp = vec3(lonW * 1.65, latW * 2.7, t * 0.18);",
    "  float ridgePow = mix(18.0, 10.5, clamp(turb * 0.5, 0.0, 1.0));",
    "  float ridge = pow(clamp(1.0 - abs(fbm(rp) * 2.0 - 1.0), 0.0, 1.0), ridgePow);",
    "  float knots = clamp((aArc * bArc + bArc * cArc) * 2.1, 0.0, 1.0);",
    "  float lines = max(max(aArc, bArc), max(cArc, dArc * 0.82));",
    "  lines = max(lines, ridge * 0.78);",
    "  lines = max(lines, knots * 0.28);",
    "  lines = pow(clamp(lines, 0.0, 1.0), 1.62);",
    "  lines *= 0.22 + 0.78 * smoothstep(0.0, 0.2, facing);",
    "  float front = step(0.5, uPower);",
    "  float coreRad = dot(vObj.xy, vObj.xy);",
    "  float core = front * exp(-coreRad * 7.2) * pow(facing, 0.58);",
    "  core *= 0.55 + 0.45 * exp(-coreRad * 22.0);",
    "  vec3 fireP = vec3(lonW * 3.1 + t * 0.34, latW * 2.6 - t * 0.24, t * 0.42 + uPhase * 0.35);",
    "  float fireA = fbm(fireP);",
    "  float fireB = fbm(fireP * 1.85 + vec3(2.2, 5.1, 0.8));",
    "  float fireWisp = pow(clamp(fireA * (0.65 + 0.35 * fireB), 0.0, 1.0), 1.15);",
    "  float onFil = smoothstep(0.18, 0.52, lines);",
    "  float fire = onFil * fireWisp * (0.42 + 0.58 * facing);",
    "  vec3 lickP = vec3(lonW * 11.5 + t * 0.41, latW * 9.2 - t * 0.36, t * 0.55 + uPhase);",
    "  float lickBase = fbm(lickP * 1.6);",
    "  float jagA = crest(lickP.x * 16.0 + lickBase * 5.2 + t * 1.35, 32.0);",
    "  float jagB = crest(lickP.y * 19.0 - lickBase * 4.1 + t * 0.95, 28.0);",
    "  float jagC = crest(lickP.z * 12.0 + jagA * 2.8, 22.0);",
    "  float tongue = pow(clamp(jagA * jagB * (0.4 + 0.6 * jagC), 0.0, 1.0), 2.4);",
    "  float rise = smoothstep(0.12, 0.88, fbm(lickP * vec3(2.1, 3.4, 1.2) + vec3(0.0, t * 0.28, 0.0)));",
    "  float onFilTight = smoothstep(0.22, 0.58, lines);",
    "  float licks = onFilTight * tongue * rise * (0.38 + 0.62 * facing);",
    "  float body = 0.032 + 0.09 * facing + 0.05 * rim;",
    "  float feat = max(lines * 0.96 + fire * 0.22, core * 0.52);",
    "  float limb = smoothstep(0.0, 0.36, facing);",
    "  float alpha = (body + feat * 0.82) * mix(0.18, 1.0, limb);",
    "  alpha *= uOpacity;",
    "  if (alpha < 0.02) discard;",
    "  vec3 deep = vec3(0.72, 0.14, 0.0);",
    "  vec3 gold = vec3(1.0, 0.5, 0.05);",
    "  vec3 solar = vec3(1.0, 0.58, 0.04);",
    "  vec3 tint = mix(deep, max(uColor, deep), 0.62);",
    "  vec3 col = mix(tint, gold, clamp(0.05 + lines * 0.82 + rim * 0.07, 0.0, 1.0));",
    "  vec3 ember = vec3(1.0, 0.4, 0.03);",
    "  vec3 flame = vec3(1.0, 0.24, 0.02);",
    "  col = mix(col, mix(ember, flame, fireA), fire * 0.48);",
    "  col = mix(col, mix(vec3(1.0, 0.62, 0.06), flame, 0.55), licks * 0.42);",
    "  float lift = clamp(core * 0.55 + knots * 0.04 + uWhite * 0.16, 0.0, 0.44);",
    "  col = mix(col, solar, lift);",
    "  col = min(col, mix(tint, solar, 0.68));",
    "  alpha = min(0.84, alpha + licks * 0.14);",
    "  gl_FragColor = vec4(col, alpha);",
    "}",
  ].join("\n");

  const FRAG_AETHER_ARC = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "uniform float uPhase;",
    "uniform float uStreak;",
    "varying vec2 vUv;",
    "void main() {",
      "  float across = abs(vUv.y - 0.5) * 2.0;",
      "  float edge = pow(clamp(1.0 - across, 0.0, 1.0), 2.05);",
    "  float flow = 0.58 + 0.42 * pow(0.5 + 0.5 * sin(vUv.x * uStreak * 6.28318 - uTime * 1.6 + uPhase), 1.15);",
    "  float tip = smoothstep(0.0, 0.07, vUv.x) * smoothstep(1.0, 0.93, vUv.x);",
    "  vec3 deep = max(uColor, vec3(1.0, 0.38, 0.02));",
    "  vec3 hot = mix(vec3(1.0, 0.55, 0.06), vec3(1.0, 0.78, 0.22), flow);",
    "  vec3 col = mix(deep, hot, 0.45 + flow * 0.4);",
    "  float a = edge * flow * tip * uOpacity;",
    "  if (a < 0.02) discard;",
    "  gl_FragColor = vec4(col, a);",
    "}",
  ].join("\n");

function createAether(scene, color) {
    // Orange-gold fiery plasma: soft atmos bloom, filament ridges, soft ribbons (no torii), embers.
    const bucket = makeBucket();
    const group = new THREE.Group();
    group.name = "aether";
    const sprite = softSprite(bucket);
    const rng = mulberry32(9090);

    function aetherTint(user) {
      // Hue nudge only. RGB lerp from calm cyan into orange passes through muddy copper.
      const fire = new THREE.Color("#ff6a00").lerp(new THREE.Color("#ffb347"), 0.5);
      const base = { h: 0, s: 0, l: 0 };
      const hue = { h: 0, s: 0, l: 0 };
      fire.getHSL(base);
      (user || fire).getHSL(hue);
      let dh = hue.h - base.h;
      if (dh > 0.5) dh -= 1;
      if (dh < -0.5) dh += 1;
      return new THREE.Color().setHSL((base.h + dh * 0.07 + 1) % 1, 0.96, 0.52);
    }

    const warm = aetherTint(color);

    addDisc(bucket, group, 2.85, FRAG_MYSTIC_ATMOS, {
      color: warm, opacity: 0.34, power: 1.05, white: 0.0, z: -0.48, mood: 0.05,
    });
    group.children[group.children.length - 1].renderOrder = 0;

    addDisc(bucket, group, 2.2, FRAG_MYSTIC_ATMOS, {
      color: warm, opacity: 0.38, power: 1.45, white: 0.0, z: -0.32, mood: 0.05,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    addDisc(bucket, group, 1.55, FRAG_DISC, {
      color: warm, opacity: 0.22, power: 2.1, white: 0.0, z: -0.16, mood: 0.03,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    const backMat = shaderMat(bucket, FRAG_AETHER, {
      color: warm, opacity: 0.68, power: 0.0, phase: 1.7, white: 0.02, mood: 0.05,
      vertex: VERT_ENERGY, side: THREE.BackSide,
    });
    const back = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(0.96, 64, 48)), backMat);
    back.renderOrder = 2;
    group.add(back);

    const plasmaMat = shaderMat(bucket, FRAG_AETHER, {
      color: warm, opacity: 0.82, power: 1.0, phase: 0.2, white: 0.03, mood: 0.06,
      vertex: VERT_ENERGY, side: THREE.FrontSide,
    });
    const plasma = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(1.02, 72, 56)), plasmaMat);
    plasma.renderOrder = 3;
    group.add(plasma);

    function shellPoints(count, innerR, outerR, bias) {
      const pos = [];
      for (let i = 0; i < count; i++) {
        const dir = new THREE.Vector3(rng() - 0.5, rng() - 0.5, rng() - 0.5);
        if (dir.lengthSq() < 1e-8) dir.set(0, 1, 0);
        dir.normalize();
        const radius = innerR + Math.pow(rng(), bias) * (outerR - innerR);
        pos.push(dir.x * radius, dir.y * radius, dir.z * radius);
      }
      return pos;
    }

    const fineCount = Math.min(220, MAX_AETHER_POINTS);
    const emberCount = Math.min(100, MAX_AETHER_POINTS - fineCount);
    const sparkCount = MAX_AETHER_POINTS - fineCount - emberCount;
    const fineGeo = bucket.geo(new THREE.BufferGeometry());
    fineGeo.setAttribute("position", new THREE.Float32BufferAttribute(shellPoints(fineCount, 0.22, 1.02, 1.05), 3));
    const fine = new THREE.Points(
      fineGeo,
      pointsMat(bucket, warm, sprite, { opacity: 0.38, white: 0.02, size: 0.018, mood: 0.04 })
    );
    const emberGeo = bucket.geo(new THREE.BufferGeometry());
    emberGeo.setAttribute("position", new THREE.Float32BufferAttribute(shellPoints(emberCount, 0.72, 1.28, 0.4), 3));
    const embers = new THREE.Points(
      emberGeo,
      pointsMat(bucket, warm, sprite, { opacity: 0.62, white: 0.06, size: 0.055, mood: 0.05 })
    );
    const sparkGeo = bucket.geo(new THREE.BufferGeometry());
    sparkGeo.setAttribute("position", new THREE.Float32BufferAttribute(shellPoints(sparkCount, 0.9, 1.44, 0.28), 3));
    const sparks = new THREE.Points(
      sparkGeo,
      pointsMat(bucket, warm, sprite, { opacity: 0.72, white: 0.1, size: 0.068, mood: 0.05 })
    );
    fine.renderOrder = 4;
    embers.renderOrder = 5;
    sparks.renderOrder = 5;
    group.add(fine);
    group.add(embers);
    group.add(sparks);

    const arcs = new THREE.Group();
    arcs.renderOrder = 4;
    const arcList = [];
    // Soft interior ribbons only — no torus meshes (ring risk vs mockup).
    const ribbonCount = Math.min(8, MAX_AETHER_ARCS);
    for (let i = 0; i < ribbonCount; i++) {
      const tight = i < 4;
      const mesh = new THREE.Mesh(
        bucket.geo(buildRibbonGeometry({
          radius: tight ? 0.32 + rng() * 0.22 : 0.55 + rng() * 0.28,
          waves: 2 + Math.floor(rng() * 4),
          phase: rng() * 6.2832,
          radAmp: tight ? 0.04 + rng() * 0.08 : 0.08 + rng() * 0.12,
          zAmp: 0.14 + rng() * (tight ? 0.22 : 0.38),
          width: tight ? 0.012 + rng() * 0.014 : 0.018 + rng() * 0.016,
          zWaves: 1 + Math.floor(rng() * 3),
          segments: 140,
        })),
        shaderMat(bucket, FRAG_AETHER_ARC, {
          color: warm,
          opacity: 0.28 + rng() * 0.2,
          white: 0.04,
          streaks: 2 + Math.floor(rng() * 4),
          phase: rng() * 6.2832,
          mood: 0.05,
          timeScale: 0.65 + rng() * 1.15,
        })
      );
      mesh.rotation.set(rng() * Math.PI, rng() * 6.2832, rng() * Math.PI);
      arcs.add(mesh);
      arcList.push({ mesh: mesh, speed: (rng() - 0.5) * 0.7 });
    }
    group.add(arcs);

    const core = new THREE.Group();
    core.renderOrder = 6;
    const coreMat = addDisc(bucket, core, 0.22, FRAG_DISC, {
      color: warm, opacity: 0.52, power: 1.08, white: 0.1, z: 0.05, mood: 0.02,
    });
    group.add(core);

    const pedestal = new THREE.Group();
    pedestal.position.y = -1.36;
    const floor = new THREE.Mesh(
      bucket.geo(new THREE.CircleGeometry(1.0, 48)),
      shaderMat(bucket, FRAG_DISC, { color: warm, opacity: 0.26, power: 1.55, white: 0.05, mood: 0.03 })
    );
    floor.rotation.x = -Math.PI / 2;
    pedestal.add(floor);
    group.add(pedestal);
    group.position.y = 0.2;

    scene.add(group);
    return {
      group: group,
      bucket: bucket,
      cameraZ: 4.35,
      animate: function (state) {
        const speed = state.cfg.spin * 0.6;
        const pulse = state.cfg.pulse;
        const turb = state.cfg.turbulence;
        const live = aetherTint(state.color);
        applyPaint(group, live, state.mood, state.cfg);
        group.scale.setScalar(1 + 0.018 * Math.sin(state.now * 0.0015) * pulse);
        const swirl = state.now * 0.001 * (0.45 + speed);
        plasmaMat.uniforms.uTime.value = swirl;
        backMat.uniforms.uTime.value = swirl * 0.82;
        plasmaMat.uniforms.uTurbulence.value = turb;
        backMat.uniforms.uTurbulence.value = turb;
        fine.rotation.y += state.dt * 0.07 * (0.4 + speed);
        embers.rotation.y -= state.dt * 0.1 * (0.4 + speed);
        embers.rotation.x = Math.sin(state.now * 0.0003) * 0.16;
        sparks.rotation.z += state.dt * 0.08 * (0.4 + speed);
        arcs.rotation.y += state.dt * 0.08 * (0.4 + speed);
        arcs.rotation.x = Math.sin(state.now * 0.0002) * 0.18;
        arcList.forEach(function (arc) {
          arc.mesh.rotation.y += state.dt * arc.speed * (0.4 + speed);
          arc.mesh.rotation.x += state.dt * arc.speed * 0.35 * (0.4 + speed);
          if (arc.mesh.material && arc.mesh.material.uniforms && arc.mesh.material.uniforms.uTime) {
            const scale = arc.mesh.material.userData.timeScale || 1;
            arc.mesh.material.uniforms.uTime.value = state.now * 0.0016 * scale;
          }
        });
        core.scale.setScalar(1 + 0.1 * Math.sin(state.now * 0.0032) * pulse);
        if (coreMat.uniforms) {
          const breath = pulse <= 0 ? 1 : 0.92 + 0.08 * Math.sin(state.now * 0.003) * Math.min(pulse, 1.35);
          coreMat.uniforms.uOpacity.value *= breath;
        }
      },
    };
  }

  function ensureHost(root) {
    let host = root.querySelector("#orb-webgl-host");
    if (!host) {
      host = document.createElement("div");
      host.id = "orb-webgl-host";
      host.style.cssText = "width:100%;height:100%;min-height:280px;display:none;";
      const canvas2d = root.querySelector("canvas");
      if (canvas2d && canvas2d.parentNode) canvas2d.parentNode.insertBefore(host, canvas2d);
      else root.appendChild(host);
    }
    return host;
  }

  function createController(root) {
    if (typeof THREE === "undefined") return null;
    const host = ensureHost(root);
    const label = root.querySelector(".orb-state");
    const canvas2d = root.querySelector("canvas");

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 30);
    camera.position.z = 4.2;
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
      premultipliedAlpha: false,
      preserveDrawingBuffer: true,
    });
    renderer.setClearColor(0x000000, 0);
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    host.appendChild(renderer.domElement);

    let styleName = "";
    let parts = null;
    let mood = 0;
    let running = false;
    let frame = 0;
    let last = 0;
    let appliedSize = 0;
    const fillMode = !!(root && root.classList && root.classList.contains("orb-fill"));

    function setSize(px) {
      if (fillMode) {
        const w = Math.max(1, root.clientWidth || window.innerWidth || 1);
        const h = Math.max(1, root.clientHeight || window.innerHeight || 1);
        host.style.width = "100%";
        host.style.height = "100%";
        host.style.minHeight = "0";
        renderer.setSize(w, h, true);
        camera.aspect = w / h;
        // Keep orb visual size ≈ px: larger canvas would otherwise magnify the same FOV.
        camera.zoom = Math.max(0.05, (px * 1.08) / h);
        camera.updateProjectionMatrix();
        appliedSize = px;
        return;
      }
      const w = px;
      const h = Math.round(px * 1.08);
      host.style.width = w + "px";
      host.style.height = h + "px";
      host.style.minHeight = h + "px";
      renderer.setSize(w, h, true);
      camera.aspect = w / h;
      camera.zoom = 1;
      camera.updateProjectionMatrix();
      if (root) root.style.minHeight = h + 28 + "px";
      appliedSize = px;
    }

    function onWindowResize() {
      if (!fillMode || !appliedSize) return;
      setSize(appliedSize);
    }
    if (fillMode) window.addEventListener("resize", onWindowResize);

    function rebuild(style) {
      if (parts) {
        if (parts.group) scene.remove(parts.group);
        if (parts.bucket) parts.bucket.dispose();
        parts = null;
      }
      styleName = style;
      const color = hexToColor(readOrbNode().calm, "#50cdff");
      if (style === "mystic") parts = createMystic(scene, color);
      else if (style === "aether") parts = createAether(scene, color);
      else if (style === "neural") parts = createNeural(scene, color);
      else if (style === "apex") parts = createApex(scene, color);
      if (parts && parts.cameraZ) camera.position.z = parts.cameraZ;
    }

    function setVisible(webgl) {
      host.style.display = webgl ? "block" : "none";
      if (canvas2d) canvas2d.style.display = webgl ? "none" : "block";
    }

    function tick(now) {
      if (!running) return;
      frame = requestAnimationFrame(tick);
      const cfg = readOrbNode();
      const hero = !!HERO[cfg.style];
      setVisible(hero);
      if (!hero) return;

      const dt = Math.min(0.05, last ? (now - last) / 1000 : 0.016);
      last = now;
      const thinking = (window.__energyOrbMode || "calm") === "thinking";
      const target = thinking ? 1 : 0;
      mood += (target - mood) * (1 - Math.exp(-dt / 0.45));

      const liveColor = hexToColor(cfg.calm, "#50cdff").lerp(hexToColor(cfg.thinking, "#b388ff"), mood);
      try {
        if (!parts || styleName !== cfg.style) rebuild(cfg.style);
      } catch (err) {
        window.__orbError = String(err && (err.stack || err));
      }
      if (appliedSize !== cfg.size) setSize(cfg.size);
      if (parts && parts.cameraZ && Math.abs(camera.position.z - parts.cameraZ) > 0.01) {
        camera.position.z = parts.cameraZ;
      }

      if (parts && parts.animate) {
        try {
          parts.animate({ now: now, dt: dt, mood: mood, color: liveColor, cfg: cfg });
        } catch (err) {
          window.__orbError = String(err && (err.stack || err));
        }
      }

      if (label) {
        label.textContent = mood >= 0.5 ? "THINKING" : "CALM";
        label.style.color = "#" + liveColor.getHexString();
      }
      renderer.render(scene, camera);
    }

    return {
      start: function () {
        if (running) return;
        running = true;
        last = 0;
        frame = requestAnimationFrame(tick);
      },
      stop: function () {
        running = false;
        cancelAnimationFrame(frame);
      },
      isHero: function (style) {
        return !!HERO[style];
      },
    };
  }

  window.__orbBuild = "webgl-mystic-aether-neural-apex";
  window.__orbWebGL = {
    HERO: HERO,
    MAX: {
      mystic: MAX_MYSTIC_POINTS,
      aether: MAX_AETHER_POINTS,
      neural: MAX_NEURAL_POINTS,
      apex: { streams: MAX_APEX_STREAMS, nodes: MAX_APEX_NODES },
      arcs: MAX_AETHER_ARCS,
      panes: MAX_NEURAL_PANES,
    },
    attach: function (element) {
      if (element.__orbWebGLCtrl) return element.__orbWebGLCtrl;
      const ctrl = createController(element);
      element.__orbWebGLCtrl = ctrl;
      if (ctrl) ctrl.start();
      return ctrl;
    },
  };
})();
