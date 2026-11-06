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

  function readOrbNode() {
    const node = document.getElementById("orb-config");
    return {
      style: node ? node.getAttribute("data-style") || "lightning" : "lightning",
      calm: node ? node.getAttribute("data-calm-color") || "#50cdff" : "#50cdff",
      thinking: node ? node.getAttribute("data-thinking-color") || "#b388ff" : "#b388ff",
      size: Math.max(200, Math.min(480, parseInt((node && node.getAttribute("data-size")) || "360", 10) || 360)),
      spin: parseFloat((node && node.getAttribute("data-spin-speed")) || "1") || 1,
      turbulence: parseFloat((node && node.getAttribute("data-turbulence")) || "1") || 1,
      pulse: parseFloat((node && node.getAttribute("data-pulse")) || "1") || 1,
      glow: parseFloat((node && node.getAttribute("data-glow")) || "1") || 1,
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
    return 0.62 + 0.38 * (cfg.glow || 1);
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
        const op = (p.opacity + p.mood * mood) * (p.glow ? g : 1);
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
    let lat = -0.2 + rng() * 1.6;
    const n = 6 + Math.floor(rng() * 4);
    for (let i = 0; i < n; i++) {
      lon += 0.28 + rng() * 0.62;
      lat += (rng() - 0.42) * 0.48;
      const r = 0.9 + rng() * 0.16;
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

  const FRAG_BUBBLE = [
    "uniform vec3 uColor;",
    "uniform float uOpacity;",
    "uniform float uTime;",
    "varying vec3 vObj;",
    "varying vec3 vNormal;",
    "varying vec3 vView;",
    "void main() {",
    "  vec3 N = normalize(vNormal);",
    "  vec3 V = normalize(vView);",
    "  float fres = pow(1.0 - abs(dot(N, V)), 2.15);",
    "  float rim = smoothstep(0.2, 0.98, fres);",
    "  float crescent = pow(max(dot(N, normalize(vec3(-0.85, 0.25, 0.45))), 0.0), 1.6);",
    "  float alpha = rim * (0.28 + crescent * 0.38) * uOpacity;",
    "  if (alpha < 0.02) discard;",
    "  vec3 col = mix(uColor, vec3(1.0), clamp(crescent * 0.35, 0.0, 0.65));",
    "  gl_FragColor = vec4(col, alpha);",
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

function createMystic(scene, color) {
    // Cyan filament / JARVIS volume: plasma ball, hot core, thin flare, faint rings, soft pedestal.
    const bucket = makeBucket();
    const group = new THREE.Group();
    group.name = "mystic";
    const sprite = softSprite(bucket);

    addDisc(bucket, group, 1.7, FRAG_DISC, {
      color: color, opacity: 0.12, power: 2.8, white: 0.0, z: -0.25, mood: 0.03,
    });

    const plasmaMat = shaderMat(bucket, FRAG_PLASMA, {
      color: color, opacity: 0.78, white: 0, mood: 0.06, glow: false,
      vertex: VERT_ENERGY, side: THREE.FrontSide,
    });
    const plasma = new THREE.Mesh(bucket.geo(new THREE.SphereGeometry(1.0, 72, 56)), plasmaMat);
    group.add(plasma);

    const halo = new THREE.Mesh(
      bucket.geo(new THREE.SphereGeometry(1.12, 48, 36)),
      shaderMat(bucket, FRAG_BUBBLE, {
        color: color, opacity: 0.16, vertex: VERT_ENERGY, side: THREE.FrontSide, mood: 0.04, glow: false,
      })
    );
    group.add(halo);

    const rings = new THREE.Group();
    const ringSpecs = [
      { r: 0.62, rx: 0.55, op: 0.28 },
      { r: 0.84, rx: 1.05, op: 0.2 },
    ];
    ringSpecs.forEach(function (spec) {
      const mesh = new THREE.Mesh(
        bucket.geo(new THREE.TorusGeometry(spec.r, 0.006, 8, 120)),
        shaderMat(bucket, FRAG_RING, { color: color, opacity: spec.op, white: 0.35, mood: 0.04, timeScale: 0.4 })
      );
      mesh.rotation.x = spec.rx;
      rings.add(mesh);
    });
    group.add(rings);

    const core = new THREE.Group();
    const coreMat = addDisc(bucket, core, 0.16, FRAG_DISC, {
      color: color, opacity: 1, power: 0.85, white: 0.92, z: 0.04, mood: 0.02, glow: false,
    });
    group.add(core);

    const flareMat = addDisc(bucket, group, 1, FRAG_FLARE, {
      color: color, opacity: 0.9, white: 0.8, z: 0.12, mood: 0.02, glow: false,
    });
    const flareMesh = group.children[group.children.length - 1];
    flareMesh.scale.set(2.7, 0.11, 1);

    const hud = new THREE.Mesh(
      bucket.geo(new THREE.TorusGeometry(1.38, 0.004, 8, 100)),
      shaderMat(bucket, FRAG_RING, { color: color, opacity: 0.16, white: 0.1, mood: 0.02 })
    );
    hud.rotation.x = 0.12;
    group.add(hud);

    const pedestal = new THREE.Group();
    pedestal.position.y = -1.38;
    for (let ring = 0; ring < 4; ring++) {
      const radius = 0.26 + ring * 0.22;
      const mesh = new THREE.Mesh(
        bucket.geo(new THREE.RingGeometry(radius, radius + 0.008, 64)),
        basicMat(bucket, color, { opacity: 0.22 - ring * 0.04, white: 0.06, mood: 0.02 })
      );
      mesh.rotation.x = -Math.PI / 2;
      pedestal.add(mesh);
    }
    const beam = new THREE.Mesh(
      bucket.geo(new THREE.CylinderGeometry(0.04, 0.07, 0.5, 10)),
      basicMat(bucket, color, { opacity: 0.28, white: 0.08, mood: 0.04 })
    );
    beam.position.y = 0.3;
    pedestal.add(beam);
    const floor = new THREE.Mesh(
      bucket.geo(new THREE.CircleGeometry(0.95, 40)),
      shaderMat(bucket, FRAG_DISC, { color: color, opacity: 0.2, power: 1.7, white: 0.04, mood: 0.03 })
    );
    floor.rotation.x = -Math.PI / 2;
    pedestal.add(floor);
    group.add(pedestal);
    group.position.y = 0.22;

    const sparkPos = [];
    const sparkRng = mulberry32(77);
    for (let i = 0; i < MAX_MYSTIC_POINTS; i++) {
      const dir = new THREE.Vector3(sparkRng() - 0.5, sparkRng() - 0.5, sparkRng() - 0.5).normalize();
      const radius = 0.96 + sparkRng() * 0.08;
      sparkPos.push(dir.x * radius, dir.y * radius, dir.z * radius);
    }
    const sparkGeo = bucket.geo(new THREE.BufferGeometry());
    sparkGeo.setAttribute("position", new THREE.Float32BufferAttribute(sparkPos, 3));
    const sparks = new THREE.Points(
      sparkGeo,
      pointsMat(bucket, color, sprite, { opacity: 0.8, white: 0.55, size: 0.02, mood: 0.05, glow: false })
    );
    group.add(sparks);

    scene.add(group);
    return {
      group: group,
      bucket: bucket,
      cameraZ: 4.7,
      animate: function (state) {
        const speed = 0.25 + state.cfg.spin * 0.35;
        applyPaint(group, state.color, state.mood, state.cfg);
        group.scale.setScalar(1 + 0.015 * Math.sin(state.now * 0.0014) * state.cfg.pulse);
        plasma.rotation.y += state.dt * 0.06 * speed;
        rings.rotation.z += state.dt * 0.05 * speed;
        sparks.rotation.y -= state.dt * 0.04 * speed;
        plasmaMat.uniforms.uTime.value = state.now * 0.001;
        core.scale.setScalar(1 + 0.08 * Math.sin(state.now * 0.0028) * state.cfg.pulse);
        if (coreMat.uniforms) coreMat.uniforms.uOpacity.value *= 0.92 + 0.08 * Math.sin(state.now * 0.003);
        if (flareMat.uniforms) flareMat.uniforms.uOpacity.value *= 0.88 + 0.12 * Math.sin(state.now * 0.0024);
      },
    };
  }

function createNeural(scene, color) {
    // Translucent glass bubble: bright rim, dark hollow centre, inner panes, rim dust.
    const bucket = makeBucket();
    const group = new THREE.Group();
    group.name = "neural";
    const sprite = softSprite(bucket);

    const shell = new THREE.Mesh(
      bucket.geo(new THREE.SphereGeometry(1.0, 72, 56)),
      shaderMat(bucket, FRAG_BUBBLE, {
        color: color, opacity: 1, vertex: VERT_ENERGY, side: THREE.FrontSide, mood: 0.06, glow: false,
      })
    );
    const bloom = new THREE.Mesh(
      bucket.geo(new THREE.SphereGeometry(1.16, 48, 36)),
      shaderMat(bucket, FRAG_BUBBLE, {
        color: color, opacity: 0.45, vertex: VERT_ENERGY, side: THREE.FrontSide, mood: 0.05, glow: false,
      })
    );
    group.add(bloom);
    group.add(shell);

    const panes = new THREE.Group();
    const paneSpecs = [
      { s: [1.05, 0.55, 0.28], r: [0.4, 0.2, 0.6], op: 0.45 },
      { s: [0.7, 1.0, 0.22], r: [1.1, 0.4, -0.3], op: 0.32 },
      { s: [0.85, 0.4, 0.2], r: [-0.5, 0.9, 0.8], op: 0.28 },
      { s: [0.6, 0.75, 0.18], r: [0.2, -0.7, 1.1], op: 0.24 },
    ].slice(0, MAX_NEURAL_PANES);
    paneSpecs.forEach(function (spec) {
      const mesh = new THREE.Mesh(
        bucket.geo(new THREE.SphereGeometry(0.72, 36, 24)),
        shaderMat(bucket, FRAG_PANE, {
          color: color, opacity: spec.op, vertex: VERT_ENERGY, side: THREE.FrontSide, mood: 0.04, glow: false,
        })
      );
      mesh.scale.set(spec.s[0], spec.s[1], spec.s[2]);
      mesh.rotation.set(spec.r[0], spec.r[1], spec.r[2]);
      panes.add(mesh);
    });
    group.add(panes);

    const dustRng = mulberry32(4401);
    const dustPos = [];
    let guard = 0;
    const dustCap = Math.max(24, MAX_NEURAL_POINTS - 24);
    while (dustPos.length / 3 < dustCap && guard < dustCap * 4) {
      guard += 1;
      const dir = new THREE.Vector3(dustRng() - 0.5, dustRng() - 0.5, dustRng() - 0.5).normalize();
      if (dir.x > 0.05 && dustRng() < 0.78) continue;
      const radius = 0.96 + dustRng() * 0.16;
      dustPos.push(dir.x * radius, dir.y * radius, dir.z * radius);
    }
    const dustGeo = bucket.geo(new THREE.BufferGeometry());
    dustGeo.setAttribute("position", new THREE.Float32BufferAttribute(dustPos, 3));
    const dust = new THREE.Points(
      dustGeo,
      pointsMat(bucket, color, sprite, { opacity: 0.95, white: 0.45, size: 0.018, mood: 0.04, glow: false })
    );
    group.add(dust);

    const bokehRng = mulberry32(808);
    const bokehPos = [];
    const bokehCount = Math.min(24, MAX_NEURAL_POINTS - dustPos.length / 3);
    for (let i = 0; i < bokehCount; i++) {
      const dir = new THREE.Vector3(bokehRng() - 0.5, bokehRng() - 0.5, bokehRng() - 0.5).normalize();
      const radius = 1.15 + bokehRng() * 0.45;
      bokehPos.push(dir.x * radius, dir.y * radius, dir.z * radius);
    }
    const bokehGeo = bucket.geo(new THREE.BufferGeometry());
    bokehGeo.setAttribute("position", new THREE.Float32BufferAttribute(bokehPos, 3));
    const bokeh = new THREE.Points(
      bokehGeo,
      pointsMat(bucket, color, sprite, { opacity: 0.35, white: 0.15, size: 0.11, mood: 0.03, glow: false })
    );
    group.add(bokeh);

    scene.add(group);
    return {
      group: group,
      bucket: bucket,
      cameraZ: 3.55,
      animate: function (state) {
        const speed = 0.2 + state.cfg.spin * 0.35;
        applyPaint(group, state.color, state.mood, state.cfg);
        group.scale.setScalar(1 + 0.02 * Math.sin(state.now * 0.0012) * state.cfg.pulse);
        shell.rotation.y += state.dt * 0.08 * speed;
        panes.rotation.y -= state.dt * 0.12 * speed;
        panes.rotation.x = Math.sin(state.now * 0.0002) * 0.08;
        dust.rotation.y += state.dt * 0.05 * speed;
        bokeh.rotation.z += state.dt * 0.03 * speed;
        if (shell.material.uniforms) shell.material.uniforms.uTime.value = state.now * 0.001;
      },
    };
  }

function createAether(scene, color) {
    // Orange-gold fiery plasma: ember shell, chaotic arcs, bright tangled core.
    const bucket = makeBucket();
    const group = new THREE.Group();
    group.name = "aether";
    const sprite = softSprite(bucket);
    const rng = mulberry32(9090);
    const warm = color.clone().lerp(new THREE.Color("#ff8c00"), 0.35);

    function shellPoints(count, inner, outer, bias) {
      const pos = [];
      for (let i = 0; i < count; i++) {
        const dir = new THREE.Vector3(rng() - 0.5, rng() - 0.5, rng() - 0.5).normalize();
        const radius = inner + Math.pow(rng(), bias) * (outer - inner);
        pos.push(dir.x * radius, dir.y * radius, dir.z * radius);
      }
      return pos;
    }

    const fineCount = Math.floor(MAX_AETHER_POINTS * 0.78);
    const emberCount = MAX_AETHER_POINTS - fineCount;
    const fineGeo = bucket.geo(new THREE.BufferGeometry());
    fineGeo.setAttribute("position", new THREE.Float32BufferAttribute(shellPoints(fineCount, 0.45, 1.18, 0.55), 3));
    const fine = new THREE.Points(
      fineGeo,
      pointsMat(bucket, warm, sprite, { opacity: 0.55, white: 0.2, size: 0.016, mood: 0.05, glow: false })
    );
    const emberGeo = bucket.geo(new THREE.BufferGeometry());
    emberGeo.setAttribute("position", new THREE.Float32BufferAttribute(shellPoints(emberCount, 0.4, 1.15, 0.8), 3));
    const embers = new THREE.Points(
      emberGeo,
      pointsMat(bucket, warm, sprite, { opacity: 0.7, white: 0.7, size: 0.07, mood: 0.05, glow: false })
    );
    group.add(fine);
    group.add(embers);

    const arcs = new THREE.Group();
    const arcList = [];
    for (let i = 0; i < MAX_AETHER_ARCS; i++) {
      const radius = 0.48 + rng() * 0.78;
      const arcLen = 0.28 + rng() * 0.85;
      const mesh = new THREE.Mesh(
        bucket.geo(new THREE.TorusGeometry(radius, 0.006 + rng() * 0.01, 6, 28, arcLen)),
        basicMat(bucket, warm, { opacity: 0.28 + rng() * 0.5, white: 0.2 + rng() * 0.45, mood: 0.05, glow: false })
      );
      mesh.rotation.set(rng() * 6.2832, rng() * 6.2832, rng() * 6.2832);
      arcs.add(mesh);
      arcList.push({ mesh: mesh, speed: (rng() - 0.5) * 0.4 });
    }
    group.add(arcs);

    const knot = new THREE.Group();
    for (let i = 0; i < 7; i++) {
      const mesh = new THREE.Mesh(
        bucket.geo(new THREE.TorusGeometry(0.16 + rng() * 0.2, 0.012 + rng() * 0.01, 8, 24, 0.7 + rng() * 1.4)),
        basicMat(bucket, warm, { opacity: 0.75, white: 0.65, mood: 0.04, glow: false })
      );
      mesh.rotation.set(rng() * 6.2832, rng() * 6.2832, rng() * 6.2832);
      knot.add(mesh);
    }
    const coreMat = addDisc(bucket, knot, 0.18, FRAG_DISC, {
      color: warm, opacity: 0.95, power: 0.9, white: 0.9, z: 0.02, mood: 0.02, glow: false,
    });
    group.add(knot);

    scene.add(group);
    return {
      group: group,
      bucket: bucket,
      cameraZ: 3.7,
      animate: function (state) {
        const speed = 0.3 + state.cfg.spin * 0.6;
        const live = state.color.clone().lerp(new THREE.Color("#ff8c00"), 0.28);
        applyPaint(group, live, state.mood, state.cfg);
        group.rotation.y += state.dt * 0.08 * speed;
        group.rotation.x = Math.sin(state.now * 0.00015) * 0.12;
        fine.rotation.y += state.dt * 0.04 * speed;
        arcs.rotation.z += state.dt * 0.05 * speed;
        arcList.forEach(function (arc) {
          arc.mesh.rotation.y += state.dt * arc.speed * speed;
        });
        knot.rotation.y -= state.dt * 0.35 * speed;
        knot.rotation.z += state.dt * 0.2 * speed;
        knot.scale.setScalar(1 + 0.1 * Math.sin(state.now * 0.003) * state.cfg.pulse);
        if (coreMat.uniforms) coreMat.uniforms.uOpacity.value *= 0.9 + 0.1 * Math.sin(state.now * 0.004);
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

    function setSize(px) {
      const w = px;
      const h = Math.round(px * 1.08);
      host.style.width = w + "px";
      host.style.height = h + "px";
      host.style.minHeight = h + "px";
      renderer.setSize(w, h, true);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      if (root) root.style.minHeight = h + 28 + "px";
      appliedSize = px;
    }

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
