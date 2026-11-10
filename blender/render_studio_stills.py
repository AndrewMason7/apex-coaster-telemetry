import bpy
import math
import json
from mathutils import Vector, Matrix

with open("/tmp/apex_telemetry.json", "r") as f:
    samples = json.load(f)["samples"]

scene = bpy.context.scene

# Configure Cycles + Metal GPU on Apple Silicon
scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences
cprefs = prefs.addons['cycles'].preferences
cprefs.RefreshDevices() if hasattr(cprefs, 'RefreshDevices') else cprefs.get_devices()
for dev_type in ['METAL', 'OPTIX', 'CUDA', 'NONE']:
    try:
        cprefs.compute_device_type = dev_type
        break
    except Exception:
        pass
for dev in cprefs.devices:
    dev.use = True
scene.cycles.device = 'GPU'
scene.cycles.samples = 64
scene.cycles.use_denoising = False

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - High Contrast'

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.008, 0.012, 0.024, 1.0)
    bg_node.inputs[1].default_value = 0.85

if "Studio_Floor" not in bpy.data.objects:
    bpy.ops.mesh.primitive_plane_add(size=160, location=(0, 0, 0))
    fl = bpy.context.active_object
    fl.name = "Studio_Floor"
    mat_fl = bpy.data.materials.new("MAT_Studio_Floor")
    mat_fl.use_nodes = True
    bsdf = mat_fl.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.012, 0.018, 0.032, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.88
    bsdf.inputs["Roughness"].default_value = 0.14
    fl.data.materials.append(mat_fl)

def add_area_light(name, loc, rot_deg, energy, color, size=14.0):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    ldata = bpy.data.lights.new(name=name, type='AREA')
    ldata.energy = energy
    ldata.color = color
    ldata.size = size
    lobj = bpy.data.objects.new(name=name, object_data=ldata)
    lobj.location = loc
    lobj.rotation_euler = [math.radians(a) for a in rot_deg]
    scene.collection.objects.link(lobj)

add_area_light("Key_Light_Top",     (0, -14, 26),   (32, 0, 0),    5200, (0.94, 0.97, 1.0), size=22.0)
add_area_light("Rim_Light_Cyan",    (-14, 12, 16),  (-35, -25, 0), 3400, (0.04, 0.78, 0.98), size=16.0)
add_area_light("Accent_Light_Rose", (2, -10, 14),   (40, 10, 0),   3800, (0.98, 0.16, 0.38), size=14.0)
add_area_light("Fill_Light_Amber",  (14, -12, 14),  (38, 25, 0),   2800, (0.98, 0.65, 0.12), size=14.0)

def three_to_blender(v):
    # Inverse of (x, z, -y): blender_x = v[0], blender_y = -v[2], blender_z = v[1]
    return Vector((v[0], -v[2], v[1]))

def place_train_at_sample(sample_idx):
    for c in range(5):
        k = (sample_idx - c * 8) % len(samples)
        car = bpy.data.objects.get(f"Coaster_Car_{c}")
        if car:
            s = samples[k]
            p = three_to_blender(s["pos"])
            t_v = three_to_blender(s["tan"]).normalized()
            s_v = three_to_blender(s["side"]).normalized()
            n_v = three_to_blender(s["up"]).normalized()
            rot_m = Matrix((
                (t_v.x, s_v.x, n_v.x),
                (t_v.y, s_v.y, n_v.y),
                (t_v.z, s_v.z, n_v.z)
            )).to_4x4()
            car.matrix_world = Matrix.Translation(p) @ rot_m

for old_name in ["Render_Cam", "Cam_Target"]:
    if old_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[old_name], do_unlink=True)

cam_data = bpy.data.cameras.new("Render_Cam")
cam_obj = bpy.data.objects.new("Render_Cam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

target_empty = bpy.data.objects.new("Cam_Target", None)
scene.collection.objects.link(target_empty)
c_track = cam_obj.constraints.new(type='TRACK_TO')
c_track.target = target_empty
c_track.track_axis = 'TRACK_NEGATIVE_Z'
c_track.up_axis = 'UP_Y'

# Shot 1: Wide Architectural Studio Overview
place_train_at_sample(148)
cam_data.lens = 28
cam_obj.location = (-2.0, -30.5, 11.2)
target_empty.location = (0.0, 0.5, 6.5)
scene.render.filepath = "/tmp/cycles_1_wide_overview.png"
bpy.ops.render.render(write_still=True)

# Shot 2: Dramatic Close-Up of the 5-Car Train Diving 89.5° into the Glowing Cyan Tunnel Rings
place_train_at_sample(176)
cam_data.lens = 36
cam_obj.location = (-6.8, -10.2, 6.8)
target_empty.location = (-1.1, 0.4, 5.8)
scene.render.filepath = "/tmp/cycles_2_vertical_plunge_closeup.png"
bpy.ops.render.render(write_still=True)

print("CYCLES_RENDERS_COMPLETE")
