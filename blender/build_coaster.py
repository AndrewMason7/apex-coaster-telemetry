"""
APEX // Hyper-Coaster Telemetry — production geometry bake.

Rebuilds the track as a real coaster cross-section (flat spine box girder,
polished running rails, delta lower chords, bolted crossties with gussets),
lattice A-frame supports with footings, a station platform with roof trusses,
lift catwalk with grating, sensor gantries, floodlight masts and a sculpted
5-car train with bogies, flanges, OTSR restraints and LED trim.

Run headless:
  Blender --background --python build_coaster.py

Outputs /tmp/apex_coaster.glb and /tmp/apex_telemetry.json
"""
import bpy
import bmesh
import math
import json
from mathutils import Vector, Matrix

# ==============================================================================
# 1. CLEAN SCENE
# ==============================================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for col in [bpy.data.meshes, bpy.data.materials, bpy.data.curves,
            bpy.data.lights, bpy.data.cameras]:
    for item in list(col):
        col.remove(item)

SCENE = bpy.context.scene
COLL = bpy.context.collection


# ==============================================================================
# 2. PBR MATERIALS  (painted steel, polished rail, galvanised structure,
#    concrete, carbon, rubber, glass, and a short controlled emissive list)
# ==============================================================================
def make_pbr(name, rgb, metallic=0.0, roughness=0.5, emit_rgb=None,
             emit_str=0.0, coat=0.0, coat_rough=0.08, ior=1.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError("Principled BSDF missing in " + name)
    def set_in(key, value):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = value
    set_in("Base Color", (*rgb, 1.0))
    set_in("Metallic", metallic)
    set_in("Roughness", roughness)
    set_in("IOR", ior)
    if coat > 0.0:
        set_in("Coat Weight", coat)
        set_in("Coat Roughness", coat_rough)
    if emit_rgb is not None:
        set_in("Emission Color", (*emit_rgb, 1.0))
        set_in("Emission Strength", emit_str)
    mat.diffuse_color = (*rgb, 1.0)
    return mat


# --- Phase identity: painted steel spine (colour = data, never a light source)
MAT_PHASE = [
    make_pbr("MAT_Track_Phase1_Cyan",    (0.010, 0.470, 0.560), 0.30, 0.30, coat=0.45),
    make_pbr("MAT_Track_Phase2_Crimson", (0.620, 0.045, 0.115), 0.30, 0.28, coat=0.45),
    make_pbr("MAT_Track_Phase3_Violet",  (0.300, 0.130, 0.660), 0.30, 0.30, coat=0.45),
    make_pbr("MAT_Track_Phase4_Amber",   (0.700, 0.330, 0.010), 0.30, 0.30, coat=0.45),
    make_pbr("MAT_Track_Phase5_Emerald", (0.012, 0.400, 0.260), 0.30, 0.30, coat=0.45),
]

MAT_RAIL      = make_pbr("MAT_Running_Rail_Polished", (0.780, 0.800, 0.830), 1.0, 0.075)
MAT_RAIL_WORN = make_pbr("MAT_Running_Rail_Contact",  (0.640, 0.660, 0.700), 1.0, 0.185)
MAT_LOWER     = make_pbr("MAT_Delta_Chord_Galv",      (0.400, 0.430, 0.470), 1.0, 0.310)
MAT_TIE       = make_pbr("MAT_Crosstie_Graphite",     (0.075, 0.085, 0.105), 0.92, 0.400)
MAT_BOLT      = make_pbr("MAT_Bolt_Zinc",             (0.700, 0.720, 0.760), 1.0, 0.230)
MAT_TOWER     = make_pbr("MAT_Tower_Steel",           (0.135, 0.155, 0.185), 0.88, 0.380)
MAT_TOWER_DK  = make_pbr("MAT_Tower_Steel_Shadow",    (0.075, 0.088, 0.110), 0.85, 0.470)
MAT_CONCRETE  = make_pbr("MAT_Concrete_Footing",      (0.255, 0.262, 0.270), 0.05, 0.880)
MAT_CONCRETE2 = make_pbr("MAT_Concrete_Platform",     (0.185, 0.195, 0.215), 0.05, 0.800)
MAT_GRATING   = make_pbr("MAT_Catwalk_Grating",       (0.230, 0.255, 0.285), 0.85, 0.560)
MAT_HANDRAIL  = make_pbr("MAT_Handrail_Safety",       (0.520, 0.430, 0.060), 0.55, 0.420)
MAT_CAR_SHELL = make_pbr("MAT_Car_Pearl_Shell",       (0.780, 0.800, 0.830), 0.15, 0.215, coat=0.9, coat_rough=0.06)
MAT_CAR_DARK  = make_pbr("MAT_Car_Chassis_Dark",      (0.050, 0.058, 0.072), 0.72, 0.340)
MAT_CAR_TRIM  = make_pbr("MAT_Car_Crimson_Trim",      (0.700, 0.045, 0.115), 0.20, 0.230, coat=0.8)
MAT_CAR_SEAT  = make_pbr("MAT_Car_Carbon_Seat",       (0.040, 0.045, 0.055), 0.15, 0.480)
MAT_CAR_PAD   = make_pbr("MAT_Car_Restraint_Pad",     (0.115, 0.115, 0.125), 0.05, 0.640)
MAT_RUBBER    = make_pbr("MAT_Bogie_Rubber",          (0.020, 0.021, 0.024), 0.0, 0.880)
MAT_GLASS     = make_pbr("MAT_Car_Windscreen",        (0.025, 0.032, 0.045), 0.30, 0.060, coat=1.0, coat_rough=0.02)
MAT_SIGN      = make_pbr("MAT_Signage_Panel",         (0.070, 0.078, 0.095), 0.35, 0.480)

# Emissive — deliberately short list
MAT_LED_CYAN   = make_pbr("MAT_Emissive_Cyan",  (0.05, 0.80, 0.95), 0.0, 0.25,
                          emit_rgb=(0.05, 0.80, 0.95), emit_str=4.0)
MAT_LED_RED    = make_pbr("MAT_Emissive_Red",   (1.00, 0.10, 0.14), 0.0, 0.25,
                          emit_rgb=(1.00, 0.10, 0.14), emit_str=5.0)
MAT_LED_WHITE  = make_pbr("MAT_Emissive_White", (1.00, 0.96, 0.90), 0.0, 0.25,
                          emit_rgb=(1.00, 0.96, 0.90), emit_str=3.2)
MAT_LED_AMBER  = make_pbr("MAT_Emissive_Amber", (1.00, 0.55, 0.05), 0.0, 0.25,
                          emit_rgb=(1.00, 0.55, 0.05), emit_str=3.5)


# ==============================================================================
# 3. GEOMETRY PRIMITIVES
# ==============================================================================
def _finish(bm, verts, mat_i, smooth):
    faces = set()
    for v in verts:
        faces.update(v.link_faces)
    for f in faces:
        f.material_index = mat_i
        f.smooth = smooth
    return list(faces)


def rect_profile(w, h, r=0.0, corner_seg=2):
    """Rounded/chamfered rectangle profile in local (u, v), CCW."""
    hw, hh = w * 0.5, h * 0.5
    r = max(0.0, min(r, hw - 1e-4, hh - 1e-4))
    if r <= 1e-5:
        return [(hw, -hh), (hw, hh), (-hw, hh), (-hw, -hh)]
    pts = []
    corners = [(hw - r, -hh + r, -math.pi * 0.5),
               (hw - r, hh - r, 0.0),
               (-hw + r, hh - r, math.pi * 0.5),
               (-hw + r, -hh + r, math.pi)]
    for (cx, cy, a0) in corners:
        for k in range(corner_seg + 1):
            a = a0 + (math.pi * 0.5) * (k / corner_seg)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def ring_from_profile(origin, u_axis, v_axis, profile):
    return [origin + u_axis * u + v_axis * v for (u, v) in profile]


def stitch(bm, rings, mat_i, smooth=False, cap_start=True, cap_end=True,
           closed_ring=True):
    vrings = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(vrings[0])
    for i in range(len(vrings) - 1):
        a, b = vrings[i], vrings[i + 1]
        for c in range(n if closed_ring else n - 1):
            c2 = (c + 1) % n
            try:
                f = bm.faces.new((a[c], a[c2], b[c2], b[c]))
            except ValueError:
                continue
            f.material_index = mat_i
            f.smooth = smooth
    if cap_start:
        try:
            f = bm.faces.new(vrings[0][::-1])
            f.material_index = mat_i
        except ValueError:
            pass
    if cap_end:
        try:
            f = bm.faces.new(vrings[-1])
            f.material_index = mat_i
        except ValueError:
            pass
    return vrings


def circle_ring(origin, u_axis, v_axis, radius, seg):
    return [origin + u_axis * (math.cos(2 * math.pi * c / seg) * radius)
            + v_axis * (math.sin(2 * math.pi * c / seg) * radius)
            for c in range(seg)]


def beam(bm, a, b, w, h, mat_i, chamfer=0.006, smooth=False, up_hint=None,
         corner_seg=1):
    """Square/rectangular structural member between two points."""
    a, b = Vector(a), Vector(b)
    axis = b - a
    L = axis.length
    if L < 1e-5:
        return []
    axis.normalize()
    hint = Vector(up_hint) if up_hint else Vector((0.0, 0.0, 1.0))
    if abs(axis.dot(hint)) > 0.94:
        hint = Vector((0.0, 1.0, 0.0))
    u = axis.cross(hint)
    if u.length < 1e-5:
        u = axis.cross(Vector((1.0, 0.0, 0.0)))
    u.normalize()
    v = u.cross(axis).normalized()
    prof = rect_profile(w, h, chamfer, corner_seg)
    rings = [ring_from_profile(a, u, v, prof), ring_from_profile(b, u, v, prof)]
    stitch(bm, rings, mat_i, smooth=smooth)
    return []


def rod(bm, a, b, r, mat_i, seg=6, smooth=True):
    a, b = Vector(a), Vector(b)
    axis = b - a
    if axis.length < 1e-5:
        return
    axis.normalize()
    hint = Vector((0, 0, 1)) if abs(axis.z) < 0.94 else Vector((0, 1, 0))
    u = axis.cross(hint).normalized()
    v = u.cross(axis).normalized()
    rings = [circle_ring(a, u, v, r, seg), circle_ring(b, u, v, r, seg)]
    stitch(bm, rings, mat_i, smooth=smooth)


def tube_path(bm, points, r, mat_i, seg=8, smooth=True, caps=True):
    pts = [Vector(p) for p in points]
    if len(pts) < 2:
        return
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            t = (pts[1] - pts[0])
        elif i == len(pts) - 1:
            t = (pts[-1] - pts[-2])
        else:
            t = (pts[i + 1] - pts[i - 1])
        t.normalize()
        hint = Vector((0, 1, 0)) if abs(t.dot(Vector((0, 1, 0)))) < 0.9 else Vector((0, 0, 1))
        u = t.cross(hint).normalized()
        v = u.cross(t).normalized()
        rings.append(circle_ring(p, u, v, r, seg))
    stitch(bm, rings, mat_i, smooth=smooth, cap_start=caps, cap_end=caps)


def box(bm, center, size, mat_i, chamfer=0.004, smooth=False, rot=None):
    c = Vector(center)
    sx, sy, sz = size
    ax = Vector((1, 0, 0))
    ay = Vector((0, 1, 0))
    az = Vector((0, 0, 1))
    if rot is not None:
        ax, ay, az = rot @ ax, rot @ ay, rot @ az
    prof = rect_profile(sx, sy, min(chamfer, min(sx, sy) * 0.45), 2)
    rings = []
    for s in (-0.5, 0.5):
        o = c + az * (sz * s)
        rings.append(ring_from_profile(o, ax, ay, prof))
    stitch(bm, rings, mat_i, smooth=smooth)
    return []


def cylinder(bm, center, axis, r, h, mat_i, seg=14, smooth=True, chamfer=0.0):
    c = Vector(center)
    axis = Vector(axis).normalized()
    hint = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((0, 1, 0))
    u = axis.cross(hint).normalized()
    v = u.cross(axis).normalized()
    prof = rect_profile(r * 2, r * 2, chamfer, 2) if chamfer > 0 else None
    ring_a = circle_ring(c - axis * (h * 0.5), u, v, r, seg)
    ring_b = circle_ring(c + axis * (h * 0.5), u, v, r, seg)
    stitch(bm, [ring_a, ring_b], mat_i, smooth=smooth)


def new_object(name, bm, materials, recalc=True):
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    for m in materials:
        obj.data.materials.append(m)
    COLL.objects.link(obj)
    return obj


# ==============================================================================
# 4. CLOSED-CIRCUIT SPLINE (unchanged periodicity, bank channel preserved)
# ==============================================================================
control_points = [
    # --- PHASE 1: Station & 45-Deg Chain Lift Hill
    (-18.0,  0.0,  1.0,   0.0),   # 0: Station dispatch
    (-15.5,  0.0,  1.0,   0.0),   # 1: Lift base engage
    (-12.5,  0.0,  4.2,   0.0),   # 2: Lower lift
    ( -9.5,  0.0,  7.6,   0.0),   # 3: Mid lift
    ( -6.5,  0.0, 11.0,   0.0),   # 4: Upper lift
    ( -4.2,  0.0, 13.8,   0.0),   # 5: Pre-crest
    ( -3.0,  0.0, 14.3,   0.0),   # 6: APEX CREST

    # --- PHASE 2: 89.5 deg beyond-vertical plunge & trench
    ( -2.1, -0.1, 13.4,   5.0),   # 7: Tip-over lip
    ( -1.6, -0.3,  8.5,   8.0),   # 8: Vertical sheer cliff
    ( -1.0, -0.6,  2.4,  12.0),   # 9: Pullout entry
    (  0.4, -1.0,  0.7,  18.0),   # 10: Trench bottom
    (  2.0, -1.2,  2.2,  28.0),   # 11: Rising out of trench

    # --- PHASE 3: Tear-drop vertical loop & banked Immelmann
    (  3.6, -0.8,  6.8,  15.0),   # 12: Loop ascent
    (  4.5,  0.0, 10.6,   0.0),   # 13: Inverted loop apex
    (  5.4,  0.8,  6.6, -20.0),   # 14: Loop descent
    (  6.8,  1.6,  1.6, -48.0),   # 15: High-G banked valley
    (  8.6,  2.2,  4.8, -62.0),   # 16: Zero-G roll entry

    # --- PHASE 4: Ejector airtime camelback & banked helix
    ( 10.8,  1.0,  7.8,   0.0),   # 17: Airtime crest
    ( 13.0, -0.6,  3.2,  35.0),   # 18: Airtime valley
    ( 15.6, -2.2,  5.4,  58.0),   # 19: Overbank entry
    ( 17.8,  0.5,  4.6,  68.0),   # 20: Overbank apex
    ( 16.2,  4.2,  2.6,  45.0),   # 21: Return curve

    # --- PHASE 5: Eddy-current brake run & return
    ( 11.5,  5.2,  1.6,  12.0),   # 22: Brake run entry
    (  5.0,  5.2,  1.4,   0.0),   # 23: Magnetic brakes
    ( -2.5,  5.0,  1.2,   0.0),   # 24: Transfer straight
    (-10.5,  4.6,  1.1, -15.0),   # 25: Station approach
    (-16.8,  3.2,  1.0, -28.0),   # 26: Final turn
    (-19.2,  1.4,  1.0, -12.0),   # 27: Station alignment
]


def catmull_rom(p0, p1, p2, p3, u):
    u2 = u * u
    u3 = u2 * u
    return 0.5 * (
        (2.0 * p1) +
        (-p0 + p2) * u +
        (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * u2 +
        (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * u3
    )


N_CTRL = len(control_points)
N_SAMPLES = 560

pts, banks_rad = [], []
for i in range(N_SAMPLES):
    t = i / N_SAMPLES
    seg_f = t * N_CTRL
    idx = int(seg_f) % N_CTRL
    u = seg_f - int(seg_f)
    c0 = control_points[(idx - 1) % N_CTRL]
    c1 = control_points[idx]
    c2 = control_points[(idx + 1) % N_CTRL]
    c3 = control_points[(idx + 2) % N_CTRL]
    v0, v1, v2, v3 = Vector(c0[:3]), Vector(c1[:3]), Vector(c2[:3]), Vector(c3[:3])
    pts.append(catmull_rom(v0, v1, v2, v3, u))
    banks_rad.append(math.radians(catmull_rom(c0[3], c1[3], c2[3], c3[3], u)))

tangents, sides, normals = [], [], []
for i in range(N_SAMPLES):
    p_prev = pts[(i - 1) % N_SAMPLES]
    p_next = pts[(i + 1) % N_SAMPLES]
    t_vec = (p_next - p_prev).normalized()
    world_up = Vector((0, 0, 1))
    raw_side = t_vec.cross(world_up)
    if raw_side.length < 1e-4:
        raw_side = Vector((0, 1, 0))
    else:
        raw_side.normalize()
    raw_norm = raw_side.cross(t_vec).normalized()
    b = banks_rad[i]
    side = (raw_side * math.cos(b) + raw_norm * math.sin(b)).normalized()
    norm = side.cross(t_vec).normalized()
    tangents.append(t_vec)
    sides.append(side)
    normals.append(norm)

# cumulative arc length for real-metre detail spacing
arc = [0.0]
for i in range(1, N_SAMPLES):
    arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
TOTAL_ARC = arc[-1] + (pts[0] - pts[-1]).length


def frame(i):
    k = i % N_SAMPLES
    return pts[k], sides[k], normals[k], tangents[k]


# ==============================================================================
# 5. TRACK — spine box girder, polished rails, delta chords, bolted crossties
# ==============================================================================
GAUGE = 0.300
R_RAIL = 0.052
SPINE_W, SPINE_H, SPINE_CZ = 0.170, 0.400, -0.300
LOWER_SIDE, LOWER_CZ, R_LOWER = 0.190, -0.560, 0.033
TIE_CZ = -0.040

phase_defs = [
    ("Track_Phase1_SlowClimb",      0, 146, MAT_PHASE[0]),
    ("Track_Phase2_ZeroBreathDrop", 145, 236, MAT_PHASE[1]),
    ("Track_Phase3_InversionLoop",  235, 346, MAT_PHASE[2]),
    ("Track_Phase4_AirtimeHill",    345, 451, MAT_PHASE[3]),
    ("Track_Phase5_BrakeRun",       450, 560, MAT_PHASE[4]),
]

SPINE_PROFILE = rect_profile(SPINE_W, SPINE_H, 0.022, 2)

for seg_name, i_start, i_end, phase_mat in phase_defs:
    bm = bmesh.new()
    idxs = list(range(i_start, i_end + 1))

    # --- spine box girder (painted, chamfered, flat-shaded to catch edges)
    spine_rings = []
    for i in idxs:
        p, s, n, _ = frame(i)
        spine_rings.append(ring_from_profile(p + n * SPINE_CZ, s, n, SPINE_PROFILE))
    stitch(bm, spine_rings, 0, smooth=False)

    # --- two polished running rails (16-sided, smooth)
    for gs in (-1.0, 1.0):
        rings = []
        for i in idxs:
            p, s, n, _ = frame(i)
            rings.append(circle_ring(p + s * (GAUGE * gs), s, n, R_RAIL, 16))
        stitch(bm, rings, 1, smooth=True)

    # --- two lower delta chords (galvanised)
    for gs in (-1.0, 1.0):
        rings = []
        for i in idxs:
            p, s, n, _ = frame(i)
            rings.append(circle_ring(p + s * (LOWER_SIDE * gs) + n * LOWER_CZ,
                                     s, n, R_LOWER, 10))
        stitch(bm, rings, 2, smooth=True)

    # --- running rail contact strip (thin worn band on top of each rail)
    for gs in (-1.0, 1.0):
        rings = []
        for i in idxs:
            p, s, n, _ = frame(i)
            c = p + s * (GAUGE * gs) + n * (R_RAIL * 0.86)
            prof = rect_profile(R_RAIL * 0.85, 0.010, 0.004, 1)
            rings.append(ring_from_profile(c, s, n, prof))
        stitch(bm, rings, 3, smooth=True)

    # --- crossties every 4 samples (~0.86 m) with bolts + gussets
    last_arc = -99.0
    for i in range(i_start, i_end, 4):
        p, s, n, t = frame(i)
        if arc[i % N_SAMPLES] - last_arc < 0.55:
            continue
        last_arc = arc[i % N_SAMPLES]

        tie_c = p + n * TIE_CZ
        # tie plate spanning both rails, chamfered
        rings = [
            ring_from_profile(tie_c + t * 0.032, s, n, rect_profile(0.760, 0.038, 0.008, 1)),
            ring_from_profile(tie_c - t * 0.032, s, n, rect_profile(0.760, 0.038, 0.008, 1)),
        ]
        stitch(bm, rings, 4, smooth=False)

        # upper web plate tying the tie down into the spine
        web = p + n * (TIE_CZ - 0.11)
        rings = [
            ring_from_profile(web + t * 0.020, s, n, rect_profile(0.120, 0.230, 0.006, 1)),
            ring_from_profile(web - t * 0.020, s, n, rect_profile(0.120, 0.230, 0.006, 1)),
        ]
        stitch(bm, rings, 4, smooth=False)

        # four hex bolt heads on the tie
        for gs in (-1.0, 1.0):
            for ts in (-1.0, 1.0):
                bc = tie_c + s * (GAUGE * gs) + t * (0.045 * ts) + n * 0.026
                cylinder(bm, bc, n, 0.019, 0.024, 5, seg=6, smooth=False)

        # gusset plates rail -> spine (both sides of the tie)
        for gs in (-1.0, 1.0):
            gusset_c = p + s * (GAUGE * gs * 0.62) + n * (SPINE_CZ + SPINE_H * 0.46)
            box(bm, gusset_c, (0.150, 0.020, 0.170), 4, chamfer=0.004,
                rot=Matrix.Rotation(math.radians(38.0 * gs), 4, 'Y'))

    # --- rail clamp blocks (adjustable clamps holding each running rail)
    clamp_arc = -99.0
    for i in range(i_start, i_end, 4):
        p, s, n, t = frame(i)
        if arc[i % N_SAMPLES] - clamp_arc < 0.55:
            continue
        clamp_arc = arc[i % N_SAMPLES]
        for gs in (-1.0, 1.0):
            cc = p + s * (GAUGE * gs) + n * (R_RAIL * 0.55)
            box(bm, cc, (0.085, 0.075, 0.075), 4, chamfer=0.012, rot=None)
            cylinder(bm, cc + n * 0.045, n, 0.013, 0.022, 5, seg=6, smooth=False)

    # --- track splice bands every ~6 m (proud ring on the spine = construction joint)
    splice_next = arc[i_start]
    for i in idxs:
        a = arc[i % N_SAMPLES]
        if a < splice_next:
            continue
        splice_next = a + 6.0
        p, s, n, t = frame(i)
        prof = rect_profile(SPINE_W * 1.10, SPINE_H * 1.04, 0.026, 2)
        rings = [
            ring_from_profile(p + n * SPINE_CZ + t * 0.030, s, n, prof),
            ring_from_profile(p + n * SPINE_CZ - t * 0.030, s, n, prof),
        ]
        stitch(bm, rings, 5, smooth=False)

    # --- Warren web: thin diagonal rods from spine to delta chords
    for i in range(i_start, i_end, 6):
        p0, s0, n0, _ = frame(i)
        p1, s1, n1, _ = frame(i + 6)
        gs = -1.0 if ((i // 6) % 2 == 0) else 1.0
        a = p0 + n0 * (SPINE_CZ + SPINE_H * 0.42)
        b = p1 + s1 * (LOWER_SIDE * gs * 0.30) + n1 * (LOWER_CZ + 0.02)
        rod(bm, a, b, 0.013, 4, seg=5, smooth=True)

    # --- calibration ticks on the spine flanks (deck's monospace language)
    for i in range(i_start, i_end, 8):
        p, s, n, t = frame(i)
        for gs in (-1.0, 1.0):
            c = p + s * (SPINE_W * 0.5 * gs) + n * (SPINE_CZ + 0.02)
            box(bm, c, (0.006, 0.020, 0.075), 5, chamfer=0.0015,
                rot=None)

    new_object(seg_name, bm, [phase_mat, MAT_RAIL, MAT_LOWER, MAT_RAIL_WORN,
                              MAT_TIE, MAT_BOLT])

# ==============================================================================
# 6. SUPPORTS — lattice A-frames, footings, saddle plates
# ==============================================================================
bm = bmesh.new()
tower_arc = -99.0
tower_positions = []
for i in range(0, N_SAMPLES, 2):
    p, s, n, t = frame(i)
    if p.z < 1.35:
        continue
    a = arc[i]
    if a - tower_arc < 7.2:
        continue
    tower_arc = a
    tower_positions.append(i)

for idx in tower_positions:
    p, s, n, t = frame(idx)
    attach = p + n * (SPINE_CZ - SPINE_H * 0.5 - 0.035)
    hs = Vector((s.x, s.y, 0.0))
    if hs.length < 1e-4:
        hs = Vector((1.0, 0.0, 0.0))
    hs.normalize()

    h = attach.z
    if h < 3.4:
        # single column with base plate
        base = Vector((attach.x, attach.y, 0.32))
        beam(bm, base, attach, 0.210, 0.210, 0, chamfer=0.014)
        box(bm, Vector((attach.x, attach.y, 0.34)), (0.62, 0.62, 0.55), 1, chamfer=0.02)
        box(bm, attach + Vector((0, 0, 0.02)), (0.34, 0.22, 0.10), 0, chamfer=0.006)
        continue

    spread = 0.95 + h * 0.055
    foot_l = Vector((attach.x - hs.x * spread, attach.y - hs.y * spread, 0.34))
    foot_r = Vector((attach.x + hs.x * spread, attach.y + hs.y * spread, 0.34))
    top_l = attach - hs * 0.34 + Vector((0, 0, 0.02))
    top_r = attach + hs * 0.34 + Vector((0, 0, 0.02))

    # legs
    beam(bm, foot_l, top_l, 0.190, 0.190, 0, chamfer=0.014)
    beam(bm, foot_r, top_r, 0.190, 0.190, 0, chamfer=0.014)

    # header saddle + spine clamp
    beam(bm, top_l - hs * 0.06, top_r + hs * 0.06, 0.130, 0.100, 0, chamfer=0.008)
    box(bm, attach + Vector((0, 0, -0.02)), (0.30, 0.30, 0.075), 0, chamfer=0.006)
    for gs in (-1.0, 1.0):
        cylinder(bm, attach + hs * (0.20 * gs) + Vector((0, 0, 0.055)),
                 Vector((0, 0, 1)), 0.018, 0.03, 5, seg=6, smooth=False)

    # X-bracing + horizontal rungs at three levels
    for f in (0.30, 0.58, 0.82):
        l = foot_l.lerp(top_l, f)
        r = foot_r.lerp(top_r, f)
        beam(bm, l, r, 0.085, 0.085, 1, chamfer=0.006)
    for f0, f1 in ((0.06, 0.30), (0.30, 0.58), (0.58, 0.82), (0.82, 0.98)):
        l0 = foot_l.lerp(top_l, f0)
        r0 = foot_r.lerp(top_r, f0)
        l1 = foot_l.lerp(top_l, f1)
        r1 = foot_r.lerp(top_r, f1)
        rod(bm, l0, r1, 0.034, 1, seg=6)
        rod(bm, r0, l1, 0.034, 1, seg=6)
        # gusset plate at the bottom node
        if f0 < 0.1:
            box(bm, l0.lerp(r0, 0.5), (0.16, 0.16, 0.012), 0, chamfer=0.002)

    # concrete footings (chamfered, slightly proud of ground)
    for ft in (foot_l, foot_r):
        box(bm, Vector((ft.x, ft.y, 0.17)), (0.86, 0.86, 0.34), 1, chamfer=0.025)
        box(bm, Vector((ft.x, ft.y, 0.355)), (0.36, 0.36, 0.05), 2, chamfer=0.008)

new_object("Support_Towers", bm, [MAT_TOWER, MAT_TOWER_DK, MAT_BOLT])

# ==============================================================================
# 6b. RETURN-RUN SUPPORTS — short braced columns under the brake run
# ==============================================================================
bm = bmesh.new()
ret_arc = -99.0
for i in range(450, N_SAMPLES, 2):
    p, s, n, t = frame(i)
    if p.z < 0.9:
        continue
    if arc[i] - ret_arc < 8.0:
        continue
    ret_arc = arc[i]
    attach = p + n * (SPINE_CZ - SPINE_H * 0.5 - 0.03)
    hs = Vector((s.x, s.y, 0.0))
    if hs.length < 1e-4:
        continue
    hs.normalize()
    base = Vector((attach.x, attach.y, 0.30))
    beam(bm, base, attach, 0.165, 0.165, 0, chamfer=0.010)
    box(bm, Vector((attach.x, attach.y, 0.17)), (0.70, 0.70, 0.34), 1, chamfer=0.02)
    box(bm, attach + Vector((0, 0, -0.03)), (0.28, 0.28, 0.07), 0, chamfer=0.006)
    # two outrigger braces to the footings
    for gs in (-1.0, 1.0):
        foot = Vector((attach.x + hs.x * 0.95 * gs, attach.y + hs.y * 0.95 * gs, 0.30))
        rod(bm, foot, attach - Vector((0, 0, 0.35)), 0.030, 0, seg=6)
        box(bm, Vector((foot.x, foot.y, 0.16)), (0.55, 0.55, 0.32), 1, chamfer=0.018)
new_object("Return_Run_Supports", bm, [MAT_TOWER, MAT_CONCRETE, MAT_BOLT])

# ==============================================================================
# 7. LIFT CATWALK — stringers, grating slats, handrail posts, toe board
# ==============================================================================
bm = bmesh.new()
WALK_OFFSET = -0.62
lift_start, lift_end = 6, 132
# stringers
for off_n in (-0.02, 0.30):
    rings = []
    for i in range(lift_start, lift_end):
        p, s, n, t = frame(i)
        c = p + s * WALK_OFFSET + n * off_n
        rings.append(ring_from_profile(c, s, n, rect_profile(0.55, 0.024, 0.004, 1)))
    stitch(bm, rings, 0, smooth=False)
# grating slats every 0.16 m
last = -99.0
for i in range(lift_start, lift_end):
    if arc[i] - last < 0.085:
        continue
    last = arc[i]
    p, s, n, t = frame(i)
    c = p + s * WALK_OFFSET + n * 0.14
    box(bm, c, (0.52, 0.028, 0.030), 0, chamfer=0.003)
# handrail posts + two rails
for i in range(lift_start, lift_end, 7):
    p, s, n, t = frame(i)
    base = p + s * (WALK_OFFSET + 0.26) + n * 0.02
    top = base + n * 1.02
    beam(bm, base, top, 0.030, 0.030, 1, chamfer=0.003)
for off_n in (0.62, 1.00):
    rings = []
    for i in range(lift_start, lift_end):
        p, s, n, t = frame(i)
        c = p + s * (WALK_OFFSET + 0.26) + n * off_n
        rings.append(circle_ring(c, s, n, 0.019, 8))
    stitch(bm, rings, 1, smooth=True)
# toe board
rings = []
for i in range(lift_start, lift_end):
    p, s, n, t = frame(i)
    c = p + s * (WALK_OFFSET + 0.26) + n * 0.09
    rings.append(ring_from_profile(c, s, n, rect_profile(0.018, 0.11, 0.003, 1)))
stitch(bm, rings, 0, smooth=False)

new_object("Lift_Catwalk", bm, [MAT_GRATING, MAT_HANDRAIL, MAT_BOLT])

# ==============================================================================
# 7b. CHAIN LIFT — trough between the rails, return chain, drive sprocket
# ==============================================================================
bm = bmesh.new()
CHAIN_START, CHAIN_END = 4, 138
# trough: two side plates + bottom, following the spine
for gs in (-1.0, 1.0):
    rings = []
    for i in range(CHAIN_START, CHAIN_END):
        p, s, n, t = frame(i)
        c = p + s * (0.075 * gs) + n * (-0.012)
        rings.append(ring_from_profile(c, s, n, rect_profile(0.014, 0.090, 0.003, 1)))
    stitch(bm, rings, 0, smooth=False)
rings = []
for i in range(CHAIN_START, CHAIN_END):
    p, s, n, t = frame(i)
    rings.append(ring_from_profile(p + n * (-0.055), s, n, rect_profile(0.170, 0.016, 0.003, 1)))
stitch(bm, rings, 0, smooth=False)
# chain links: alternating plates on a 0.30 m pitch
last = -99.0
link_flip = False
for i in range(CHAIN_START, CHAIN_END):
    if arc[i] - last < 0.30:
        continue
    last = arc[i]
    p, s, n, t = frame(i)
    c = p + n * (-0.040)
    box(bm, c + s * 0.010, (0.050, 0.055, 0.030), 1, chamfer=0.004)
    box(bm, c - s * 0.020, (0.030, 0.075, 0.018), 2, chamfer=0.003)
    link_flip = not link_flip
# drive sprocket housing at the base of the lift
sp, ss, sn, st = frame(CHAIN_START + 2)
cyl_c = sp + sn * (-0.20)
cylinder(bm, cyl_c, Vector((ss.x, ss.y, 0)).normalized(), 0.26, 0.16, 0, seg=20, smooth=True)
cylinder(bm, cyl_c, Vector((ss.x, ss.y, 0)).normalized(), 0.30, 0.05, 1, seg=20, smooth=True)
box(bm, cyl_c + Vector((0, 0, -0.34)), (0.52, 0.52, 0.30), 3, chamfer=0.02)
new_object("Chain_Lift", bm, [MAT_TIE, MAT_BOLT, MAT_TOWER_DK, MAT_CONCRETE])

# ==============================================================================
# 8. SENSOR GANTRIES — structural frames with controlled emissive strips
# ==============================================================================
bm = bmesh.new()
for idx in (104, 466):
    p, s, n, t = frame(idx)
    hs = Vector((s.x, s.y, 0.0)).normalized()
    for gs in (-1.0, 1.0):
        base = Vector((p.x + hs.x * 2.0 * gs, p.y + hs.y * 2.0 * gs, 0.0))
        top = base + Vector((0, 0, max(2.4, p.z + 1.35)))
        beam(bm, base, top, 0.10, 0.10, 0, chamfer=0.008)
        box(bm, base + Vector((0, 0, 0.14)), (0.42, 0.42, 0.28), 1, chamfer=0.015)
    # cross header + LED strip
    l_top = Vector((p.x + hs.x * 2.0, p.y + hs.y * 2.0, 0.0)) + Vector((0, 0, max(2.4, p.z + 1.35)))
    r_top = Vector((p.x - hs.x * 2.0, p.y - hs.y * 2.0, 0.0)) + Vector((0, 0, max(2.4, p.z + 1.35)))
    beam(bm, l_top, r_top, 0.14, 0.12, 0, chamfer=0.008)
    mid = l_top.lerp(r_top, 0.5) - Vector((0, 0, 0.085))
    box(bm, mid, (2.6, 0.030, 0.045), 2, chamfer=0.004, rot=None)
    # camera boxes
    for f in (0.32, 0.68):
        cp = l_top.lerp(r_top, f) - Vector((0, 0, 0.20))
        box(bm, cp, (0.11, 0.11, 0.15), 0, chamfer=0.006)

new_object("Sensor_Gantries", bm, [MAT_TOWER, MAT_CONCRETE, MAT_LED_CYAN])

# ==============================================================================
# 9. STATION — platform, columns, roof trusses, fascia signage
# ==============================================================================
bm = bmesh.new()
PLAT_X0, PLAT_X1 = -20.2, -15.0
PLAT_Y0, PLAT_Y1 = -2.7, -0.55
plat_y_mid = (PLAT_Y0 + PLAT_Y1) * 0.5
plat_w = PLAT_Y1 - PLAT_Y0
plat_x_mid = (PLAT_X0 + PLAT_X1) * 0.5
plat_len = PLAT_X1 - PLAT_X0

# deck slab
box(bm, (plat_x_mid, plat_y_mid, 0.44), (plat_len, plat_w, 0.30), 0, chamfer=0.02)
# platform edge nosing + tactile strip
box(bm, (plat_x_mid, PLAT_Y1 - 0.06, 0.60), (plat_len, 0.14, 0.035), 1, chamfer=0.006)
box(bm, (plat_x_mid, PLAT_Y1 - 0.18, 0.602), (plat_len, 0.10, 0.008), 2, chamfer=0.002)
# support wall / plinth
box(bm, (plat_x_mid, plat_y_mid, 0.15), (plat_len - 0.4, plat_w - 0.4, 0.32), 0, chamfer=0.01)

# columns along the outer edge
col_y = PLAT_Y0 + 0.22
col_xs = [PLAT_X0 + 0.5 + k * 1.45 for k in range(int(plat_len / 1.45) + 1)]
for cx in col_xs:
    beam(bm, (cx, col_y, 0.58), (cx, col_y, 3.56), 0.215, 0.215, 1, chamfer=0.010)
    box(bm, (cx, col_y, 0.66), (0.30, 0.30, 0.06), 1, chamfer=0.006)
    box(bm, (cx, col_y, 3.50), (0.26, 0.26, 0.06), 1, chamfer=0.006)

# roof: deck + trusses spanning to the track side
roof_z = 3.72
box(bm, (plat_x_mid, plat_y_mid - 0.25, roof_z), (plat_len + 0.5, plat_w + 0.9, 0.10), 3, chamfer=0.006)
for cx in col_xs:
    top_a = Vector((cx, col_y, 3.56))
    top_b = Vector((cx, PLAT_Y1 + 0.62, 3.66))
    beam(bm, top_a, top_b, 0.10, 0.12, 1, chamfer=0.005)
    # diagonal web
    mid = top_a.lerp(top_b, 0.5)
    rod(bm, top_a + Vector((0, 0, -0.02)), mid + Vector((0, 0, 0.16)), 0.022, 1, seg=5)
    rod(bm, top_b + Vector((0, 0, -0.02)), mid + Vector((0, 0, 0.16)), 0.022, 1, seg=5)
    box(bm, mid + Vector((0, 0, 0.17)), (0.06, 0.06, 0.16), 1, chamfer=0.004)

# station building behind the platform: wall panels, window band, door, roof slab
BLD_Y0, BLD_Y1 = PLAT_Y0 - 2.30, PLAT_Y0 - 0.20
bld_ymid = (BLD_Y0 + BLD_Y1) * 0.5
box(bm, (plat_x_mid, bld_ymid, 1.85), (plat_len - 0.6, BLD_Y1 - BLD_Y0, 2.60), 4, chamfer=0.03)
box(bm, (plat_x_mid, BLD_Y1 + 0.02, 2.35), (plat_len - 1.2, 0.10, 0.95), 1, chamfer=0.01)
box(bm, (plat_x_mid, BLD_Y1 + 0.07, 2.35), (plat_len - 1.6, 0.06, 0.72), 6, chamfer=0.008)
box(bm, (plat_x_mid, BLD_Y1 + 0.08, 1.20), (1.30, 0.10, 1.10), 1, chamfer=0.02)
box(bm, (plat_x_mid, bld_ymid, 3.22), (plat_len - 0.2, BLD_Y1 - BLD_Y0 + 0.35, 0.16), 3, chamfer=0.01)

# fascia signage board
board_c = (plat_x_mid, PLAT_Y0 - 0.02, 3.30)
box(bm, board_c, (5.4, 0.10, 0.62), 4, chamfer=0.008)
box(bm, (board_c[0], board_c[1] - 0.06, 3.30), (5.15, 0.012, 0.06), 2, chamfer=0.002)
box(bm, (board_c[0], board_c[1] - 0.06, 3.10), (5.15, 0.012, 0.012), 2, chamfer=0.002)

# queue railings on the platform
for k in range(6):
    qx = PLAT_X0 + 1.1 + k * 0.72
    beam(bm, (qx, PLAT_Y1 - 0.55, 0.61), (qx, PLAT_Y1 - 0.55, 1.55), 0.035, 0.035, 1, chamfer=0.003)
beam(bm, (PLAT_X0 + 1.1, PLAT_Y1 - 0.55, 1.55), (PLAT_X0 + 4.7, PLAT_Y1 - 0.55, 1.55),
     0.045, 0.045, 1, chamfer=0.004)
beam(bm, (PLAT_X0 + 1.1, PLAT_Y1 - 0.55, 1.08), (PLAT_X0 + 4.7, PLAT_Y1 - 0.55, 1.08),
     0.030, 0.030, 1, chamfer=0.003)

# roof purlins + edge fascia + under-canopy luminaires
for py in (-2.45, -1.85, -1.25, -0.75):
    beam(bm, (PLAT_X0 + 0.15, py, roof_z + 0.10), (PLAT_X1 - 0.15, py, roof_z + 0.10),
         0.075, 0.055, 1, chamfer=0.005)
beam(bm, (PLAT_X0 + 0.1, PLAT_Y1 + 0.60, roof_z - 0.02),
     (PLAT_X1 - 0.1, PLAT_Y1 + 0.60, roof_z - 0.02), 0.07, 0.16, 1, chamfer=0.006)
for lx in (PLAT_X0 + 1.6, PLAT_X0 + 4.0, PLAT_X0 + 6.4):
    box(bm, (lx, plat_y_mid - 0.15, roof_z - 0.14), (0.62, 0.16, 0.07), 3, chamfer=0.006)
    box(bm, (lx, plat_y_mid - 0.15, roof_z - 0.185), (0.52, 0.10, 0.012), 2, chamfer=0.002)

new_object("Station_Platform", bm,
           [MAT_CONCRETE2, MAT_TOWER, MAT_LED_CYAN, MAT_GRATING, MAT_SIGN,
            MAT_LED_WHITE, MAT_GLASS])

# Extruded station lettering (converted to mesh, no fonts required at runtime)
def add_text(body, size, loc, rot_z, mat):
    curve = bpy.data.curves.new(type='FONT', name="txt_" + body)
    curve.body = body
    curve.size = size
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.extrude = 0.012
    curve.resolution_u = 2
    obj = bpy.data.objects.new("Text_" + body, curve)
    obj.location = loc
    obj.rotation_euler = (math.radians(90), 0.0, math.radians(rot_z))
    obj.data.materials.append(mat)
    COLL.objects.link(obj)
    return obj

add_text("APEX", 0.34, (plat_x_mid - 1.15, PLAT_Y0 - 0.09, 3.30), 0.0, MAT_LED_WHITE)
add_text("01", 0.22, (plat_x_mid + 1.55, PLAT_Y0 - 0.09, 3.26), 0.0, MAT_LED_CYAN)

# ==============================================================================
# 10. FLOODLIGHT MASTS + GROUND PROPS
# ==============================================================================
bm = bmesh.new()
mast_defs = [(-26.0, -9.0, 9.2), (25.0, -8.0, 8.4), (26.0, 9.5, 8.8), (-24.0, 10.0, 9.6)]
for (mx, my, mh) in mast_defs:
    beam(bm, (mx, my, 0.0), (mx, my, mh), 0.10, 0.10, 0, chamfer=0.008)
    box(bm, (mx, my, 0.12), (0.55, 0.55, 0.24), 1, chamfer=0.02)
    # head yoke + two fixtures aimed at the structure
    aim = Vector((0, 0, 5.0)) - Vector((mx, my, mh))
    box(bm, (mx, my, mh + 0.10), (0.55, 0.18, 0.16), 0, chamfer=0.01)
    for off in (-0.17, 0.17):
        hx = mx + off
        box(bm, (hx, my, mh + 0.24), (0.26, 0.30, 0.22), 2, chamfer=0.012,
            rot=Matrix.Rotation(math.radians(28), 4, 'X'))
        box(bm, (hx, my - 0.15, mh + 0.18), (0.22, 0.02, 0.17), 3, chamfer=0.004)

# maintenance props: crates, cable reel, barriers, ladder
box(bm, (-13.2, -2.2, 0.30), (0.85, 0.62, 0.60), 4, chamfer=0.012)
box(bm, (-13.1, -2.05, 0.86), (0.62, 0.50, 0.42), 4, chamfer=0.010)
box(bm, (-13.25, -3.05, 0.22), (0.55, 0.48, 0.44), 5, chamfer=0.010)
# cable reel
cylinder(bm, (9.2, -4.4, 0.55), Vector((0, 1, 0)), 0.46, 0.30, 4, seg=18, smooth=True)
cylinder(bm, (9.2, -4.4, 0.55), Vector((0, 1, 0)), 0.18, 0.36, 1, seg=12, smooth=True)
# barrier fence segments
for bx in (-6.0, -3.4, -0.8):
    beam(bm, (bx, -5.2, 0.0), (bx, -5.2, 1.05), 0.05, 0.05, 1, chamfer=0.004)
    beam(bm, (bx + 1.9, -5.2, 0.0), (bx + 1.9, -5.2, 1.05), 0.05, 0.05, 1, chamfer=0.004)
    box(bm, (bx + 0.95, -5.2, 0.86), (2.0, 0.03, 0.14), 5, chamfer=0.004)
    box(bm, (bx + 0.95, -5.2, 0.44), (2.0, 0.03, 0.06), 5, chamfer=0.004)

# maintenance ladder leaning on the tall tower near the drop
for lz in [0.5 + k * 0.34 for k in range(9)]:
    box(bm, (2.05, -1.9, lz), (0.44, 0.035, 0.028), 1, chamfer=0.004)
    for sx in (-1.0, 1.0):
        box(bm, (2.05 + sx * 0.21, -1.9, lz), (0.030, 0.030, 0.34), 1, chamfer=0.003)

new_object("Ground_Props", bm,
           [MAT_TOWER, MAT_CONCRETE, MAT_TOWER_DK, MAT_LED_WHITE,
            MAT_GRATING, MAT_HANDRAIL, MAT_BOLT])

# ==============================================================================
# 11. TRAIN — sculpted shell, bogies, flanges, OTSR restraints, LED trim
# ==============================================================================
C_SHELL, C_TRIM, C_DARK, C_SEAT = 0, 1, 2, 3
C_RUBBER, C_GLASS, C_PAD, C_LED, C_AMBER, C_BOLT = 4, 5, 6, 7, 8, 9


def body_section(x, w, h, z0, r, seg=3):
    prof = rect_profile(w, h, r, seg)
    return [Vector((x, u, z0 + v)) for (u, v) in prof]


def build_car(name, lead=False):
    bm = bmesh.new()
    L = 1.62 if lead else 1.48
    xs = [-0.74, -0.60, -0.20, 0.22, 0.52, 0.70] if not lead else \
         [-0.78, -0.62, -0.15, 0.30, 0.62, 0.86]
    widths = [0.36, 0.52, 0.59, 0.59, 0.53, 0.40] if not lead else \
             [0.34, 0.50, 0.60, 0.60, 0.52, 0.34]
    heights = [0.26, 0.40, 0.46, 0.46, 0.40, 0.26] if not lead else \
              [0.24, 0.38, 0.46, 0.45, 0.34, 0.20]
    z0s = [0.60, 0.62, 0.64, 0.64, 0.62, 0.58] if not lead else \
          [0.58, 0.60, 0.63, 0.62, 0.56, 0.50]

    sections = []
    for k in range(len(xs)):
        sections.append(body_section(xs[k], widths[k], heights[k], z0s[k], 0.085))
    # pointed nose for the lead car
    if lead:
        sections.append(body_section(1.02, 0.16, 0.16, 0.52, 0.05))
    else:
        sections.append(body_section(-0.80, 0.20, 0.18, 0.60, 0.05))
    stitch(bm, sections, C_SHELL, smooth=True)

    # low chassis skirt
    box(bm, (0.0, 0.0, 0.34), (L * 0.92, 0.50, 0.20), C_DARK, chamfer=0.03)
    # side pods (asymmetric accent panels)
    for gy in (-1.0, 1.0):
        box(bm, (0.02, gy * 0.585, 0.60), (L * 0.66, 0.05, 0.20), C_TRIM, chamfer=0.012)
        box(bm, (0.04, gy * 0.60, 0.46), (L * 0.58, 0.03, 0.035), C_LED, chamfer=0.004)
    # windscreen / cockpit fairing
    box(bm, (0.30, 0.0, 0.86), (0.34, 0.44, 0.12), C_GLASS, chamfer=0.03,
        rot=Matrix.Rotation(math.radians(-9), 4, 'Y'))

    # seats + restraints
    for sy in (-0.185, 0.185):
        # cushion and back
        box(bm, (0.02, sy, 0.755), (0.34, 0.29, 0.09), C_SEAT, chamfer=0.02)
        box(bm, (-0.20, sy, 0.88), (0.10, 0.29, 0.30), C_SEAT, chamfer=0.02,
            rot=Matrix.Rotation(math.radians(12), 4, 'Y'))
        # headrest fairing
        box(bm, (-0.26, sy, 1.00), (0.15, 0.25, 0.15), C_SHELL, chamfer=0.045)
        # OTSR: bent tube from behind head, over the shoulder, to the chest
        p0 = Vector((-0.24, sy, 1.00))
        p1 = Vector((-0.10, sy, 1.16))
        p2 = Vector((0.16, sy, 0.74))
        arc = []
        for k in range(8):
            f = k / 7.0
            arc.append((1 - f) ** 2 * p0 + 2 * (1 - f) * f * p1 + f ** 2 * p2)
        tube_path(bm, arc, 0.023, C_DARK, seg=6, smooth=True)
        # shoulder pad on the restraint
        box(bm, (0.13, sy, 0.79), (0.10, 0.10, 0.12), C_PAD, chamfer=0.03)
        # side bolsters
        for gy in (-1.0, 1.0):
            box(bm, (0.0, sy + gy * 0.17, 0.80), (0.32, 0.045, 0.13), C_DARK, chamfer=0.015)

    # lap bar across both seats
    beam(bm, (0.18, -0.34, 0.74), (0.18, 0.34, 0.74), 0.055, 0.055, C_PAD, chamfer=0.02)

    # rear spoiler (lead car only)
    if lead:
        box(bm, (-0.80, 0.0, 1.00), (0.13, 0.62, 0.035), C_TRIM, chamfer=0.008,
            rot=Matrix.Rotation(math.radians(14), 4, 'Y'))
        for gy in (-1.0, 1.0):
            box(bm, (-0.80, gy * 0.29, 0.90), (0.10, 0.028, 0.19), C_DARK, chamfer=0.005)

    # bogie side plates + cross beams
    for gx in (-0.44, 0.44):
        for gy in (-1.0, 1.0):
            box(bm, (gx, gy * 0.345, 0.10), (0.52, 0.035, 0.26), C_DARK, chamfer=0.012)
        beam(bm, (gx, -0.34, 0.10), (gx, 0.34, 0.10), 0.06, 0.07, C_DARK, chamfer=0.008)

    # wheels: road (top), upstop (under), side friction (inside)
    wheel_r = 0.082
    for gx in (-0.44, 0.44):
        for gy in (-1.0, 1.0):
            y = gy * GAUGE
            # road wheel
            cylinder(bm, (gx, y, wheel_r * 0.92), Vector((0, 1, 0)), wheel_r, 0.055,
                     C_RUBBER, seg=16, smooth=True)
            # flange
            cylinder(bm, (gx, y - gy * 0.038, wheel_r * 0.92), Vector((0, 1, 0)),
                     wheel_r * 1.16, 0.010, C_DARK, seg=16, smooth=True)
            # hub
            cylinder(bm, (gx, y + gy * 0.030, wheel_r * 0.92), Vector((0, 1, 0)),
                     wheel_r * 0.42, 0.016, C_BOLT, seg=10, smooth=True)
            # upstop wheel
            cylinder(bm, (gx, y, -0.062), Vector((0, 1, 0)), 0.052, 0.05,
                     C_RUBBER, seg=12, smooth=True)
            # side friction wheel
            cylinder(bm, (gx, gy * (GAUGE + 0.075), -0.005), Vector((1, 0, 0)),
                     0.042, 0.045, C_RUBBER, seg=12, smooth=True)
            # bogie status LED
            box(bm, (gx, gy * 0.355, 0.225), (0.05, 0.012, 0.02), C_AMBER, chamfer=0.003)

    # rear coupler
    box(bm, (-0.86, 0.0, 0.42), (0.14, 0.10, 0.09), C_DARK, chamfer=0.01)
    # car number plate
    box(bm, (-0.40, 0.605, 0.72), (0.16, 0.012, 0.10), C_BOLT, chamfer=0.003)

    obj = new_object(name, bm,
                     [MAT_CAR_SHELL, MAT_CAR_TRIM, MAT_CAR_DARK, MAT_CAR_SEAT,
                      MAT_RUBBER, MAT_GLASS, MAT_CAR_PAD, MAT_LED_CYAN,
                      MAT_LED_AMBER, MAT_BOLT])
    return obj


car0 = build_car("Coaster_Car_0", lead=True)
car1 = build_car("Coaster_Car_1", lead=False)
for k in range(2, 5):
    dup = bpy.data.objects.new(f"Coaster_Car_{k}", car1.data)
    for m in car1.data.materials:
        pass
    COLL.objects.link(dup)

# ==============================================================================
# 12. EXPORT GLB
# ==============================================================================
out_glb = "/tmp/apex_coaster.glb"
bpy.ops.export_scene.gltf(
    filepath=out_glb,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_yup=True,
    export_materials='EXPORT',
    export_cameras=False,
    export_lights=False,
    export_extras=False,
    export_texcoords=False,
    export_normals=True,
    export_tangents=False,
)

# ==============================================================================
# 13. TELEMETRY SIDECAR (560 frames, identical schema)
# ==============================================================================
telemetry_samples = []
for i in range(N_SAMPLES):
    t = i / N_SAMPLES
    p, s_vec, n_vec, t_vec = frame(i)
    three_pos = [round(p.x, 4), round(p.z, 4), round(-p.y, 4)]
    three_tan = [round(t_vec.x, 4), round(t_vec.z, 4), round(-t_vec.y, 4)]
    three_up = [round(n_vec.x, 4), round(n_vec.z, 4), round(-n_vec.y, 4)]
    three_side = [round(s_vec.x, 4), round(s_vec.z, 4), round(-s_vec.y, 4)]

    alt_ft = round(max(0.0, (p.z - 0.7) / 13.6 * 420.0), 1)
    pitch_deg = round(math.degrees(math.asin(max(-1.0, min(1.0, t_vec.z)))), 1)
    bank_deg = round(math.degrees(banks_rad[i]), 1)

    if i < 145:
        u = i / 145.0
        phase, phase_id = "PHASE 01 // THE SLOW CLIMB", 1
        speed_mph = 6.4
        g_force = 1.02
        bpm = int(82 + u * 62)
        resp_lmin = round(14.0 + u * 8.2, 1)
        grip_pct = int(38 + u * 50)
        db = round(88.2 + math.sin(u * 48.0) * 1.4, 1)
    elif i < 235:
        u = (i - 145) / 90.0
        phase, phase_id = "PHASE 02 // ZERO-BREATH DROP", 2
        speed_mph = round(6.4 + 122.0 * (math.sin(u * math.pi * 0.65) ** 0.75), 1)
        if u < 0.32:
            g_force = round(-0.9 - 0.5 * math.sin(u / 0.32 * math.pi), 2)
            pitch_deg = -89.5
        else:
            v = (u - 0.32) / 0.68
            g_force = round(1.2 + 3.72 * math.sin(v * math.pi), 2)
        bpm = int(164 + 24 * math.sin(u * math.pi * 0.75))
        resp_lmin = 0.0
        grip_pct = 99
        db = round(109.5 + 5.3 * math.sin(u * math.pi), 1)
    elif i < 345:
        u = (i - 235) / 110.0
        phase, phase_id = "PHASE 03 // TEARDROP LOOP & ROLL", 3
        speed_mph = round(116.0 - u * 18.0, 1)
        g_force = round(3.85 - 2.4 * math.sin(u * math.pi), 2)
        bpm = int(184 - u * 8)
        resp_lmin = 0.0 if u < 0.35 else round((u - 0.35) * 14.0, 1)
        grip_pct = 94
        db = round(111.0 - u * 6.0, 1)
    elif i < 450:
        u = (i - 345) / 105.0
        phase, phase_id = "PHASE 04 // -1.4G EJECTOR AIRTIME", 4
        speed_mph = round(98.0 - u * 16.0, 1)
        g_force = round(-1.40 * math.sin(u * math.pi) + 0.4 * math.cos(u * math.pi * 2), 2)
        bpm = int(175 - u * 11)
        resp_lmin = round(19.2 + 4.5 * math.sin(u * math.pi), 1)
        grip_pct = 89
        db = round(105.0 + 4.2 * math.sin(u * math.pi), 1)
    else:
        u = (i - 450) / 110.0
        phase, phase_id = "PHASE 05 // MAGNETIC FIN BRAKE RUN", 5
        speed_mph = round(max(6.4, 82.0 * (1.0 - u * 0.92)), 1)
        g_force = round(1.0 + 0.65 * (1.0 - u), 2)
        bpm = int(162 - u * 68)
        resp_lmin = round(26.0 - u * 10.0, 1)
        grip_pct = int(72 - u * 44)
        db = round(78.0 - u * 10.0, 1)

    telemetry_samples.append({
        "t": round(t, 4),
        "pos": three_pos,
        "tan": three_tan,
        "up": three_up,
        "side": three_side,
        "alt": alt_ft,
        "speed": speed_mph,
        "g": g_force,
        "pitch": pitch_deg,
        "bank": bank_deg,
        "bpm": bpm,
        "resp": resp_lmin,
        "grip": grip_pct,
        "db": db,
        "phase": phase,
        "phaseId": phase_id,
    })

with open("/tmp/apex_telemetry.json", "w") as f:
    json.dump({"samples": telemetry_samples}, f)

faces = 0
tris = 0
verts = 0
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:
    o.data.calc_loop_triangles()
    faces += len(o.data.polygons)
    tris += len(o.data.loop_triangles)
    verts += len(o.data.vertices)
print("APEX_MANIFEST " + json.dumps({
    "faces": faces,
    "tris": tris,
    "objects": len(meshes),
    "verts": verts,
    "object_names": sorted(o.name for o in meshes),
    "glb": out_glb,
}))
