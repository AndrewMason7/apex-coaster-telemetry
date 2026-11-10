import bpy
import bmesh
import math
import json
from mathutils import Vector, Matrix

# ==============================================================================
# 1. CLEAN SCENE & SETUP
# ==============================================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for col in [bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights]:
    for item in list(col):
        col.remove(item)

# ==============================================================================
# 2. PBR ARCHITECTURAL & AEROSPACE MATERIALS
# ==============================================================================
def make_pbr(name, rgb, metallic=0.8, roughness=0.22, emit_rgb=None, emit_str=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if emit_rgb and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emit_rgb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emit_str
    return mat

# Phase Track Spine & Rail Materials
mat_climb   = make_pbr("MAT_Track_Phase1_Cyan",    (0.02, 0.72, 0.85), metallic=0.78, roughness=0.20, emit_rgb=(0.02, 0.72, 0.85), emit_str=0.35)
mat_drop    = make_pbr("MAT_Track_Phase2_Crimson", (0.95, 0.14, 0.34), metallic=0.82, roughness=0.18, emit_rgb=(0.95, 0.14, 0.34), emit_str=0.50)
mat_loop    = make_pbr("MAT_Track_Phase3_Violet",  (0.55, 0.32, 0.96), metallic=0.78, roughness=0.20, emit_rgb=(0.55, 0.32, 0.96), emit_str=0.38)
mat_airtime = make_pbr("MAT_Track_Phase4_Amber",   (0.96, 0.62, 0.04), metallic=0.78, roughness=0.20, emit_rgb=(0.96, 0.62, 0.04), emit_str=0.38)
mat_brake   = make_pbr("MAT_Track_Phase5_Emerald", (0.06, 0.75, 0.51), metallic=0.78, roughness=0.20, emit_rgb=(0.06, 0.75, 0.51), emit_str=0.35)

# Running Steel Rails (Polished Bare Steel where polyurethane wheels roll)
mat_running_steel = make_pbr("MAT_Running_Rail_Steel", (0.82, 0.86, 0.92), metallic=0.94, roughness=0.14)
mat_crosstie_dark = make_pbr("MAT_Crosstie_Graphite",  (0.16, 0.19, 0.25), metallic=0.85, roughness=0.32)
mat_pillar_steel  = make_pbr("MAT_Tower_Column_Steel", (0.12, 0.15, 0.21), metallic=0.88, roughness=0.35)
mat_concrete_pad  = make_pbr("MAT_Concrete_Footer",    (0.22, 0.24, 0.28), metallic=0.15, roughness=0.75)
mat_catwalk_mesh  = make_pbr("MAT_Catwalk_Steel",      (0.20, 0.24, 0.30), metallic=0.80, roughness=0.40)
mat_beacon_red    = make_pbr("MAT_Aviation_Beacon",    (1.00, 0.12, 0.22), metallic=0.20, roughness=0.10, emit_rgb=(1.00, 0.12, 0.22), emit_str=3.5)
mat_tunnel_ring   = make_pbr("MAT_Tunnel_Portal_Cyan", (0.04, 0.82, 0.96), metallic=0.50, roughness=0.15, emit_rgb=(0.04, 0.82, 0.96), emit_str=2.2)

# Articulated Coaster Train Materials
mat_car_shell     = make_pbr("MAT_Car_Aero_Shell",     (0.94, 0.96, 1.00), metallic=0.88, roughness=0.12)
mat_car_trim      = make_pbr("MAT_Car_Laser_Trim",     (0.96, 0.16, 0.36), metallic=0.50, roughness=0.15, emit_rgb=(0.96, 0.16, 0.36), emit_str=2.2)
mat_car_seat      = make_pbr("MAT_Car_Carbon_Seat",    (0.08, 0.09, 0.12), metallic=0.40, roughness=0.45)
mat_car_restraint = make_pbr("MAT_Car_Hydraulic_Bar",  (0.96, 0.62, 0.04), metallic=0.75, roughness=0.22, emit_rgb=(0.96, 0.62, 0.04), emit_str=0.4)
mat_wheel_pu      = make_pbr("MAT_Bogie_Wheel_Cyan",   (0.02, 0.78, 0.92), metallic=0.30, roughness=0.25, emit_rgb=(0.02, 0.78, 0.92), emit_str=1.2)

# ==============================================================================
# 3. CLOSED-CIRCUIT CONTINUOUS 3D SPLINE + BANKING ROLL ANGLE
# ==============================================================================
control_points = [
    # --- PHASE 1: Station & 45-Deg Chain Lift Hill (X: -18 -> -3.5, Y: 0.0, Z: 1.0 -> 14.2) ---
    (-18.0,  0.0,  1.0,   0.0),   # 0: Station dispatch
    (-15.5,  0.0,  1.0,   0.0),   # 1: Lift base engage
    (-12.5,  0.0,  4.2,   0.0),   # 2: Lower lift
    ( -9.5,  0.0,  7.6,   0.0),   # 3: Mid lift
    ( -6.5,  0.0, 11.0,   0.0),   # 4: Upper lift
    ( -4.2,  0.0, 13.8,   0.0),   # 5: Pre-crest
    ( -3.0,  0.0, 14.3,   0.0),   # 6: 420 FT APEX CREST

    # --- PHASE 2: 89.5° Beyond-Vertical Breathless Plunge & +4.92G Trench (X: -3.0 -> +1.8) ---
    ( -2.1, -0.1, 13.4,   5.0),   # 7: Tip-over lip
    ( -1.6, -0.3,  8.5,   8.0),   # 8: 89.5 deg vertical sheer cliff
    ( -1.0, -0.6,  2.4,  12.0),   # 9: High-speed pullout entry
    (  0.4, -1.0,  0.7,  18.0),   # 10: +4.92G Blackout Trench Bottom!
    (  2.0, -1.2,  2.2,  28.0),   # 11: Rising out of trench

    # --- PHASE 3: Tear-Drop Vertical Loop & Banked Immelmann Twist (X: 2.0 -> 8.5) ---
    (  3.6, -0.8,  6.8,  15.0),   # 12: Loop ascent
    (  4.5,  0.0, 10.6,   0.0),   # 13: Inverted Loop Apex
    (  5.4,  0.8,  6.6, -20.0),   # 14: Loop descent
    (  6.8,  1.6,  1.6, -48.0),   # 15: High-G banked sweeping valley
    (  8.6,  2.2,  4.8, -62.0),   # 16: Banked Zero-G Roll entry

    # --- PHASE 4: -1.40G Ejector Airtime Camelback & Banked Helix (X: 8.6 -> 17.5) ---
    ( 10.8,  1.0,  7.8,   0.0),   # 17: Ejector Airtime Crest (-1.40G!)
    ( 13.0, -0.6,  3.2,  35.0),   # 18: Airtime drop valley
    ( 15.6, -2.2,  5.4,  58.0),   # 19: High-speed overbanked turn entry
    ( 17.8,  0.5,  4.6,  68.0),   # 20: Overbanked apex (far right)
    ( 16.2,  4.2,  2.6,  45.0),   # 21: Sweeping return curve

    # --- PHASE 5: Magnetic Eddy-Current Brake Run & Return to Station (Back side Y > 0) ---
    ( 11.5,  5.2,  1.6,  12.0),   # 22: Brake run entry
    (  5.0,  5.2,  1.4,   0.0),   # 23: Copper fin magnetic brakes
    ( -2.5,  5.0,  1.2,   0.0),   # 24: Transfer track straight
    (-10.5,  4.6,  1.1, -15.0),   # 25: Station approach curve
    (-16.8,  3.2,  1.0, -28.0),   # 26: Final turn into station
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

pts = []
banks_rad = []
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
    pos = catmull_rom(v0, v1, v2, v3, u)
    bank_deg = catmull_rom(c0[3], c1[3], c2[3], c3[3], u)
    pts.append(pos)
    banks_rad.append(math.radians(bank_deg))

tangents = []
sides = []
normals = []
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

    b_ang = banks_rad[i]
    cos_b = math.cos(b_ang)
    sin_b = math.sin(b_ang)
    side = (raw_side * cos_b + raw_norm * sin_b).normalized()
    norm = side.cross(t_vec).normalized()

    tangents.append(t_vec)
    sides.append(side)
    normals.append(norm)

# ==============================================================================
# 4. BUILD REALISTIC B&M / INTAMIN 4-TUBE BOX-SPINE TRACK & CROSSTIES
# ==============================================================================
phase_defs = [
    ("Track_Phase1_SlowClimb",      0, 146, mat_climb),
    ("Track_Phase2_ZeroBreathDrop", 145, 236, mat_drop),
    ("Track_Phase3_InversionLoop",  235, 346, mat_loop),
    ("Track_Phase4_AirtimeHill",    345, 451, mat_airtime),
    ("Track_Phase5_BrakeRun",       450, 561, mat_brake),
]

RAIL_GAUGE_HALF = 0.26
SPINE_DEPTH = -0.24
R_RAIL = 0.042
R_SPINE = 0.085

def add_swept_tube(bm, indices, offset_side, offset_norm, radius, n_sides=8, mat_index=0):
    rings = []
    for idx in indices:
        k_idx = idx % N_SAMPLES
        p = pts[k_idx]
        s = sides[k_idx]
        n = normals[k_idx]
        center = p + s * offset_side + n * offset_norm
        ring = []
        for c in range(n_sides):
            ang = 2.0 * math.pi * c / n_sides
            v_pos = center + s * (math.cos(ang) * radius) + n * (math.sin(ang) * radius)
            ring.append(bm.verts.new(v_pos))
        rings.append(ring)

    for r_i in range(len(rings) - 1):
        r1 = rings[r_i]
        r2 = rings[r_i + 1]
        for c in range(n_sides):
            c_next = (c + 1) % n_sides
            f = bm.faces.new((r1[c], r2[c], r2[c_next], r1[c_next]))
            f.material_index = mat_index
            f.smooth = True

def add_strut(bm, p_a, p_b, radius, segments=6, mat_index=0):
    vec = p_b - p_a
    length = vec.length
    if length < 1e-4:
        return
    mid = (p_a + p_b) * 0.5
    rot = Vector((0, 0, 1)).rotation_difference(vec.normalized()).to_matrix().to_4x4()
    res = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segments,
        radius1=radius, radius2=radius, depth=length,
        matrix=Matrix.Translation(mid) @ rot
    )
    for v in res["verts"]:
        for f in v.link_faces:
            f.material_index = mat_index

for seg_name, i_start, i_end, phase_mat in phase_defs:
    bm = bmesh.new()
    idxs = list(range(i_start, i_end))

    add_swept_tube(bm, idxs,  0.0,              SPINE_DEPTH,        R_SPINE, n_sides=10, mat_index=0)
    add_swept_tube(bm, idxs, -RAIL_GAUGE_HALF*0.55, SPINE_DEPTH*0.55, R_RAIL*0.65, n_sides=6, mat_index=0)
    add_swept_tube(bm, idxs,  RAIL_GAUGE_HALF*0.55, SPINE_DEPTH*0.55, R_RAIL*0.65, n_sides=6, mat_index=0)

    add_swept_tube(bm, idxs, -RAIL_GAUGE_HALF, 0.0, R_RAIL, n_sides=8, mat_index=0)
    add_swept_tube(bm, idxs,  RAIL_GAUGE_HALF, 0.0, R_RAIL, n_sides=8, mat_index=0)
    add_swept_tube(bm, idxs, -RAIL_GAUGE_HALF*0.92, 0.025, R_RAIL*0.45, n_sides=6, mat_index=1)
    add_swept_tube(bm, idxs,  RAIL_GAUGE_HALF*0.92, 0.025, R_RAIL*0.45, n_sides=6, mat_index=1)

    for step in range(i_start, i_end - 1, 2):
        k0 = step % N_SAMPLES
        k1 = min(i_end - 1, step + 2) % N_SAMPLES
        p0, s0, n0 = pts[k0], sides[k0], normals[k0]
        p1, s1, n1 = pts[k1], sides[k1], normals[k1]

        l_rail0 = p0 - s0 * RAIL_GAUGE_HALF
        r_rail0 = p0 + s0 * RAIL_GAUGE_HALF
        spine0  = p0 + n0 * SPINE_DEPTH
        spine1  = p1 + n1 * SPINE_DEPTH
        l_rail1 = p1 - s1 * RAIL_GAUGE_HALF
        r_rail1 = p1 + s1 * RAIL_GAUGE_HALF

        add_strut(bm, spine0, l_rail0, 0.024, segments=6, mat_index=2)
        add_strut(bm, spine0, r_rail0, 0.024, segments=6, mat_index=2)
        add_strut(bm, l_rail0, r_rail0, 0.018, segments=6, mat_index=2)
        add_strut(bm, spine0, l_rail1, 0.016, segments=5, mat_index=0)
        add_strut(bm, spine0, r_rail1, 0.016, segments=5, mat_index=0)

    mesh = bpy.data.meshes.new(seg_name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(seg_name, mesh)
    obj.data.materials.append(phase_mat)
    obj.data.materials.append(mat_running_steel)
    obj.data.materials.append(mat_crosstie_dark)
    bpy.context.collection.objects.link(obj)

# ==============================================================================
# 5. LIFT HILL CATWALK STAIRS, HANDRAILS & CHAIN TROUGH + TUNNEL PORTAL
# ==============================================================================
bm_catwalk = bmesh.new()
lift_idxs = list(range(12, 138))
add_swept_tube(bm_catwalk, lift_idxs, -0.58,  0.32, 0.018, n_sides=6, mat_index=0)
add_swept_tube(bm_catwalk, lift_idxs, -0.58, -0.05, 0.025, n_sides=6, mat_index=0)
add_swept_tube(bm_catwalk, lift_idxs,  0.00, -0.04, 0.045, n_sides=6, mat_index=1)
for k in range(14, 136, 4):
    p, s, n = pts[k], sides[k], normals[k]
    post_bot = p - s * 0.58 - n * 0.08
    post_top = p - s * 0.58 + n * 0.32
    add_strut(bm_catwalk, post_bot, post_top, 0.014, segments=5, mat_index=0)
    add_strut(bm_catwalk, p - s * RAIL_GAUGE_HALF, post_bot, 0.018, segments=5, mat_index=0)

for k in [184, 192, 200, 208, 216]:
    p, t_v, s, n = pts[k], tangents[k], sides[k], normals[k]
    ring_pts = []
    n_ring = 20
    for c in range(n_ring):
        ang = 2.0 * math.pi * c / n_ring
        ring_pts.append(p + n * 0.25 + s * (math.cos(ang) * 0.95) + n * (math.sin(ang) * 0.95))
    for c in range(n_ring):
        add_strut(bm_catwalk, ring_pts[c], ring_pts[(c + 1) % n_ring], 0.042, segments=6, mat_index=1)

mesh_cw = bpy.data.meshes.new("Catwalk_And_Tunnel_Portals")
bm_catwalk.to_mesh(mesh_cw)
bm_catwalk.free()
obj_cw = bpy.data.objects.new("Catwalk_And_Tunnel_Portals", mesh_cw)
obj_cw.data.materials.append(mat_catwalk_mesh)
obj_cw.data.materials.append(mat_tunnel_ring)
bpy.context.collection.objects.link(obj_cw)

# ==============================================================================
# 6. HEAVY ENGINEERING LATTICE SUPPORT TOWERS, A-FRAMES & AVIATION BEACONS
# ==============================================================================
bm_towers = bmesh.new()
tower_samples = list(range(8, N_SAMPLES, 14))
for k in tower_samples:
    p = pts[k]
    n = normals[k]
    s = sides[k]
    attach = p + n * SPINE_DEPTH
    if attach.z > 0.65:
        if attach.z > 7.5:
            spread = 0.85 + (attach.z - 7.5) * 0.14
            foot_L = Vector((attach.x - s.x * spread, attach.y - s.y * spread, 0.0))
            foot_R = Vector((attach.x + s.x * spread, attach.y + s.y * spread, 0.0))
            add_strut(bm_towers, foot_L, attach, 0.085, segments=8, mat_index=0)
            add_strut(bm_towers, foot_R, attach, 0.085, segments=8, mat_index=0)
            for frac in [0.35, 0.68]:
                mL = foot_L.lerp(attach, frac)
                mR = foot_R.lerp(attach, frac)
                add_strut(bm_towers, mL, mR, 0.048, segments=6, mat_index=0)
            for ft in [foot_L, foot_R]:
                bmesh.ops.create_cone(
                    bm_towers, cap_ends=True, cap_tris=False, segments=10,
                    radius1=0.32, radius2=0.24, depth=0.28,
                    matrix=Matrix.Translation(ft + Vector((0, 0, 0.14)))
                )
        else:
            foot = Vector((attach.x, attach.y, 0.0))
            add_strut(bm_towers, foot, attach, 0.075, segments=8, mat_index=0)
            bmesh.ops.create_cone(
                bm_towers, cap_ends=True, cap_tris=False, segments=10,
                radius1=0.28, radius2=0.22, depth=0.24,
                matrix=Matrix.Translation(foot + Vector((0, 0, 0.12)))
            )

for k in [136, 144, 282]:
    top_pos = pts[k] + Vector((0, 0, 0.55))
    add_strut(bm_towers, pts[k], top_pos, 0.022, segments=6, mat_index=0)
    res = bmesh.ops.create_icosphere(bm_towers, subdivisions=2, radius=0.14, matrix=Matrix.Translation(top_pos))
    for v in res["verts"]:
        for f in v.link_faces:
            f.material_index = 2

mesh_towers = bpy.data.meshes.new("Support_Pillars")
bm_towers.to_mesh(mesh_towers)
bm_towers.free()
obj_towers = bpy.data.objects.new("Support_Pillars", mesh_towers)
obj_towers.data.materials.append(mat_pillar_steel)
obj_towers.data.materials.append(mat_concrete_pad)
obj_towers.data.materials.append(mat_beacon_red)
bpy.context.collection.objects.link(obj_towers)

# ==============================================================================
# 7. BUILD 5 ARTICULATED AEROSPACE COASTER CARS (LEAD CAR + 4 TRAILING CARS)
# ==============================================================================
def create_coaster_car(name, is_lead=False):
    bm = bmesh.new()

    length = 1.15 if is_lead else 0.95
    bmesh.ops.create_cube(
        bm, size=1.0,
        matrix=Matrix.Translation((0.0, 0.0, 0.20)) @ Matrix.Diagonal((length, 0.62, 0.26, 1.0))
    )
    if is_lead:
        rot_y = Matrix.Rotation(math.pi * 0.5, 4, 'Y')
        res_nose = bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=False, segments=14,
            radius1=0.31, radius2=0.06, depth=0.65,
            matrix=Matrix.Translation((0.82, 0.0, 0.16)) @ rot_y
        )
        for v in res_nose["verts"]:
            for f in v.link_faces:
                f.smooth = True

    for y_sign in [-1.0, 1.0]:
        res_trim = bmesh.ops.create_cube(
            bm, size=1.0,
            matrix=Matrix.Translation((0.05 if is_lead else 0.0, y_sign * 0.32, 0.20)) @ Matrix.Diagonal((length * 0.92, 0.03, 0.06, 1.0))
        )
        for v in res_trim["verts"]:
            for f in v.link_faces:
                f.material_index = 1

    for y_seat in [-0.16, 0.16]:
        res_seat = bmesh.ops.create_cube(
            bm, size=1.0,
            matrix=Matrix.Translation((-0.08, y_seat, 0.42)) @ Matrix.Diagonal((0.22, 0.22, 0.36, 1.0))
        )
        for v in res_seat["verts"]:
            for f in v.link_faces:
                f.material_index = 2
        res_bar = bmesh.ops.create_cube(
            bm, size=1.0,
            matrix=Matrix.Translation((0.08, y_seat, 0.38)) @ Matrix.Diagonal((0.24, 0.18, 0.07, 1.0))
        )
        for v in res_bar["verts"]:
            for f in v.link_faces:
                f.material_index = 3

    rot_wheel = Matrix.Rotation(math.pi * 0.5, 4, 'X')
    for x_bogie in ([-0.35, 0.35] if is_lead else [-0.30, 0.30]):
        for y_rail in [-RAIL_GAUGE_HALF, RAIL_GAUGE_HALF]:
            for z_wheel, r_w in [(0.055, 0.065), (-0.055, 0.052)]:
                res_w = bmesh.ops.create_cone(
                    bm, cap_ends=True, cap_tris=False, segments=10,
                    radius1=r_w, radius2=r_w, depth=0.045,
                    matrix=Matrix.Translation((x_bogie, y_rail, z_wheel)) @ rot_wheel
                )
                for v in res_w["verts"]:
                    for f in v.link_faces:
                        f.material_index = 4

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat_car_shell)
    obj.data.materials.append(mat_car_trim)
    obj.data.materials.append(mat_car_seat)
    obj.data.materials.append(mat_car_restraint)
    obj.data.materials.append(mat_wheel_pu)
    bpy.context.collection.objects.link(obj)
    return obj

for car_idx in range(5):
    create_coaster_car(f"Coaster_Car_{car_idx}", is_lead=(car_idx == 0))

# ==============================================================================
# 8. EXPORT GLB + HIGH-PRECISION 560-FRAME TELEMETRY & ORIENTATION SIDECAR
# ==============================================================================
out_glb = "/tmp/apex_coaster.glb"
bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB', use_selection=False, export_apply=True)

telemetry_samples = []
for i in range(N_SAMPLES):
    t = i / N_SAMPLES
    p = pts[i]
    t_vec = tangents[i]
    s_vec = sides[i]
    n_vec = normals[i]

    three_pos  = [round(p.x, 4),     round(p.z, 4),     round(-p.y, 4)]
    three_tan  = [round(t_vec.x, 4), round(t_vec.z, 4), round(-t_vec.y, 4)]
    three_up   = [round(n_vec.x, 4), round(n_vec.z, 4), round(-n_vec.y, 4)]
    three_side = [round(s_vec.x, 4), round(s_vec.z, 4), round(-s_vec.y, 4)]

    alt_ft = round(max(0.0, (p.z - 0.7) / 13.6 * 420.0), 1)
    pitch_deg = round(math.degrees(math.asin(max(-1.0, min(1.0, t_vec.z)))), 1)
    bank_deg = round(math.degrees(banks_rad[i]), 1)

    if i < 145:
        u = i / 145.0
        phase = "PHASE 01 // THE SLOW CLIMB"
        phase_id = 1
        speed_mph = 6.4
        g_force = 1.02
        bpm = int(82 + u * 62)
        resp_lmin = round(14.0 + u * 8.2, 1)
        grip_pct = int(38 + u * 50)
        db = round(88.2 + math.sin(u * 48.0) * 1.4, 1)
    elif i < 235:
        u = (i - 145) / 90.0
        phase = "PHASE 02 // ZERO-BREATH DROP"
        phase_id = 2
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
        phase = "PHASE 03 // TEARDROP LOOP & ROLL"
        phase_id = 3
        speed_mph = round(116.0 - u * 18.0, 1)
        g_force = round(3.85 - 2.4 * math.sin(u * math.pi), 2)
        bpm = int(184 - u * 8)
        resp_lmin = 0.0 if u < 0.35 else round((u - 0.35) * 14.0, 1)
        grip_pct = 94
        db = round(111.0 - u * 6.0, 1)
    elif i < 450:
        u = (i - 345) / 105.0
        phase = "PHASE 04 // -1.4G EJECTOR AIRTIME"
        phase_id = 4
        speed_mph = round(98.0 - u * 16.0, 1)
        g_force = round(-1.40 * math.sin(u * math.pi) + 0.4 * math.cos(u * math.pi * 2), 2)
        bpm = int(175 - u * 11)
        resp_lmin = round(19.2 + 4.5 * math.sin(u * math.pi), 1)
        grip_pct = 89
        db = round(105.0 + 4.2 * math.sin(u * math.pi), 1)
    else:
        u = (i - 450) / 110.0
        phase = "PHASE 05 // MAGNETIC FIN BRAKE RUN"
        phase_id = 5
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
        "phaseId": phase_id
    })

with open("/tmp/apex_telemetry.json", "w") as f:
    json.dump({"samples": telemetry_samples}, f)

total_faces = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print(f"BENCHMARK_BAKE_COMPLETE: {len(bpy.data.objects)} objects, {total_faces} faces, {len(telemetry_samples)} frames")
