<div align="center">

# APEX // Hyper-Coaster Telemetry

**A real-time 3D roller-coaster telemetry cockpit — Blender-baked geometry, Stitch-designed UI, live-synced at 60 fps.**

[![Live demo](https://img.shields.io/badge/%E2%96%B6_LIVE_DEMO-andrewmason7.github.io-06B6D4?style=for-the-badge&labelColor=09090B)](https://andrewmason7.github.io/apex-coaster-telemetry/)
[![Repo](https://img.shields.io/badge/GitHub-apex--coaster--telemetry-F43F5E?style=for-the-badge&logo=github&labelColor=09090B)](https://github.com/AndrewMason7/apex-coaster-telemetry)

[![Three.js](https://img.shields.io/badge/Three.js-r170-000000?style=flat-square&logo=three.js&logoColor=white)](https://threejs.org)
[![Blender](https://img.shields.io/badge/Blender-5.3-EA7600?style=flat-square&logo=blender&logoColor=white)](https://www.blender.org)
[![Google Stitch](https://img.shields.io/badge/Google_Stitch-UI_%2B_tokens-4285F4?style=flat-square&logo=google&logoColor=white)](https://stitch.withgoogle.com)
[![WebGL](https://img.shields.io/badge/WebGL-2.0-990000?style=flat-square&logo=webgl&logoColor=white)](#)
[![design.md](https://img.shields.io/badge/%40google%2Fdesign.md-0_errors_0_warnings-10B981?style=flat-square)](#design-system)
[![License](https://img.shields.io/badge/license-MIT-F59E0B?style=flat-square)](LICENSE)

[![faces](https://img.shields.io/badge/geometry-44%2C386_faces-8B5CF6?style=flat-square)](#track-geometry)
[![frames](https://img.shields.io/badge/telemetry-560_frames-06B6D4?style=flat-square)](#how-it-works)
[![cars](https://img.shields.io/badge/train-5_articulated_cars-F43F5E?style=flat-square)](#how-it-works)
[![cameras](https://img.shields.io/badge/cameras-4_modes-F59E0B?style=flat-square)](#controls)
[![build](https://img.shields.io/badge/build-none_%E2%80%94_plain_HTML-10B981?style=flat-square)](#run-it)

`44,386 faces` · `560 telemetry frames` · `5 articulated cars` · `4 camera modes` · `banked 3D spline`

</div>

---

> *"The slow climb is half the fun, and the other half is the part where nobody can breathe."*

APEX is a split-screen instrument panel for a fictional hyper-coaster. The top half is a real
WebGL scene built from a Blender-authored `.glb`; the bottom half is a telemetry deck. Both are
driven by the **same** 560-frame kinematic sidecar, so every number on screen is a function of
where the train physically is on the track — not a canned animation.

| ![Orbit](screenshots/00-hero-orbit.png) |
|:---:|
| *The full cockpit: live WebGL stage above, 560-frame telemetry deck below* |

| ![Orbit](screenshots/01-orbit-slow-climb.png) |
|:---:|
| *Orbit 3D — the 45° chain lift, catwalk and A-frame support towers* |

| ![Side profile](screenshots/02-side-profile-89deg-plunge.png) | ![Rider POV](screenshots/03-rider-pov-crest.png) |
|:---:|:---:|
| *Side profile — the 89.5° plunge into the glowing tunnel portals* | *Rider POV — hanging over the 420 ft crest, banked camera up-vector* |

| ![Chase cam](screenshots/04-chase-cam-loop.png) | ![Stitch UI](design/stitch-ui-render.png) |
|:---:|:---:|
| *Chase cam — five articulated cars banking into the teardrop loop* | *The Stitch-generated cockpit layout, before the 3D stage was mounted* |

---

## The ride

Five phases, each with its own colour identity, its own materials, and its own physiology:

| # | Phase | Colour | What actually happens | Peak readout |
|---|---|---|---|---|
| 01 | **The Slow Climb** | Cyan `#06B6D4` | 45° chain lift, 420 ft, lap-bar clench rising | `6.4 mph` · `+87% grip` |
| 02 | **Zero-Breath Drop** | Crimson `#F43F5E` | 89.5° beyond-vertical, then the pullout trench | `128.4 mph` · `+4.92 G` · `0.0 L/min` |
| 03 | **Teardrop Loop & Roll** | Violet `#8B5CF6` | Inverted apex into a banked zero-G roll | `-64° → +68° bank` |
| 04 | **−1.4 G Ejector Airtime** | Amber `#F59E0B` | Camelback crest with real ejector airtime | `−1.80 G` measured |
| 05 | **Magnetic Fin Brake Run** | Emerald `#10B981` | Eddy-current deceleration back to station | `82 → 6.4 mph` |

Measured extremes across all 560 frames: **420.8 ft** max altitude, **128.4 mph** max speed,
**+4.92 G / −1.80 G** vertical G range, **188 bpm** peak heart rate, **114.8 dB** peak scream
register, **0.0 L/min** minimum respiration.

---

## How it works

```
blender/build_coaster.py
      │
      │  28 control points → periodic Catmull-Rom spline
      │  → 560 samples of position + tangent + banked side + normal
      │
      ├──► assets/apex_coaster.glb        (44,386 faces, 12 objects, 5-material track)
      └──► assets/apex_telemetry.json     (560 frames × kinematics + biometrics)
                    │
                    ▼
            index.html  ── Three.js r170 + PMREM env map + UnrealBloom
                    │
                    └──► bottom deck: every card is bound to the frame index
```

**The spline is closed and periodic.** The train never teleports: sample `559` interpolates back
into sample `0`, so the loop is continuous in position, tangent **and** roll. The bank angle is a
fourth Catmull-Rom channel evaluated on the same parameter, which is why the train leans into the
overbanked turn instead of sliding through it flat.

**Orientation is a proper basis, not a `lookAt`.** Each frame exports `tan`, `up` and `side`; the
renderer re-orthogonalises them with Gram-Schmidt and builds a rotation matrix
`makeBasis(tan, up, side)`. That is what lets the rider-POV camera roll upside down through the
loop without gimbal artefacts.

**Five cars, five spline offsets.** Each car samples the spline at `leadT − i·0.0145`, so the consist
articulates around crests exactly like a real train.

---

## Track geometry

| Component | Detail |
|---|---|
| Track spine | 4-tube B&M/Intamin-style box truss: glowing phase spine, two lower chords, two polished running rails |
| Cross-ties | Y-ribs + Warren diagonal lacing every 2 samples (~6,200 ties) |
| Support towers | A-frame dual-leg above 7.5 m with cross-bracing, monopile + concrete pier below |
| Catwalk | 126 samples of handrail, deck rail and chain trough along the lift hill |
| Tunnel portals | 5 emissive rings at the base of the plunge trench |
| Beacons | Aviation warning spheres on the crest, tip-over lip and loop apex |
| Train | Lead car with nose cone + 4 trailing cars, bucket seats, OTSR bars, 3-wheel bogies |

---

## Run it

No build step, no bundler — it is one HTML file plus two assets.

```bash
python3 -m http.server 8791
# open http://127.0.0.1:8791/
```

A plain `file://` open will not work: the GLB is fetched with `fetch()`, which browsers block
across the file protocol.

### Controls

| Control | Effect |
|---|---|
| Drag the 3D stage | Orbit the camera (theta / phi) |
| `ORBIT 3D` | Free orbit around the track |
| `RIDER POV` | Eye point on the lead car, camera up-vector follows the bank |
| `SIDE PROFILE` | Fixed lateral orthographic-ish view |
| `CHASE CAM` | Trail offset from the previous spline sample |
| `LIVE PAUSE` | Freeze the simulation |
| Timeline scrubber | Click anywhere to jump the train and every readout to that frame |
| Phase matrix rows | Click a block to seek to that phase |

The page also exposes a deterministic hook for headless capture:

```js
window.apexStepSimulation(0.268, 'RIDER_POV');  // freeze + seek + re-render
window.apexScrubTo(0.50);
```

---

## Rebuilding the asset

Requires Blender 4.x/5.x with the Python API. `blender/build_coaster.py` is self-contained: it
clears the scene, builds every material, sweeps the track, places the towers, generates the five
cars, exports the GLB and writes the telemetry sidecar.

```bash
blender --background --python blender/build_coaster.py
# → /tmp/apex_coaster.glb  +  /tmp/apex_telemetry.json
```

The script prints its own manifest, e.g. `BENCHMARK_BAKE_COMPLETE: 12 objects, 44386 faces, 560 frames`.

`blender/render_studio_stills.py` is an optional offline path that sets up a Cycles studio with
area lights for high-resolution stills — useful if you want marketing frames rather than the
live WebGL view.

`scripts/build_live_app.py` regenerates `index.html` by injecting a Three.js runtime into the
Stitch-generated cockpit layout and binding the telemetry deck's element IDs.

---

## Design system

`design/DESIGN.md` is a full token sheet in the `@google/design.md` format — colours, typography,
radii, spacing and component specs.

```bash
npx -y @google/design.md lint design/DESIGN.md   # 0 errors, 0 warnings
```

Every phase owns an accent. The UI never invents a colour that the 3D scene does not use, which is
why the deck and the track read as one instrument rather than two pasted halves.

---

## Repo layout

```
.
├── index.html                     # the whole app
├── assets/
│   ├── apex_coaster.glb           # 44,386-face Blender export
│   └── apex_telemetry.json        # 560-frame kinematic + biometric sidecar
├── design/
│   ├── DESIGN.md                  # design tokens (lint-clean)
│   └── stitch-ui-render.png       # Stitch-generated layout
├── blender/
│   ├── build_coaster.py           # geometry + spline + GLB + sidecar
│   └── render_studio_stills.py    # optional Cycles studio renderer
├── scripts/
│   └── build_live_app.py          # injects the WebGL runtime into the Stitch layout
└── screenshots/
```

---

## Notes & limits

- The ride is fictional. The physics are *plausible*, not simulated: G-force, heart rate and
  respiration are authored curves sampled per frame, not outputs of a rigid-body solver.
- `apex_telemetry.json` is the single source of truth. If you change the spline, regenerate the
  sidecar too — the renderer trusts the sidecar for orientation, so a stale sidecar will drive the
  train through the track.
- Tested in Chromium and Safari. `MeshStandardMaterial` + PMREM environment reflections are
  required for the steel to read as steel; disabling `scene.environment` flattens every rail.
- No tracking, no analytics, no external API calls at runtime. Fonts are the only network
  dependency.

---

## Licence

MIT — see [LICENSE](LICENSE).

Built with [Google Stitch](https://stitch.withgoogle.com) (UI + design tokens) and
[Blender](https://www.blender.org) (geometry), rendered with [Three.js](https://threejs.org).
