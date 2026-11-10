import json
import re

with open("/home/claw/.hermes/cache/scratch/apex-coaster/apex-05-multicolor-split-3d.html", "r") as f:
    html = f.read()

with open("/home/claw/.hermes/cache/scratch/apex-coaster/apex_telemetry.json", "r") as f:
    telemetry_data = json.load(f)

three_block = f"""<!-- STITCH_THREEJS_START:BLENDER_GLB_BENCHMARK -->
<div class="w-full h-full absolute inset-0" style="display:block;">
  <div id="threejs-container-BLENDER" style="width:100%;height:100%;cursor:grab;"></div>
</div>
<script type="importmap">
{{
  "imports": {{
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }}
}}
</script>
<script type="module">
import * as THREE from 'three';
import {{ GLTFLoader }} from 'three/addons/loaders/GLTFLoader.js';
import {{ RoomEnvironment }} from 'three/addons/environments/RoomEnvironment.js';
import {{ EffectComposer }} from 'three/addons/postprocessing/EffectComposer.js';
import {{ RenderPass }} from 'three/addons/postprocessing/RenderPass.js';
import {{ UnrealBloomPass }} from 'three/addons/postprocessing/UnrealBloomPass.js';

const TELEMETRY = {json.dumps(telemetry_data["samples"])};
const container = document.getElementById('threejs-container-BLENDER');
const width = container.clientWidth || 1360;
const height = container.clientHeight || 491;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x05070e);
scene.fog = new THREE.FogExp2(0x05070e, 0.011);

const camera = new THREE.PerspectiveCamera(44, width / height, 0.1, 400);
camera.position.set(0, 8.8, 22.5);

const renderer = new THREE.WebGLRenderer({{ antialias: true, powerPreference: 'high-performance' }});
renderer.setSize(width, height);
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.28;
container.appendChild(renderer.domElement);

// Studio HDR PMREM Environment Reflection Map (Crucial for realistic metallic steel speculars!)
const pmremGenerator = new THREE.PMREMGenerator(renderer);
scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 1.15;

// Post-Processing Pipeline: RenderPass + UnrealBloomPass (Selective Emissive Glow)
const composer = new EffectComposer(renderer);
const renderPass = new RenderPass(scene, camera);
composer.addPass(renderPass);
const bloomPass = new UnrealBloomPass(new THREE.Vector2(width, height), 0.52, 0.35, 0.68);
composer.addPass(bloomPass);

// Cinematic Multi-Zone Studio Lighting
scene.add(new THREE.HemisphereLight(0x93c5fd, 0x090d16, 0.95));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.6);
keyLight.position.set(16, 34, 24);
scene.add(keyLight);

const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.4);
rimLight.position.set(-22, 18, -16);
scene.add(rimLight);

// Phase Zone Accent Lights
const zoneLights = [
  {{ color: 0x06b6d4, intensity: 28, dist: 24, pos: [-10, 9, 2] }},
  {{ color: 0xf43f5e, intensity: 38, dist: 26, pos: [-1.5, 9, 2] }},
  {{ color: 0x8b5cf6, intensity: 30, dist: 24, pos: [5.0, 8, 2] }},
  {{ color: 0xf59e0b, intensity: 30, dist: 24, pos: [12.5, 7, 2] }},
  {{ color: 0x10b981, intensity: 22, dist: 24, pos: [0, 3, -5] }}
];
zoneLights.forEach(cfg => {{
  const pl = new THREE.PointLight(cfg.color, cfg.intensity, cfg.dist);
  pl.position.set(...cfg.pos);
  scene.add(pl);
}});

// Custom Architectural Telemetry Ground Floor + Radial Glowing Grid + Starfield Dome
const floorGeo = new THREE.PlaneGeometry(140, 140);
const floorMat = new THREE.MeshStandardMaterial({{
  color: 0x070a12,
  metalness: 0.85,
  roughness: 0.22
}});
const floorMesh = new THREE.Mesh(floorGeo, floorMat);
floorMesh.rotation.x = -Math.PI * 0.5;
floorMesh.position.y = -0.02;
scene.add(floorMesh);

const mainGrid = new THREE.GridHelper(90, 90, 0x1e293b, 0x0f172a);
mainGrid.position.y = 0.01;
scene.add(mainGrid);

// Concentric Telemetry Range Rings on the Ground Plane
[8, 16, 24, 32].forEach((rad, i) => {{
  const rGeo = new THREE.RingGeometry(rad - 0.04, rad + 0.04, 96);
  const rMat = new THREE.MeshBasicMaterial({{
    color: i === 1 ? 0x06b6d4 : (i === 2 ? 0xf43f5e : 0x334155),
    side: THREE.DoubleSide,
    transparent: true,
    opacity: i === 1 || i === 2 ? 0.35 : 0.18
  }});
  const rMesh = new THREE.Mesh(rGeo, rMat);
  rMesh.rotation.x = -Math.PI * 0.5;
  rMesh.position.y = 0.02;
  scene.add(rMesh);
}});

// Subtle Atmospheric Starfield / Dust Particles for 3D Depth & Rider POV Speed Feel
const starCount = 900;
const starPos = new Float32Array(starCount * 3);
const starColors = new Float32Array(starCount * 3);
const palette = [new THREE.Color(0x38bdf8), new THREE.Color(0xf43f5e), new THREE.Color(0xa855f7), new THREE.Color(0xfbbf24), new THREE.Color(0xffffff)];
for (let i = 0; i < starCount; i++) {{
  starPos[i * 3]     = (Math.random() - 0.5) * 95;
  starPos[i * 3 + 1] = 1.5 + Math.random() * 28;
  starPos[i * 3 + 2] = (Math.random() - 0.5) * 65;
  const col = palette[i % palette.length];
  starColors[i * 3]     = col.r;
  starColors[i * 3 + 1] = col.g;
  starColors[i * 3 + 2] = col.b;
}}
const starGeo = new THREE.BufferGeometry();
starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
starGeo.setAttribute('color', new THREE.BufferAttribute(starColors, 3));
const starMat = new THREE.PointsMaterial({{ size: 0.14, vertexColors: true, transparent: true, opacity: 0.65 }});
const starField = new THREE.Points(starGeo, starMat);
scene.add(starField);

// Load the 44,386-Face Blender Benchmark Coaster & 5 Articulated Train Cars
const carMeshes = [null, null, null, null, null];
const PHASE_MAT_OVERRIDE = {{
  'MAT_Track_Phase1_Cyan':    {{ color: 0x06b6d4, emissive: 0x06b6d4, emissiveIntensity: 0.55, metalness: 0.82, roughness: 0.18 }},
  'MAT_Track_Phase2_Crimson': {{ color: 0xf43f5e, emissive: 0xf43f5e, emissiveIntensity: 0.72, metalness: 0.82, roughness: 0.16 }},
  'MAT_Track_Phase3_Violet':  {{ color: 0x8b5cf6, emissive: 0x8b5cf6, emissiveIntensity: 0.58, metalness: 0.82, roughness: 0.18 }},
  'MAT_Track_Phase4_Amber':   {{ color: 0xf59e0b, emissive: 0xf59e0b, emissiveIntensity: 0.58, metalness: 0.82, roughness: 0.18 }},
  'MAT_Track_Phase5_Emerald': {{ color: 0x10b981, emissive: 0x10b981, emissiveIntensity: 0.52, metalness: 0.82, roughness: 0.18 }},
  'MAT_Running_Rail_Steel':   {{ color: 0xe2e8f0, emissive: 0x38bdf8, emissiveIntensity: 0.12, metalness: 0.95, roughness: 0.10 }},
  'MAT_Crosstie_Graphite':    {{ color: 0x1e293b, emissive: 0x000000, emissiveIntensity: 0.0,  metalness: 0.88, roughness: 0.28 }},
  'MAT_Tower_Column_Steel':   {{ color: 0x1e293b, emissive: 0x0f172a, emissiveIntensity: 0.15, metalness: 0.88, roughness: 0.30 }},
  'MAT_Concrete_Footer':      {{ color: 0x334155, emissive: 0x000000, emissiveIntensity: 0.0,  metalness: 0.20, roughness: 0.75 }},
  'MAT_Aviation_Beacon':      {{ color: 0xff1e42, emissive: 0xff1e42, emissiveIntensity: 2.80, metalness: 0.20, roughness: 0.10 }},
  'MAT_Catwalk_Steel':        {{ color: 0x334155, emissive: 0x06b6d4, emissiveIntensity: 0.08, metalness: 0.85, roughness: 0.32 }},
  'MAT_Tunnel_Portal_Cyan':   {{ color: 0x06b6d4, emissive: 0x06b6d4, emissiveIntensity: 1.90, metalness: 0.50, roughness: 0.15 }},
  'MAT_Car_Aero_Shell':       {{ color: 0xf8fafc, emissive: 0x38bdf8, emissiveIntensity: 0.18, metalness: 0.90, roughness: 0.10 }},
  'MAT_Car_Laser_Trim':       {{ color: 0xf43f5e, emissive: 0xf43f5e, emissiveIntensity: 2.10, metalness: 0.50, roughness: 0.15 }},
  'MAT_Car_Carbon_Seat':      {{ color: 0x0f172a, emissive: 0x000000, emissiveIntensity: 0.0,  metalness: 0.45, roughness: 0.40 }},
  'MAT_Car_Hydraulic_Bar':    {{ color: 0xf59e0b, emissive: 0xf59e0b, emissiveIntensity: 0.65, metalness: 0.75, roughness: 0.20 }},
  'MAT_Bogie_Wheel_Cyan':     {{ color: 0x38bdf8, emissive: 0x06b6d4, emissiveIntensity: 1.60, metalness: 0.40, roughness: 0.20 }}
}};

const trainRoot = new THREE.Group();
scene.add(trainRoot);
const carContainers = [0, 1, 2, 3, 4].map(() => {{
  const g = new THREE.Group();
  trainRoot.add(g);
  return g;
}});

// Add volumetric dual headlights to the Lead Car (carContainers[0])
const headSpot = new THREE.PointLight(0xffffff, 18, 12);
headSpot.position.set(1.1, 0.35, 0);
carContainers[0].add(headSpot);

const loader = new GLTFLoader();
loader.load('./apex_coaster.glb', (gltf) => {{
  const root = gltf.scene;
  const carsFound = [];
  root.traverse((child) => {{
    if (child.isMesh && child.material) {{
      const mName = child.material.name;
      if (PHASE_MAT_OVERRIDE[mName]) {{
        child.material = new THREE.MeshStandardMaterial(PHASE_MAT_OVERRIDE[mName]);
      }}
    }}
    if (child.name && /^Coaster_Car_[0-4]$/.test(child.name)) {{
      carsFound.push(child);
    }}
  }});

  carsFound.forEach((carNode) => {{
    const idx = parseInt(carNode.name.split('_').pop(), 10);
    carNode.position.set(0, 0, 0);
    carNode.rotation.set(0, 0, 0);
    carNode.scale.set(1.18, 1.18, 1.18);
    carContainers[idx].add(carNode);
    carMeshes[idx] = carNode;
  }});

  scene.add(root);
  window.__coasterLoaded = true;
}});

// Interpolate telemetry sample + full 3D Frenet/Banked Orientation Frame at normalized t in [0, 1)
function sampleTelemetry(tNorm) {{
  const t = ((tNorm % 1) + 1) % 1;
  const exactIdx = t * TELEMETRY.length;
  const i0 = Math.floor(exactIdx) % TELEMETRY.length;
  const i1 = (i0 + 1) % TELEMETRY.length;
  const frac = exactIdx - Math.floor(exactIdx);
  const s0 = TELEMETRY[i0];
  const s1 = TELEMETRY[i1];
  const lerp = (a, b) => a + (b - a) * frac;
  const pos = new THREE.Vector3(lerp(s0.pos[0], s1.pos[0]), lerp(s0.pos[1], s1.pos[1]), lerp(s0.pos[2], s1.pos[2]));
  const tan = new THREE.Vector3(lerp(s0.tan[0], s1.tan[0]), lerp(s0.tan[1], s1.tan[1]), lerp(s0.tan[2], s1.tan[2])).normalize();
  const up  = new THREE.Vector3(lerp(s0.up[0],  s1.up[0]),  lerp(s0.up[1],  s1.up[1]),  lerp(s0.up[2],  s1.up[2])).normalize();
  // Re-orthogonalize side & up with Gram-Schmidt so the 3x3 rotation matrix is orthonormal
  const side = tan.clone().cross(up).normalize();
  const orthoUp = side.clone().cross(tan).normalize();

  return {{
    t,
    pos,
    tan,
    up: orthoUp,
    side,
    alt: lerp(s0.alt, s1.alt),
    speed: lerp(s0.speed, s1.speed),
    g: lerp(s0.g, s1.g),
    pitch: lerp(s0.pitch, s1.pitch),
    bank: lerp(s0.bank, s1.bank),
    bpm: Math.round(lerp(s0.bpm, s1.bpm)),
    resp: lerp(s0.resp, s1.resp),
    grip: Math.round(lerp(s0.grip, s1.grip)),
    db: lerp(s0.db, s1.db),
    phase: s0.phase,
    phaseId: s0.phaseId
  }};
}}

// Place and orient each of the 5 articulated cars along the banked 3D spline
const rotMatrix = new THREE.Matrix4();
function updateArticulatedTrain(leadT) {{
  const CAR_SPACING_T = 0.0145; // Physical arc-length coupling between cars
  for (let c = 0; c < 5; c++) {{
    const carT = ((leadT - c * CAR_SPACING_T) % 1 + 1) % 1;
    const s = sampleTelemetry(carT);
    const containerGroup = carContainers[c];
    containerGroup.position.copy(s.pos);

    // In Blender export (+Z -> +Y, +Y -> -Z), car local axes are:
    // +X = forward (tan), +Y = up (orthoUp), +Z = right (side)
    rotMatrix.makeBasis(s.tan, s.up, s.side);
    containerGroup.quaternion.setFromRotationMatrix(rotMatrix);
  }}
}}

// Interactive Camera & Playback State
let progress = 0.14;
let isPaused = false;
let speedMultiplier = 1.0;
let cameraMode = 'ORBIT';
let camTheta = 0.14;
let camPhi = 0.22;
let camRadius = 21.5;
let isDragging = false;
let prevMouse = {{ x: 0, y: 0 }};

renderer.domElement.addEventListener('mousedown', (e) => {{
  isDragging = true;
  prevMouse = {{ x: e.clientX, y: e.clientY }};
}});
window.addEventListener('mouseup', () => {{ isDragging = false; }});
window.addEventListener('mousemove', (e) => {{
  if (!isDragging) return;
  camTheta -= (e.clientX - prevMouse.x) * 0.007;
  camPhi = Math.max(0.04, Math.min(1.25, camPhi + (e.clientY - prevMouse.y) * 0.007));
  prevMouse = {{ x: e.clientX, y: e.clientY }};
}});

let frameCounter = 4800;
function syncUI(sample) {{
  frameCounter++;
  const el = (id) => document.getElementById(id);
  if (el('hud-frame')) el('hud-frame').textContent = `FRAME: #${{frameCounter}}`;
  if (el('hud-x')) el('hud-x').textContent = `${{sample.pos.x.toFixed(1)}} m`;
  if (el('hud-y')) el('hud-y').textContent = `${{sample.alt.toFixed(1)}} ft`;
  if (el('hud-z')) el('hud-z').textContent = `${{sample.pos.z.toFixed(1)}} m`;
  if (el('hud-pitch')) {{
    const pSign = sample.pitch > 0 ? '+' : '';
    el('hud-pitch').textContent = `${{pSign}}${{sample.pitch.toFixed(1)}}° / BANK ${{sample.bank.toFixed(0)}}°`;
  }}
  if (el('scrub-phase-label')) {{
    const timeSec = (sample.t * 134.4).toFixed(1);
    el('scrub-phase-label').textContent = `● ${{sample.phase}} (T+${{timeSec}}s)`;
  }}
  if (el('scrub-pos-label')) {{
    el('scrub-pos-label').textContent = `SCRUB POSITION: ${{(sample.t * 100).toFixed(1)}}%`;
  }}
  if (el('scrub-playhead')) {{
    el('scrub-playhead').style.left = `${{(sample.t * 100).toFixed(2)}}%`;
  }}

  // Card 1: Slow Climb Live Metrics
  if (el('c1-speed')) el('c1-speed').innerHTML = `${{sample.phaseId === 1 ? sample.speed.toFixed(1) : '6.4'}} <span class="text-xs font-normal text-muted">MPH</span>`;
  if (el('c1-alt')) el('c1-alt').textContent = `Alt: ${{sample.alt.toFixed(1)}} FT`;
  const peMj = Math.min(120, Math.max(4, (sample.alt / 420.0) * 118.0)).toFixed(1);
  if (el('c1-pe-text')) el('c1-pe-text').innerHTML = `${{peMj}} MJ <span class="text-muted font-normal">/ 120 MJ</span>`;
  if (el('c1-pe-bar')) el('c1-pe-bar').style.width = `${{Math.min(100, (peMj / 120) * 100)}}%`;
  if (el('c1-grip-text')) el('c1-grip-text').textContent = `${{sample.grip}}% ${{sample.grip > 80 ? 'White-Knuckle' : 'Tension'}}`;
  if (el('c1-grip-bar')) el('c1-grip-bar').style.width = `${{sample.grip}}%`;

  // Card 2: Breathless Drop & Biometrics
  if (el('c2-speed')) el('c2-speed').innerHTML = `${{sample.speed.toFixed(1)}} <span class="text-xs font-normal text-muted">MPH</span>`;
  if (el('c2-resp')) el('c2-resp').textContent = `${{sample.resp.toFixed(1)}} L/MIN`;
  if (el('c2-apnea-note')) {{
    el('c2-apnea-note').textContent = sample.resp === 0
      ? '⚠️ NOBODY CAN BREATHE // ZERO-RESPIRATION APNEA LOCK'
      : `RESPIRATION ACTIVE: ${{sample.resp.toFixed(1)}} L/MIN VENTILATION`;
  }}
  if (el('c2-bpm')) el('c2-bpm').textContent = `${{sample.bpm}} BPM ${{sample.bpm > 160 ? '(TACHY)' : '(ELEVATED)'}}`;
  if (el('c2-db')) el('c2-db').textContent = `${{sample.db.toFixed(1)}} dB`;

  // Card 3: G-Force & Dynamics
  const gFormatted = (sample.g >= 0 ? '+' : '') + sample.g.toFixed(2) + ' G';
  if (el('c3-live-g')) el('c3-live-g').textContent = `${{gFormatted}} Instantaneous`;

  // Card 4: Live 5-Phase Block Matrix
  for (let p = 1; p <= 5; p++) {{
    const row = el(`sec-row-${{p}}`);
    const badge = el(`sec-badge-${{p}}`);
    if (row && badge) {{
      if (p === sample.phaseId) {{
        row.className = 'cursor-pointer flex items-center justify-between p-1.5 rounded bg-white/10 border border-white/40 shadow-sm transition-all';
        badge.textContent = 'LIVE SYNC ●';
        badge.className = 'text-[10px] font-bold bg-telemetry-crimson text-white px-1.5 py-0.5 rounded animate-pulse';
      }} else if (p < sample.phaseId) {{
        row.className = 'cursor-pointer flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline opacity-75';
        badge.textContent = 'COMPLETED';
        badge.className = 'text-[10px] text-muted font-bold';
      }} else {{
        row.className = 'cursor-pointer flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline';
        badge.textContent = 'ARMED';
        badge.className = 'text-[10px] text-telemetry-emerald font-bold';
      }}
    }}
  }}
}}

const clock = new THREE.Clock();
function animate() {{
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  const sample = sampleTelemetry(progress);

  if (!isPaused) {{
    // Realistic coaster kinematics: slow mechanical chain lift vs blistering drop/loop/airtime
    const baseRate = sample.phaseId === 1 ? 0.020 : (sample.phaseId === 2 ? 0.068 : (sample.phaseId === 3 ? 0.056 : (sample.phaseId === 4 ? 0.050 : 0.036)));
    progress = (progress + baseRate * dt * speedMultiplier) % 1.0;
  }}

  updateArticulatedTrain(progress);

  // Camera Modes with true banked up-vectors for Rider POV & Chase Cam!
  if (cameraMode === 'ORBIT') {{
    camera.up.set(0, 1, 0);
    camera.position.x = sample.pos.x * 0.28 + camRadius * Math.sin(camTheta) * Math.cos(camPhi);
    camera.position.y = Math.max(2.2, camRadius * Math.sin(camPhi) + 5.2);
    camera.position.z = camRadius * Math.cos(camTheta) * Math.cos(camPhi);
    camera.lookAt(sample.pos.x * 0.35, 6.2, 0);
  }} else if (cameraMode === 'RIDER_POV') {{
    const eyePos = sample.pos.clone().add(sample.up.clone().multiplyScalar(0.68)).add(sample.tan.clone().multiplyScalar(0.45));
    const lookTarget = eyePos.clone().add(sample.tan.clone().multiplyScalar(6.0)).add(sample.up.clone().multiplyScalar(-0.25));
    camera.position.copy(eyePos);
    camera.up.copy(sample.up);
    camera.lookAt(lookTarget);
  }} else if (cameraMode === 'SIDE_PROFILE') {{
    camera.up.set(0, 1, 0);
    camera.position.set(sample.pos.x * 0.45, 7.6, 22.5);
    camera.lookAt(sample.pos.x * 0.45, 6.8, 0);
  }} else if (cameraMode === 'CHASE_CAM') {{
    const trailSample = sampleTelemetry((progress - 0.055 + 1.0) % 1.0);
    const chasePos = trailSample.pos.clone().add(trailSample.up.clone().multiplyScalar(1.85)).add(trailSample.side.clone().multiplyScalar(1.25));
    camera.position.copy(chasePos);
    camera.up.set(0, 1, 0);
    camera.lookAt(sample.pos.clone().add(sample.up.clone().multiplyScalar(0.4)));
  }}

  syncUI(sample);
  composer.render();
}}
animate();

window.addEventListener('resize', () => {{
  const w = container.clientWidth || window.innerWidth;
  const h = container.clientHeight || 491;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  composer.setSize(w, h);
}});

// Expose deterministic stepping hook for headless video capture & interactive UI controls
window.apexSetCamera = (mode, btnEl) => {{
  cameraMode = mode;
  document.querySelectorAll('[data-cam-btn]').forEach(b => {{
    b.className = 'px-2.5 py-1 text-muted hover:text-on-surface transition-colors flex items-center gap-1';
  }});
  if (btnEl) {{
    btnEl.className = 'px-2.5 py-1 rounded bg-surface text-telemetry-cyan font-bold border border-outline shadow-sm flex items-center gap-1';
  }}
}};

window.apexScrubTo = (tVal) => {{
  progress = ((tVal % 1) + 1) % 1;
  const s = sampleTelemetry(progress);
  updateArticulatedTrain(progress);
  syncUI(s);
  composer.render();
}};

window.apexStepSimulation = (tVal, mode, thetaOverride, phiOverride) => {{
  isPaused = true;
  if (mode) cameraMode = mode;
  if (typeof thetaOverride === 'number') camTheta = thetaOverride;
  if (typeof phiOverride === 'number') camPhi = phiOverride;
  window.apexScrubTo(tVal);
}};

const scrubBar = document.getElementById('scrub-bar-track');
if (scrubBar) {{
  scrubBar.addEventListener('click', (e) => {{
    const rect = scrubBar.getBoundingClientRect();
    const clickT = (e.clientX - rect.left) / rect.width;
    window.apexScrubTo(clickT);
  }});
}}

const playBtn = document.getElementById('playback-btn');
if (playBtn) {{
  playBtn.addEventListener('click', () => {{
    isPaused = !isPaused;
    const icon = playBtn.querySelector('.material-symbols-outlined');
    const text = playBtn.querySelector('span:last-child');
    if (isPaused) {{
      icon.textContent = 'play_arrow';
      text.textContent = 'RESUME SIM';
    }} else {{
      icon.textContent = 'pause';
      text.textContent = 'LIVE PAUSE';
    }}
  }});
}}
</script>
<!-- STITCH_THREEJS_END:BLENDER_GLB_BENCHMARK -->"""

html = re.sub(
    r"<!-- STITCH_THREEJS_START:ANIMATION_8.*?<!-- STITCH_THREEJS_END:ANIMATION_8 -->",
    lambda _: three_block,
    html,
    flags=re.DOTALL,
)

replacements = [
    ('<span>Mesh Poly Count:</span>\n<span class="text-on-surface font-semibold">14,280 Traces</span>', '<span>Mesh Poly Count:</span>\n<span class="text-on-surface font-semibold">44,386 Faces (5-Car Train)</span>'),
    ('<span class="text-[10px] text-muted">FRAME: #3409</span>', '<span id="hud-frame" class="text-[10px] text-muted">FRAME: #4800</span>'),
    ('<div class="font-bold text-on-surface">-24.2 m</div>', '<div id="hud-x" class="font-bold text-on-surface">-24.2 m</div>'),
    ('<div class="font-bold text-telemetry-cyan">128.0 m</div>', '<div id="hud-y" class="font-bold text-telemetry-cyan">420.0 ft</div>'),
    ('<div class="font-bold text-on-surface">-4.8 m</div>', '<div id="hud-z" class="font-bold text-on-surface">0.0 m</div>'),
    ('<span class="text-telemetry-crimson font-bold tracking-tight animate-pulse">-89.5° SHEER DIVE</span>', '<span id="hud-pitch" class="text-telemetry-crimson font-bold tracking-tight animate-pulse">-89.5° SHEER DIVE</span>'),
    ('<span class="text-telemetry-crimson font-bold text-xs animate-pulse">● DROP LIP TRANSITION (T+38.2s)</span>', '<span id="scrub-phase-label" class="text-telemetry-crimson font-bold text-xs animate-pulse">● DROP LIP TRANSITION (T+38.2s)</span>'),
    ('<span class="text-muted text-[11px]">SCRUB POSITION: 28.5%</span>', '<span id="scrub-pos-label" class="text-muted text-[11px]">SCRUB POSITION: 28.5%</span>'),
    ('<div class="relative w-full h-3 bg-surface-container-lowest rounded-full overflow-hidden flex border border-outline">', '<div id="scrub-bar-track" class="relative w-full h-3.5 bg-surface-container-lowest rounded-full overflow-hidden flex border border-outline cursor-pointer"><div id="scrub-playhead" class="absolute top-0 bottom-0 w-1 bg-white shadow-[0_0_8px_#fff] z-20 pointer-events-none" style="left:28%;"></div>'),
    ('<button class="px-2.5 py-1 rounded bg-surface text-telemetry-cyan font-bold border border-outline shadow-sm flex items-center gap-1">\n<span class="material-symbols-outlined text-xs" data-icon="3d_rotation">3d_rotation</span> ORBIT 3D\n          </button>', '<button data-cam-btn onclick="window.apexSetCamera(\'ORBIT\', this)" class="px-2.5 py-1 rounded bg-surface text-telemetry-cyan font-bold border border-outline shadow-sm flex items-center gap-1"><span class="material-symbols-outlined text-xs" data-icon="3d_rotation">3d_rotation</span> ORBIT 3D</button>'),
    ('<button class="px-2.5 py-1 text-muted hover:text-on-surface transition-colors flex items-center gap-1">\n<span class="material-symbols-outlined text-xs" data-icon="visibility">visibility</span> RIDER POV\n          </button>', '<button data-cam-btn onclick="window.apexSetCamera(\'RIDER_POV\', this)" class="px-2.5 py-1 text-muted hover:text-on-surface transition-colors flex items-center gap-1"><span class="material-symbols-outlined text-xs" data-icon="visibility">visibility</span> RIDER POV</button>'),
    ('<button class="px-2.5 py-1 text-muted hover:text-on-surface transition-colors flex items-center gap-1">\n<span class="material-symbols-outlined text-xs" data-icon="view_sidebar">view_sidebar</span> SIDE PROFILE\n          </button>', '<button data-cam-btn onclick="window.apexSetCamera(\'SIDE_PROFILE\', this)" class="px-2.5 py-1 text-muted hover:text-on-surface transition-colors flex items-center gap-1"><span class="material-symbols-outlined text-xs" data-icon="view_sidebar">view_sidebar</span> SIDE PROFILE</button>'),
    ('<button class="px-2.5 py-1 text-muted hover:text-on-surface transition-colors flex items-center gap-1">\n<span class="material-symbols-outlined text-xs" data-icon="flight_takeoff">flight_takeoff</span> CHASE CAM\n          </button>', '<button data-cam-btn onclick="window.apexSetCamera(\'CHASE_CAM\', this)" class="px-2.5 py-1 text-muted hover:text-on-surface transition-colors flex items-center gap-1"><span class="material-symbols-outlined text-xs" data-icon="flight_takeoff">flight_takeoff</span> CHASE CAM</button>'),
    ('<span class="font-mono text-xl font-bold text-telemetry-cyan">6.4 <span class="text-xs font-normal text-muted">MPH</span></span>', '<span id="c1-speed" class="font-mono text-xl font-bold text-telemetry-cyan">6.4 <span class="text-xs font-normal text-muted">MPH</span></span>'),
    ('<span class="text-[9px] font-mono text-muted block mt-0.5">Crest: 420.0 FT</span>', '<span id="c1-alt" class="text-[9px] font-mono text-muted block mt-0.5">Crest: 420.0 FT</span>'),
    ('<span class="text-telemetry-cyan font-bold">98.4 MJ <span class="text-muted font-normal">/ 120 MJ</span></span>', '<span id="c1-pe-text" class="text-telemetry-cyan font-bold">98.4 MJ <span class="text-muted font-normal">/ 120 MJ</span></span>'),
    ('<div class="h-full bg-telemetry-cyan transition-all" style="width: 82%;"></div>', '<div id="c1-pe-bar" class="h-full bg-telemetry-cyan transition-all" style="width: 82%;"></div>'),
    ('<span class="text-on-surface font-bold">87% White-Knuckle</span>', '<span id="c1-grip-text" class="text-on-surface font-bold">87% White-Knuckle</span>'),
    ('<div class="h-full bg-gradient-to-r from-telemetry-cyan to-telemetry-amber" style="width: 87%;"></div>', '<div id="c1-grip-bar" class="h-full bg-gradient-to-r from-telemetry-cyan to-telemetry-amber" style="width: 87%;"></div>'),
    ('<span class="font-mono text-xl font-bold text-telemetry-crimson">128.4 <span class="text-xs font-normal text-muted">MPH</span></span>', '<span id="c2-speed" class="font-mono text-xl font-bold text-telemetry-crimson">128.4 <span class="text-xs font-normal text-muted">MPH</span></span>'),
    ('<span class="font-mono text-telemetry-crimson font-bold">0.0 L/MIN</span>', '<span id="c2-resp" class="font-mono text-telemetry-crimson font-bold">0.0 L/MIN</span>'),
    ('TOTAL INVOLUNTARY BREATH-HOLD: 6.2s ELAPSED', '<span id="c2-apnea-note">TOTAL INVOLUNTARY BREATH-HOLD: 6.2s ELAPSED</span>'),
    ('<span class="font-bold">188 BPM (TACHY)</span>', '<span id="c2-bpm" class="font-bold">188 BPM (TACHY)</span>'),
    ('<span class="text-on-surface font-bold">114.8 dB</span>', '<span id="c2-db" class="text-on-surface font-bold">114.8 dB</span>'),
    ('<span class="text-on-surface font-bold">+5.11 G Total Combined</span>', '<span id="c3-live-g" class="text-on-surface font-bold">+4.92 G Instantaneous</span>'),
    ('<div class="flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline">\n<span class="text-telemetry-cyan font-semibold flex items-center gap-1">\n<span class="material-symbols-outlined text-[11px]" data-icon="check_circle">check_circle</span> SEC 01 (6.4 mph)\n              </span>\n<span class="text-[10px] text-muted font-bold">COMPLETED</span>\n</div>', '<div id="sec-row-1" onclick="window.apexScrubTo(0.15)" class="cursor-pointer flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline"><span class="text-telemetry-cyan font-semibold flex items-center gap-1"><span class="material-symbols-outlined text-[11px]" data-icon="check_circle">check_circle</span> SEC 01 (Slow Climb)</span><span id="sec-badge-1" class="text-[10px] text-muted font-bold">COMPLETED</span></div>'),
    ('<div class="flex items-center justify-between p-1 rounded bg-telemetry-crimson/15 border border-telemetry-crimson/50 text-telemetry-crimson">\n<span class="font-bold flex items-center gap-1">\n<span class="material-symbols-outlined text-[11px] animate-spin" data-icon="sync">sync</span> SEC 02 (89.5° Plunge)\n              </span>\n<span class="text-[10px] font-bold bg-telemetry-crimson text-white px-1 rounded animate-pulse">ACTIVE</span>\n</div>', '<div id="sec-row-2" onclick="window.apexScrubTo(0.31)" class="cursor-pointer flex items-center justify-between p-1 rounded bg-telemetry-crimson/15 border border-telemetry-crimson/50 text-telemetry-crimson"><span class="font-bold flex items-center gap-1"><span class="material-symbols-outlined text-[11px]" data-icon="bolt">bolt</span> SEC 02 (89.5° Plunge)</span><span id="sec-badge-2" class="text-[10px] font-bold bg-telemetry-crimson text-white px-1 rounded animate-pulse">ACTIVE</span></div>'),
    ('<div class="flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline">\n<span class="text-telemetry-violet font-semibold">SEC 03 (Cobra Roll)</span>\n<span class="text-[10px] text-telemetry-violet font-bold">ARMED</span>\n</div>', '<div id="sec-row-3" onclick="window.apexScrubTo(0.50)" class="cursor-pointer flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline"><span class="text-telemetry-violet font-semibold">SEC 03 (Teardrop Loop)</span><span id="sec-badge-3" class="text-[10px] text-telemetry-violet font-bold">ARMED</span></div>'),
    ('<div class="flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline">\n<span class="text-telemetry-amber font-semibold">SEC 04 (-1.4G Camelback)</span>\n<span class="text-[10px] text-muted">STANDBY</span>\n</div>', '<div id="sec-row-4" onclick="window.apexScrubTo(0.68)" class="cursor-pointer flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline"><span class="text-telemetry-amber font-semibold">SEC 04 (-1.4G Airtime)</span><span id="sec-badge-4" class="text-[10px] text-muted">STANDBY</span></div>'),
    ('<div class="flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline">\n<span class="text-telemetry-emerald font-semibold">SEC 05 (Eddy Brakes)</span>\n<span class="text-[10px] text-telemetry-emerald font-bold">ONLINE</span>\n</div>', '<div id="sec-row-5" onclick="window.apexScrubTo(0.88)" class="cursor-pointer flex items-center justify-between p-1 rounded bg-surface-container-lowest border border-outline"><span class="text-telemetry-emerald font-semibold">SEC 05 (Eddy Brakes)</span><span id="sec-badge-5" class="text-[10px] text-telemetry-emerald font-bold">ONLINE</span></div>'),
]

for old, new in replacements:
    html = html.replace(old, new)

html = re.sub(r"<!-- Light interactive vanilla script for controls toggle -->.*?</script>", "", html, flags=re.DOTALL)

with open("/home/claw/.hermes/cache/scratch/apex-coaster/index.html", "w") as f:
    f.write(html)

print("BENCHMARK_WEB_APP_BUILT_BYTES:", len(html))
