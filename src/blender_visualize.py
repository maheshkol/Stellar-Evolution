# src/blender_visualize.py
# Run inside Blender:
# blender --background --python src/blender_visualize.py -- data/processed/gaia_processed.csv --n 24 --out visualizations/stars_visual.blend

import bpy
import sys
import os
import json
import math
import csv
from mathutils import Color

# -----------------------
# parse args after "--"
# -----------------------
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

# defaults
input_path = argv[0] if len(argv) >= 1 else "data/processed/gaia_processed.csv"
# parse --n <int>
n_stars = 24
if "--n" in argv:
    try:
        idx = argv.index("--n")
        n_stars = int(argv[idx + 1])
    except Exception:
        pass
# parse --out <path>
out_blend = "visualizations/stars_visual.blend"
if "--out" in argv:
    try:
        idx = argv.index("--out")
        out_blend = argv[idx + 1]
    except Exception:
        pass

# ensure output dir exists
out_dir = os.path.dirname(out_blend)
if out_dir and not os.path.exists(out_dir):
    os.makedirs(out_dir, exist_ok=True)

# -----------------------
# Clear scene to empty
# -----------------------
bpy.ops.wm.read_factory_settings(use_empty=True)

# -----------------------
# Setup scene safely
# -----------------------
def setup_scene():
    # ensure a world exists
    if bpy.context.scene.world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world = bpy.context.scene.world
    world.use_nodes = True
    # set background
    nt = world.node_tree
    # remove existing nodes safely
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.01, 0.01, 0.02, 1)
    bg.inputs[1].default_value = 0.35
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs[0])

    # Camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, -30.0, 10.0)
    cam_obj.rotation_euler = (math.radians(60), 0, 0)
    bpy.context.scene.camera = cam_obj

    # Light
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_data.energy = 3.0
    light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
    light_obj.location = (0.0, 0.0, 30.0)
    bpy.context.collection.objects.link(light_obj)

    # Render engine: prefer CYCLES if available, else EEVEE
    engines = bpy.context.preferences.addons.keys()
    # safe choice: try to set to 'CYCLES' if available in builds
    try:
        bpy.context.scene.render.engine = 'CYCLES'
    except Exception:
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'

    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

setup_scene()

# -----------------------
# Utilities
# -----------------------
def teff_to_rgb(teff):
    # Guard
    try:
        t = float(teff)
    except Exception:
        t = 5500.0
    t = max(1000.0, min(40000.0, t))
    t_norm = (math.log10(t) - math.log10(3000.0)) / (math.log10(30000.0) - math.log10(3000.0))
    hue = 0.66 - 0.66 * t_norm
    c = Color()
    c.hsv = (hue, 0.9, 1.0)
    r,g,b = c.r, c.g, c.b
    if t > 8000:
        r = min(1.0, r + 0.15)
        g = min(1.0, g + 0.1)
    return (r, g, b, 1.0)

def mass_to_radius(mass_est):
    try:
        m = float(mass_est)
    except Exception:
        m = 1.0
    radius = 0.4 * (max(0.01, m) ** (1/3))
    return max(0.08, min(radius, 6.0))

def make_material(name, color, emission_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    # clear nodes safely
    for n in list(nodes):
        nodes.remove(n)
    output = nodes.new(type='ShaderNodeOutputMaterial')
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    emission = nodes.new(type='ShaderNodeEmission')
    mix = nodes.new(type='ShaderNodeMixShader')
    # set values
    principled.inputs['Base Color'].default_value = color
    principled.inputs['Roughness'].default_value = 0.6
    emission.inputs['Color'].default_value = color
    emission.inputs['Strength'].default_value = emission_strength
    # link
    links.new(principled.outputs['BSDF'], mix.inputs[1])
    links.new(emission.outputs['Emission'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])
    mix.inputs['Fac'].default_value = 0.5
    return mat, emission, principled, mix

# Animation frames
FRAME_MAIN = 1
FRAME_RED = 30
FRAME_COLLAPSE = 60
FRAME_REMNANT = 90
TOTAL_FRAMES = 120
bpy.context.scene.frame_start = FRAME_MAIN
bpy.context.scene.frame_end = TOTAL_FRAMES

# Load input (prefer JSON simulations, else CSV)
use_simulations = False
data = []
if input_path.endswith('.json') and os.path.exists(input_path):
    with open(input_path, 'r') as f:
        data = json.load(f)
    use_simulations = True
else:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(input_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)

data = data[:n_stars]
n = len(data)
print(f"Visualizing {n} stars from {input_path} (use_simulations={use_simulations})")

# Create collection
coll = bpy.data.collections.new("Stars")
bpy.context.scene.collection.children.link(coll)

cols = int(math.ceil(math.sqrt(n)))
rows = int(math.ceil(n / cols))
spacing_x = 6.0
spacing_y = 6.0

def create_star_object(index, mass_est, teff, timeline=None):
    col_i = index % cols
    row_i = index // cols
    x = (col_i - cols/2) * spacing_x
    y = (row_i - rows/2) * spacing_y
    z = 0.0
    radius = mass_to_radius(mass_est)
    color = teff_to_rgb(teff)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(x,y,z))
    obj = bpy.context.active_object
    obj.scale = (radius, radius, radius)
    obj.name = f"Star_{index}"
    coll.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)
    mat, emiss, princ, mix = make_material(f"Mat_Star_{index}", color, emission_strength=2.0)
    obj.data.materials.append(mat)
    # keyframes initial
    obj.keyframe_insert(data_path="scale", frame=FRAME_MAIN)
    try:
        emiss.inputs['Strength'].default_value = 1.0
        emiss.inputs['Strength'].keyframe_insert(data_path='default_value', frame=FRAME_MAIN)
    except Exception:
        pass

    # timeline or heuristic
    if use_simulations and timeline:
        nsteps = len(timeline)
        frames_per_step = max(1, int((FRAME_REMNANT - FRAME_MAIN) / nsteps))
        current_frame = FRAME_MAIN
        for st in timeline:
            stage_name = st.get('stage','').lower()
            if 'main' in stage_name:
                obj.scale = (radius, radius, radius)
                obj.keyframe_insert(data_path="scale", frame=current_frame)
            elif 'red' in stage_name or 'giant' in stage_name:
                obj.scale = (radius*4.0, radius*4.0, radius*4.0)
                obj.keyframe_insert(data_path="scale", frame=current_frame + frames_per_step//2)
                try:
                    princ.inputs['Base Color'].default_value = (1.0,0.3,0.1,1.0)
                    princ.inputs['Base Color'].keyframe_insert(data_path='default_value', frame=current_frame + frames_per_step//2)
                except Exception:
                    pass
            elif 'core' in stage_name or 'collapse' in stage_name or 'supernova' in stage_name:
                try:
                    emiss.inputs['Strength'].default_value = 20.0
                    emiss.inputs['Strength'].keyframe_insert(data_path='default_value', frame=current_frame + frames_per_step//2)
                except Exception:
                    pass
                obj.scale = (radius*0.2, radius*0.2, radius*0.2)
                obj.keyframe_insert(data_path="scale", frame=current_frame + frames_per_step)
            elif 'white' in stage_name:
                obj.scale = (radius*0.6, radius*0.6, radius*0.6)
                obj.keyframe_insert(data_path="scale", frame=current_frame + frames_per_step)
            elif 'neutron' in stage_name:
                obj.scale = (radius*0.15, radius*0.15, radius*0.15)
                obj.keyframe_insert(data_path="scale", frame=current_frame + frames_per_step)
            elif 'black' in stage_name:
                obj.scale = (radius*0.02, radius*0.02, radius*0.02)
                obj.keyframe_insert(data_path="scale", frame=current_frame + frames_per_step)
            current_frame += frames_per_step
    else:
        # heuristic by mass_est
        try:
            m = float(mass_est)
        except Exception:
            m = 1.0
        obj.scale = (radius, radius, radius)
        obj.keyframe_insert(data_path="scale", frame=FRAME_MAIN)
        if m < 8:
            obj.scale = (radius*4.0, radius*4.0, radius*4.0)
            obj.keyframe_insert(data_path="scale", frame=FRAME_RED)
            obj.scale = (radius*0.6, radius*0.6, radius*0.6)
            obj.keyframe_insert(data_path="scale", frame=FRAME_REMNANT)
        elif m < 20:
            obj.scale = (radius*5.0, radius*5.0, radius*5.0)
            obj.keyframe_insert(data_path="scale", frame=FRAME_RED)
            try:
                emiss.inputs['Strength'].default_value = 18.0
                emiss.inputs['Strength'].keyframe_insert(data_path='default_value', frame=FRAME_COLLAPSE)
            except Exception:
                pass
            obj.scale = (radius*0.15, radius*0.15, radius*0.15)
            obj.keyframe_insert(data_path="scale", frame=FRAME_REMNANT)
        else:
            obj.scale = (radius*6.0, radius*6.0, radius*6.0)
            obj.keyframe_insert(data_path="scale", frame=FRAME_RED)
            try:
                emiss.inputs['Strength'].default_value = 30.0
                emiss.inputs['Strength'].keyframe_insert(data_path='default_value', frame=FRAME_COLLAPSE)
            except Exception:
                pass
            obj.scale = (radius*0.02, radius*0.02, radius*0.02)
            obj.keyframe_insert(data_path="scale", frame=FRAME_REMNANT)

    return obj

# create star objects
for i, row in enumerate(data):
    if i >= n_stars:
        break
    try:
        if use_simulations:
            timeline = row.get('timeline', None)
            first = timeline[0] if timeline and len(timeline) > 0 else {}
            mass_est = first.get('mass', 1.0)
            teff = first.get('teff', 5000)
            create_star_object(i, mass_est, teff, timeline=timeline)
        else:
            mass_est = row.get('mass_est') or row.get('mass_solar') or row.get('mass') or 1.0
            teff = row.get('teff') or row.get('teff_gspphot') or 5500
            # cast
            try:
                mass_val = float(mass_est)
            except Exception:
                mass_val = 1.0
            try:
                teff_val = float(teff)
            except Exception:
                teff_val = 5500.0
            create_star_object(i, mass_val, teff_val)
    except Exception as e:
        print(f"Error creating star {i}: {e}")

# parent to empty and rotate
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
root = bpy.context.active_object
root.name = "Scene_Root"
for o in coll.objects:
    o.parent = root

root.rotation_euler = (0,0,0)
root.keyframe_insert(data_path="rotation_euler", frame=1)
root.rotation_euler = (0, 0, math.radians(360))
root.keyframe_insert(data_path="rotation_euler", frame=TOTAL_FRAMES)

# Save blend
bpy.ops.wm.save_mainfile(filepath=out_blend)
print("Saved Blender scene to", out_blend)

