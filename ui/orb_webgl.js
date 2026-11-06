/* WebGL hero orb (Three.js r160). Expects global THREE. Attaches to window.__orbWebGL.
   Styles: mystic = cyan filament sphere, aether = fiery plasma, neural = glass bubble. */
(function () {
  const HERO = { mystic: 1, aether: 1, neural: 1 };
  const MAX_MYSTIC_POINTS = 280;
  const MAX_AETHER_POINTS = 400;
  const MAX_NEURAL_POINTS = 360;
  const MAX_AETHER_ARCS = 24;
  const MAX_NEURAL_PANES = 4;
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

  // Neural only: wide fresnel glass shell — dark hollow centre, thick limb band with volume.
  // No face fill, no MeshPhysical transmission, no atan (seam-safe). Turbulence = rim shimmer.
  const FRAG_BUBBLE = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "uniform float uTurbulence;",
    "varying vec3 vObj;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "void main() {",
    "  vec3 N = normalize(vNormal);",
    "  vec3 V = normalize(vView);",
    "  float ndv = clamp(abs(dot(N, V)), 0.0, 1.0);",
    // Lower power → wider rim band (glass shell thickness, not a thin neon line).
    "  float fresWide = pow(1.0 - ndv, 1.45);",
    "  float fresEdge = pow(1.0 - ndv, 2.65);",
    "  float F0 = 0.045;",
    "  float schlick = F0 + (1.0 - F0) * pow(1.0 - ndv, 4.2);",
    // Soft translucent volume + brighter outer lip.
    "  float volume = smoothstep(0.08, 0.72, fresWide);",
    "  float softVol = pow(volume, 0.78);",
    "  float lip = smoothstep(0.22, 0.95, fresEdge);",
    "  float rimCore = pow(lip, 1.55);",
    "  float crescent = pow(max(dot(N, normalize(vec3(-0.72, 0.42, 0.35))), 0.0), 2.2);",
    "  float gloss = pow(max(dot(N, normalize(vec3(-0.55, 0.82, 0.22))), 0.0), 22.0);",
    "  float gloss2 = pow(max(dot(N, normalize(vec3(0.62, 0.55, 0.4))), 0.0), 40.0);",
    "  float turb = clamp(uTurbulence, 0.0, 2.0);",
    "  float nDot = dot(N, vec3(0.31, 0.67, 0.22));",
    "  float shimmer = 0.5 + 0.5 * sin(nDot * (4.6 + turb * 1.2) + uTime * (0.34 + 0.16 * turb) + vObj.y * 1.25);",
    "  float shell = softVol * (0.42 + schlick * 0.95) * (0.88 + crescent * 0.32);",
    "  shell += rimCore * 0.62;",
    "  shell += softVol * shimmer * (0.035 + 0.055 * turb);",
    "  shell += gloss * 0.72 + gloss2 * 0.28;",
    // Keep the face a dark void; allow a thicker shell band than a knife-edge.
    "  shell *= smoothstep(0.1, 0.42, fresWide);",
    "  float alpha = shell * uOpacity;",
    "  if (alpha < 0.012) discard;",
    "  vec3 col = mix(uColor * 0.55, uColor, softVol);",
    "  col = mix(col, vec3(0.58, 0.9, 1.0), clamp(crescent * 0.16 + gloss * 0.5 + gloss2 * 0.3, 0.0, 0.52));",
    "  gl_FragColor = vec4(col, min(alpha, 0.9));",
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

  // Neural only: additive bloom around the bubble — peak near the limb, dark inside.
  const FRAG_NEURAL_ATMOS = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uPower;",
    "varying vec2 vUv;",
    "void main() {",
    "  float d = length(vUv - vec2(0.5)) * 2.0;",
    "  float ring = exp(-pow((d - 0.56) * uPower, 2.0));",
    "  float halo = exp(-pow(max(d - 0.48, 0.0) * (uPower * 0.55), 2.0));",
    "  float a = (ring * 0.95 + halo * 0.55) * uOpacity;",
    "  a *= smoothstep(0.22, 0.5, d);",
    "  a *= smoothstep(1.12, 0.55, d);",
    "  if (a < 0.003) discard;",
    "  gl_FragColor = vec4(uColor, a);",
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

function createNeural(scene, color) {
    // Fresnel rim-only glass bubble: dark hollow centre, soft limb glow, ring atmos bloom,
    // sparse sparkles. Soft occlusion core keeps bloom from filling the void. No transmission.
    const bucket = makeBucket();
    const group = new THREE.Group();
    group.name = "neural";
    const sprite = softSprite(bucket);
    const cyanBias = color.clone().lerp(new THREE.Color("#6ee8ff"), 0.38);

    // Soft atmospheric bloom around the bubble (additive; centre killed in shader).
    addDisc(bucket, group, 3.7, FRAG_NEURAL_ATMOS, {
      color: cyanBias, opacity: 0.54, power: 1.05, white: 0.0, z: -0.58, mood: 0.04,
    });
    group.children[group.children.length - 1].renderOrder = 0;

    addDisc(bucket, group, 2.75, FRAG_NEURAL_ATMOS, {
      color: cyanBias, opacity: 0.38, power: 1.4, white: 0.0, z: -0.4, mood: 0.04,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    addDisc(bucket, group, 2.05, FRAG_NEURAL_ATMOS, {
      color: cyanBias, opacity: 0.18, power: 1.85, white: 0.0, z: -0.24, mood: 0.03,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    // Soft occlusion so the hollow reads black (not bloom leaking through the open shell).
    const voidMat = bucket.mat(new THREE.MeshBasicMaterial({
      color: new THREE.Color("#000000"),
      transparent: true,
      opacity: 1.0,
      depthWrite: false,
      toneMapped: false,
      side: THREE.FrontSide,
      blending: THREE.NormalBlending,
    }));
    const voidCore = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(0.88, 64, 48)), voidMat);
    voidCore.renderOrder = 2;
    group.add(voidCore);

    const shellMat = shaderMat(bucket, FRAG_BUBBLE, {
      color: cyanBias, opacity: 1.72, vertex: VERT_ENERGY, side: THREE.FrontSide, mood: 0.05,
    });
    const shell = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(1.0, 96, 72)), shellMat);
    shell.renderOrder = 4;
    // Backface for glass-wall thickness at the limb without filling the void.
    const innerMat = shaderMat(bucket, FRAG_BUBBLE, {
      color: cyanBias, opacity: 0.55, vertex: VERT_ENERGY, side: THREE.BackSide, mood: 0.03,
    });
    const innerShell = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(0.955, 72, 56)), innerMat);
    innerShell.renderOrder = 3;
    group.add(innerShell);
    group.add(shell);

    // Sparse sparkles near the glass limb / bloom field.
    const dustRng = mulberry32(4401);
    const dustPos = [];
    let guard = 0;
    const dustCap = Math.min(16, MAX_NEURAL_POINTS);
    while (dustPos.length / 3 < dustCap && guard < dustCap * 14) {
      guard += 1;
      const dir = new THREE.Vector3(dustRng() - 0.5, dustRng() - 0.5, dustRng() - 0.5).normalize();
      if (Math.abs(dir.z) < 0.32 && dustRng() < 0.7) continue;
      const radius = 0.98 + dustRng() * 0.34;
      dustPos.push(dir.x * radius, dir.y * radius, dir.z * radius);
    }
    const dustGeo = bucket.geo(new THREE.BufferGeometry());
    dustGeo.setAttribute("position", new THREE.Float32BufferAttribute(dustPos, 3));
    const dust = new THREE.Points(
      dustGeo,
      pointsMat(bucket, cyanBias, sprite, { opacity: 0.48, white: 0.3, size: 0.01, mood: 0.02 })
    );
    dust.renderOrder = 5;
    group.add(dust);

    const bokehRng = mulberry32(808);
    const bokehPos = [];
    const bokehCount = Math.min(3, MAX_NEURAL_POINTS - dustPos.length / 3);
    for (let i = 0; i < bokehCount; i++) {
      const dir = new THREE.Vector3(bokehRng() - 0.5, bokehRng() - 0.5, bokehRng() - 0.5).normalize();
      const radius = 1.2 + bokehRng() * 0.36;
      bokehPos.push(dir.x * radius, dir.y * radius, dir.z * radius);
    }
    const bokehGeo = bucket.geo(new THREE.BufferGeometry());
    bokehGeo.setAttribute("position", new THREE.Float32BufferAttribute(bokehPos, 3));
    const bokeh = new THREE.Points(
      bokehGeo,
      pointsMat(bucket, cyanBias, sprite, { opacity: 0.09, white: 0.04, size: 0.038, mood: 0.015 })
    );
    bokeh.renderOrder = 4;
    group.add(bokeh);

    scene.add(group);
    return {
      group: group,
      bucket: bucket,
      cameraZ: 3.65,
      animate: function (state) {
        const speed = state.cfg.spin * 0.45;
        const pulse = state.cfg.pulse;
        const turb = state.cfg.turbulence;
        const live = state.color.clone().lerp(new THREE.Color("#6ee8ff"), 0.28);
        applyPaint(group, live, state.mood, state.cfg);
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
        shell.rotation.y += state.dt * 0.05 * (0.35 + speed);
        innerShell.rotation.y -= state.dt * 0.03 * (0.35 + speed);
        dust.rotation.y += state.dt * 0.04 * (0.35 + speed);
        bokeh.rotation.z += state.dt * 0.022 * (0.35 + speed);
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
    "  float sharp = mix(11.0, 5.0, clamp(turb * 0.5, 0.0, 1.0));",
    "  float aArc = crest(latW * 5.4 + lonW * 0.48 + wLon * 3.0, sharp);",
    "  float bArc = crest(lonW * 4.3 + latW * 1.35 + wLat * 2.5, sharp);",
    "  float cArc = crest((latW + lonW) * 3.9 + wLon * 2.2, sharp);",
    "  float dArc = crest((latW * 1.6 - lonW) * 3.0 + wLat * 3.6, sharp);",
    "  vec3 rp = vec3(lonW * 1.2, latW * 2.1, t * 0.16);",
    "  float ridgePow = mix(12.0, 7.0, clamp(turb * 0.5, 0.0, 1.0));",
    "  float ridge = pow(clamp(1.0 - abs(fbm(rp) * 2.0 - 1.0), 0.0, 1.0), ridgePow);",
    "  float knots = clamp((aArc * bArc + bArc * cArc) * 3.8, 0.0, 1.0);",
    "  float lines = max(max(aArc, bArc), max(cArc, dArc * 0.8));",
    "  lines = max(lines, ridge);",
    "  lines = max(lines, knots * 0.9);",
    "  lines *= 0.28 + 0.72 * smoothstep(0.0, 0.22, facing);",
    "  float front = step(0.5, uPower);",
    "  float core = front * exp(-dot(vObj.xy, vObj.xy) * 6.4) * pow(facing, 0.5);",
    "  float body = 0.22 + 0.28 * facing + 0.18 * rim;",
    "  float feat = max(lines, core * 1.05);",
    "  float limb = smoothstep(0.0, 0.36, facing);",
    "  float alpha = (body + feat * 0.85) * mix(0.28, 1.0, limb);",
    "  alpha *= uOpacity;",
    "  if (alpha < 0.02) discard;",
    "  vec3 deep = vec3(1.0, 0.28, 0.0);",
    "  vec3 gold = vec3(1.0, 0.66, 0.1);",
    "  vec3 whiteHot = vec3(1.0, 0.94, 0.78);",
    "  vec3 tint = mix(deep, max(uColor, deep), 0.7);",
    "  vec3 col = mix(tint, gold, clamp(0.22 + lines * 0.55 + rim * 0.18, 0.0, 1.0));",
    "  float lift = clamp(core * 0.75 + knots * 0.18 + uWhite * 0.35, 0.0, 0.72);",
    "  col = mix(col, whiteHot, lift);",
    "  col = min(col, mix(tint, whiteHot, 0.78));",
    "  gl_FragColor = vec4(col, min(alpha, 0.92));",
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
    "  float edge = pow(clamp(1.0 - across, 0.0, 1.0), 1.35);",
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
    // Orange-gold fiery plasma: soft atmos bloom, filament ridges, arcs, ember sparks.
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

    addDisc(bucket, group, 2.7, FRAG_MYSTIC_ATMOS, {
      color: warm, opacity: 0.36, power: 1.12, white: 0.0, z: -0.46, mood: 0.05,
    });
    group.children[group.children.length - 1].renderOrder = 0;

    addDisc(bucket, group, 2.1, FRAG_MYSTIC_ATMOS, {
      color: warm, opacity: 0.42, power: 1.55, white: 0.0, z: -0.3, mood: 0.05,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    addDisc(bucket, group, 1.55, FRAG_DISC, {
      color: warm, opacity: 0.2, power: 2.2, white: 0.0, z: -0.16, mood: 0.03,
    });
    group.children[group.children.length - 1].renderOrder = 1;

    const backMat = shaderMat(bucket, FRAG_AETHER, {
      color: warm, opacity: 0.78, power: 0.0, phase: 1.7, white: 0.02, mood: 0.05,
      vertex: VERT_ENERGY, side: THREE.BackSide,
    });
    const back = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(0.96, 64, 48)), backMat);
    back.renderOrder = 2;
    group.add(back);

    const plasmaMat = shaderMat(bucket, FRAG_AETHER, {
      color: warm, opacity: 0.96, power: 1.0, phase: 0.2, white: 0.04, mood: 0.06,
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
      pointsMat(bucket, warm, sprite, { opacity: 0.5, white: 0.06, size: 0.018, mood: 0.04 })
    );
    const emberGeo = bucket.geo(new THREE.BufferGeometry());
    emberGeo.setAttribute("position", new THREE.Float32BufferAttribute(shellPoints(emberCount, 0.72, 1.28, 0.4), 3));
    const embers = new THREE.Points(
      emberGeo,
      pointsMat(bucket, warm, sprite, { opacity: 0.92, white: 0.18, size: 0.055, mood: 0.05 })
    );
    const sparkGeo = bucket.geo(new THREE.BufferGeometry());
    sparkGeo.setAttribute("position", new THREE.Float32BufferAttribute(shellPoints(sparkCount, 0.9, 1.44, 0.28), 3));
    const sparks = new THREE.Points(
      sparkGeo,
      pointsMat(bucket, warm, sprite, { opacity: 1, white: 0.4, size: 0.068, mood: 0.05 })
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
    const ribbonCount = Math.min(12, MAX_AETHER_ARCS);
    const torusCount = Math.min(6, MAX_AETHER_ARCS - ribbonCount);
    for (let i = 0; i < ribbonCount; i++) {
      const tight = i < 5;
      const mesh = new THREE.Mesh(
        bucket.geo(buildRibbonGeometry({
          radius: tight ? 0.36 + rng() * 0.26 : 0.66 + rng() * 0.32,
          waves: 2 + Math.floor(rng() * 4),
          phase: rng() * 6.2832,
          radAmp: tight ? 0.05 + rng() * 0.1 : 0.1 + rng() * 0.16,
          zAmp: 0.16 + rng() * (tight ? 0.28 : 0.5),
          width: tight ? 0.026 + rng() * 0.028 : 0.042 + rng() * 0.036,
          zWaves: 1 + Math.floor(rng() * 3),
          segments: 140,
        })),
        shaderMat(bucket, FRAG_AETHER_ARC, {
          color: warm,
          opacity: 0.4 + rng() * 0.26,
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
    for (let i = 0; i < torusCount; i++) {
      const mesh = new THREE.Mesh(
        bucket.geo(new THREE.TorusGeometry(
          0.42 + rng() * 0.58,
          0.014 + rng() * 0.014,
          12,
          96,
          2.1 + rng() * 3.1
        )),
        shaderMat(bucket, FRAG_AETHER_ARC, {
          color: warm,
          opacity: 0.38 + rng() * 0.24,
          white: 0.06,
          streaks: 2 + Math.floor(rng() * 3),
          phase: rng() * 6.2832,
          mood: 0.05,
          timeScale: 0.5 + rng() * 0.9,
        })
      );
      mesh.rotation.set(rng() * 6.2832, rng() * 6.2832, rng() * 6.2832);
      arcs.add(mesh);
      arcList.push({ mesh: mesh, speed: (rng() - 0.5) * 0.5 });
    }
    group.add(arcs);

    const core = new THREE.Group();
    core.renderOrder = 6;
    const coreMat = addDisc(bucket, core, 0.12, FRAG_DISC, {
      color: warm, opacity: 0.95, power: 0.75, white: 0.78, z: 0.06, mood: 0.02,
    });
    addDisc(bucket, core, 0.28, FRAG_DISC, {
      color: warm, opacity: 0.48, power: 1.5, white: 0.14, z: 0.03, mood: 0.03,
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

  window.__orbBuild = "webgl-mystic-aether-neural";
  window.__orbWebGL = {
    HERO: HERO,
    MAX: {
      mystic: MAX_MYSTIC_POINTS,
      aether: MAX_AETHER_POINTS,
      neural: MAX_NEURAL_POINTS,
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
