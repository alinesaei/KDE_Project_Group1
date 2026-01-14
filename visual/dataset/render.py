import bpy
import os
import math
from mathutils import Vector

# =======================
# PATHS
# =======================
ROOT_MODEL_DIR = "Project/models"
OUTPUT_DIR = "Project/renders"

ANGLES = [0, 72, 144, 216, 288]
RENDER_SIZE = 1024

# =======================
# SCENE RESET
# =======================
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for data in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for block in data:
            data.remove(block)

# =======================
# IMPORT
# =======================
def import_model(path):
    bpy.ops.wm.collada_import(filepath=path)

def find_model(folder):
    path = os.path.join(folder, "model.dae")
    return path if os.path.isfile(path) else None

# =======================
# ROOT PARENT (CRITICAL)
# =======================
def create_root():
    root = bpy.data.objects.new("ROOT", None)
    bpy.context.collection.objects.link(root)

    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for m in meshes:
        m.parent = root

    return root, meshes

def force_upright(root):
    # Most Pokédex 3D Collada models are Y-up → convert to Z-up
    root.rotation_euler = (math.radians(-90), 0, 0)

    bpy.context.view_layer.update()

    # Apply rotation so bounds + camera are correct
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

# =======================
# CAMERA
# =======================
def get_bounds(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    center = sum(corners, Vector()) / 8
    radius = max((c - center).length for c in corners)
    return center, radius

def setup_camera(target):
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    center, radius = get_bounds(target)

    cam.data.lens_unit = 'FOV'
    cam.data.angle = math.radians(50)

    dist = radius / math.tan(cam.data.angle / 2)
    cam.location = center + Vector((0, -dist * 1.3, radius * 0.6))
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()

# =======================
# LIGHTING (DARKER)
# =======================
def setup_lighting():
    def add(loc, power, size):
        light = bpy.data.lights.new("Light", 'AREA')
        light.energy = power
        light.size = size
        obj = bpy.data.objects.new("Light", light)
        bpy.context.collection.objects.link(obj)
        obj.location = loc

    add((4, -4, 5), 600, 4)   # Key
    add((-4, -3, 3), 300, 5)  # Fill
    add((0, 4, 4), 400, 3)    # Rim

# =======================
# RENDER SETTINGS
# =======================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = RENDER_SIZE
scene.render.resolution_y = RENDER_SIZE
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'

scene.view_settings.look = 'AgX - Base Contrast'
scene.view_settings.exposure = 0.7

scene.world.use_nodes = True
bg = scene.world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 0.25

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =======================
# MAIN LOOP
# =======================
for name in sorted(os.listdir(ROOT_MODEL_DIR)):
    folder = os.path.join(ROOT_MODEL_DIR, name)
    if not os.path.isdir(folder):
        continue
    
    out_dir = os.path.join(OUTPUT_DIR, name)
    if os.path.exists(out_dir):
        print(f"Alert: {name} has already been rendered...")
        continue
    else:
        os.makedirs(out_dir, exist_ok=True)

    model = find_model(folder)
    if not model:
        print(f"Skipping {name} (no model.dae)")
        continue

    print(f"\n=== Rendering {name} ===")

    clear_scene()
    import_model(model)

    root, meshes = create_root()
    force_upright(root)

    if not meshes:
        print(f"FAILED: {name}")
        continue

    # Camera frames largest mesh
    main_mesh = max(meshes, key=lambda o: len(o.data.vertices))
    setup_camera(main_mesh)
    setup_lighting()

    for angle in ANGLES:
        root.rotation_euler = (0, 0, math.radians(angle))
        scene.render.filepath = f"{out_dir}/{name}_{angle}.png"
        bpy.ops.render.render(write_still=True)

print("\nALL MODELS RENDERED")
