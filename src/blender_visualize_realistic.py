# src/blender_visualize_realistic.py
# Run inside Blender:
# blender --background --python src/blender_visualize_realistic.py -- data/processed/gaia_processed.csv --n 24 --out visualizations/stars_visual_realistic.blend

import bpy, sys, os, math, json, csv
from mathutils import Color

# -----------------------
# parse args after "--"
# -----------------------
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

input_path = argv[0] if len(argv) >= 1 else "data/processed/gaia_processed.csv"
n_stars = 24
if "--n" in argv:
    try:
        n_stars = int(argv[argv.index("--n") + 1])
    except Exception:
        pass
out_blend = "visualizations/stars_visual_realistic.blend"
if "--out" in argv:
    try:
        out_blend = argv[argv.index("--out")+1]
    except Exception:
        pass

out_dir = os.path.dirname(out_blend)
if out_dir and not os.path.exists(out_dir):
    os.makedirs(out_dir, exist_ok=True)

# clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# safe scene/world setup
def setup_scene():
    sc = bpy.context.scene
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    world = sc.world
    world.use_nodes = True
    nt = world.node_tree
    # clear nodes
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.01,0.01,0.02,1)
    bg.inputs[1].default_value = 0.25
    out = nt.nodes.new("ShaderNodeOutputWorld")
    try:
        nt.links.new(bg.outputs[0], out.inputs[0])
    except Exception:
        pass

    # Camera
    cam = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, -35.0, 12.0)
    cam_obj.rotation_euler = (math.radians(60), 0, 0)
    sc.camera = cam_obj

    # Light
    light_data = bpy.data.lights.new("Sun", type='SUN')
    light_data.energy = 3.0
    sun = bpy.data.objects.new("Sun", object_data=light_data)
    sun.location = (0,0,40)
    bpy.context.collection.objects.link(sun)

    # Render engine
    try:
        sc.render.engine = 'CYCLES'
        if sc.render.engine == 'CYCLES':
            # safe set if available
            try:
                sc.cycles.samples = 32
            except Exception:
                pass
    except Exception:
        sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1080
    sc.render.image_settings.file_format = 'PNG'

setup_scene()

# Frames / animation times
FRAME_MAIN = 1
FRAME_RED = 30
FRAME_COLLAPSE = 60
FRAME_REMNANT = 90
TOTAL_FRAMES = 120
bpy.context.scene.frame_start = FRAME_MAIN
bpy.context.scene.frame_end = TOTAL_FRAMES

# Utilities
def safe_float(x, default=1.0):
    try:
        return float(x)
    except Exception:
        return default

def mass_to_radius(m):
    m = safe_float(m, 1.0)
    radius = 0.4 * (max(0.01, m) ** (1/3))
    return max(0.06, min(radius, 6.0))

def teff_to_preview_rgb(teff):
    t = safe_float(teff, 5500.0)
    t = max(1000.0, min(40000.0, t))
    t_norm = (math.log10(t)-math.log10(3000.0)) / (math.log10(30000.0)-math.log10(3000.0))
    hue = 0.66 - 0.66 * t_norm
    c = Color()
    c.hsv = (hue, 0.9, 1.0)
    return (c.r, c.g, c.b, 1.0)

# create a material using Blackbody -> Emission blended with Principled
def create_blackbody_material(name, teff, emission_strength=5.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    # clear nodes
    for n in list(nodes):
        nodes.remove(n)
    output = nodes.new(type='ShaderNodeOutputMaterial')
    mix = nodes.new(type='ShaderNodeMixShader')
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    emission = nodes.new(type='ShaderNodeEmission')
    # Blackbody node may not exist on some builds but usually does
    try:
        blackbody = nodes.new(type='ShaderNodeBlackbody')
        blackbody_exists = True
    except Exception:
        # fallback: we will use preview RGB mapping
        blackbody = None
        blackbody_exists = False

    # If blackbody exists, set temperature; otherwise set principled base color from preview
    if blackbody_exists:
        try:
            blackbody.inputs['Temperature'].default_value = safe_float(teff, 5500.0)
        except Exception:
            # some versions name inputs differently; try index access (0)
            try:
                blackbody.inputs[0].default_value = safe_float(teff, 5500.0)
            except Exception:
                pass
        # connect blackbody -> emission & principled base color
        try:
            links.new(blackbody.outputs['Color'], emission.inputs['Color'])
        except Exception:
            pass
        try:
            links.new(blackbody.outputs['Color'], principled.inputs['Base Color'])
        except Exception:
            # fallback: set base color directly
            principled.inputs['Base Color'].default_value = teff_to_preview_rgb(teff)
    else:
        # no blackbody node: fallback color
        try:
            principled.inputs['Base Color'].default_value = teff_to_preview_rgb(teff)
            emission.inputs['Color'].default_value = teff_to_preview_rgb(teff)
        except Exception:
            pass

    # set principled defaults defensively
    try:
        if 'Roughness' in principled.inputs:
            principled.inputs['Roughness'].default_value = 0.35
    except Exception:
        pass
    try:
        if 'Specular' in principled.inputs:
            principled.inputs['Specular'].default_value = 0.5
    except Exception:
        # some builds don't expose 'Specular' key; ignore
        pass

    # emission strength
    try:
        emission.inputs['Strength'].default_value = emission_strength
    except Exception:
        pass

    # link principled & emission with mix node if available
    try:
        links.new(principled.outputs['BSDF'], mix.inputs[1])
        links.new(emission.outputs['Emission'], mix.inputs[2])
        mix.inputs['Fac'].default_value = 0.35
        links.new(mix.outputs['Shader'], output.inputs['Surface'])
    except Exception:
        # fallback: link principled directly to output
        try:
            links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        except Exception:
            pass

    return mat, emission, principled, blackbody

# create particle system for supernova
def add_supernova_particles(obj, name="SN_Particles", burst_frame=FRAME_COLLAPSE):
    # emitter - small icosphere
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.01, location=obj.location)
    emitter = bpy.context.active_object
    emitter.name = f"{obj.name}_SN_Emitter"
    emitter.scale = obj.scale
    emitter.hide_render = True

    # particle system
    ps = emitter.modifiers.new(name, type='PARTICLE_SYSTEM')
    psys = ps.particle_system
    settings = psys.settings
    settings.count = 800
    settings.frame_start = burst_frame
    settings.frame_end = burst_frame + 2
    settings.lifetime = 60
    settings.emit_from = 'VOLUME'
    settings.physics_type = 'NEWTON'
    settings.normal_factor = 6.0
    settings.factor_random = 2.0
    settings.use_rotations = True
    settings.angular_velocity_mode = 'VELOCITY'

    # create particle object (small sphere)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(0,0,0))
    p_obj = bpy.context.active_object
    p_obj.name = f"{obj.name}_SN_Particle"
    # give particle a simple emission material
    try:
        pmat, _, _, _ = create_blackbody_material(f"{p_obj.name}_mat", teff=8000, emission_strength=6.0)
        if p_obj.data.materials:
            p_obj.data.materials[0] = pmat
        else:
            p_obj.data.materials.append(pmat)
    except Exception:
        pass

    settings.render_type = 'OBJECT'
    settings.instance_object = p_obj
    settings.particle_size = 0.05
    settings.size_random = 0.8

    return emitter, p_obj

# load input data
use_sim = False
data = []
if input_path.endswith('.json') and os.path.exists(input_path):
    with open(input_path, 'r') as f:
        data = json.load(f)
    use_sim = True
else:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing input: {input_path}")
    with open(input_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for r in reader:
            data.append(r)

data = data[:n_stars]
n = len(data)
print("Visualizing", n, "stars (use_simulations=", use_sim, ")")

# create collection
coll = bpy.data.collections.new("Stars")
bpy.context.scene.collection.children.link(coll)

cols = int(math.ceil(math.sqrt(n)))
rows = int(math.ceil(n / cols))
spacing = 6.0

def create_star(index, mass_est, teff, timeline=None):
    col_i = index % cols
    row_i = index // cols
    x = (col_i - cols/2) * spacing
    y = (row_i - rows/2) * spacing
    z = 0.0
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(x,y,z))
    obj = bpy.context.active_object
    radius = mass_to_radius(mass_est)
    obj.scale = (radius, radius, radius)
    obj.name = f"Star_{index}"
    coll.objects.link(obj)
    try:
        bpy.context.scene.collection.objects.unlink(obj)
    except Exception:
        pass

    # material with Blackbody node
    mat, emiss, princ, blackbody = create_blackbody_material(f"Mat_Star_{index}", teff, emission_strength=4.0)
    try:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    except Exception:
        pass

    # set initial keyframes
    try:
        obj.keyframe_insert(data_path="scale", frame=FRAME_MAIN)
    except Exception:
        pass
    try:
        emiss.inputs['Strength'].default_value = 1.0
        emiss.inputs['Strength'].keyframe_insert(data_path='default_value', frame=FRAME_MAIN)
    except Exception:
        pass

    # timeline animation
    if use_sim and timeline:
        nsteps = max(1, len(timeline))
        step_frames = max(1, int((FRAME_REMNANT - FRAME_MAIN) / nsteps))
        cf = FRAME_MAIN
        for st in timeline:
            stage = str(st.get('stage','')).lower()
            if 'main' in stage:
                try:
                    obj.scale = (radius, radius, radius)
                    obj.keyframe_insert(data_path="scale", frame=cf)
                except Exception:
                    pass
            elif 'red' in stage or 'giant' in stage:
                try:
                    obj.scale = (radius*4.0, radius*4.0, radius*4.0)
                    obj.keyframe_insert(data_path="scale", frame=cf + step_frames//2)
                except Exception:
                    pass
                try:
                    if blackbody is not None:
                        blackbody.inputs['Temperature'].default_value = max(3000.0, (blackbody.inputs['Temperature'].default_value*0.7))
                        blackbody.inputs['Temperature'].keyframe_insert(data_path='default_value', frame=cf + step_frames//2)
                except Exception:
                    pass
            elif 'core' in stage or 'collapse' in stage or 'supernova' in stage:
                try:
                    emiss.inputs['Strength'].default_value = 30.0
                    emiss.inputs['Strength'].keyframe_insert(data_path='default_value', frame=cf + step_frames//2)
                except Exception:
                    pass
                try:
                    emitter, p_obj = add_supernova_particles(obj, burst_frame=cf + step_frames//2)
                    emitter.parent = obj
                    emitter.location = obj.location
                except Exception:
                    pass
            elif 'white' in stage:
                try:
                    obj.scale = (radius*0.6, radius*0.6, radius*0.6)
                    obj.keyframe_insert(data_path="scale", frame=cf + step_frames)
                except Exception:
                    pass
            elif 'neutron' in stage:
                try:
                    obj.scale = (radius*0.15, radius*0.15, radius*0.15)
                    obj.keyframe_insert(data_path="scale", frame=cf + step_frames)
                except Exception:
                    pass
            elif 'black' in stage:
                try:
                    obj.scale = (radius*0.02, radius*0.02, radius*0.02)
                    obj.keyframe_insert(data_path="scale", frame=cf + step_frames)
                except Exception:
                    pass
            cf += step_frames
    else:
        m = safe_float(mass_est, 1.0)
        try:
            obj.scale = (radius, radius, radius)
            obj.keyframe_insert(data_path="scale", frame=FRAME_MAIN)
        except Exception:
            pass
        if m < 8:
            try:
                obj.scale = (radius*4.0, radius*4.0, radius*4.0)
                obj.keyframe_insert(data_path="scale", frame=FRAME_RED)
                obj.scale = (radius*0.6, radius*0.6, radius*0.6)
                obj.keyframe_insert(data_path="scale", frame=FRAME_REMNANT)
            except Exception:
                pass
        elif m < 20:
            try:
                obj.scale = (radius*5.0, radius*5.0, radius*5.0)
                obj.keyframe_insert(data_path="scale", frame=FRAME_RED)
            except Exception:
                pass
            try:
                emiss.inputs['Strength'].default_value = 18.0
                emiss.inputs['Strength'].keyframe_insert(data_path='default_value', frame=FRAME_COLLAPSE)
            except Exception:
                pass
            try:
                emitter, p_obj = add_supernova_particles(obj, burst_frame=FRAME_COLLAPSE)
                emitter.parent = obj
                emitter.location = obj.location
            except Exception:
                pass
            try:
                obj.scale = (radius*0.15, radius*0.15, radius*0.15)
                obj.keyframe_insert(data_path="scale", frame=FRAME_REMNANT)
            except Exception:
                pass
        else:
            try:
                obj.scale = (radius*6.0, radius*6.0, radius*6.0)
                obj.keyframe_insert(data_path="scale", frame=FRAME_RED)
            except Exception:
                pass
            try:
                emiss.inputs['Strength'].default_value = 30.0
                emiss.inputs['Strength'].keyframe_insert(data_path='default_value', frame=FRAME_COLLAPSE)
            except Exception:
                pass
            try:
                emitter, p_obj = add_supernova_particles(obj, burst_frame=FRAME_COLLAPSE)
                emitter.parent = obj
                emitter.location = obj.location
            except Exception:
                pass
            try:
                obj.scale = (radius*0.02, radius*0.02, radius*0.02)
                obj.keyframe_insert(data_path="scale", frame=FRAME_REMNANT)
            except Exception:
                pass

    return obj

# create stars
for i,row in enumerate(data):
    if i >= n_stars:
        break
    if use_sim:
        timeline = row.get('timeline', [])
        first = timeline[0] if timeline else {}
        mass = first.get('mass', 1.0)
        teff = first.get('teff', 5500)
        create_star(i, mass, teff, timeline=timeline)
    else:
        mass = row.get('mass_est') or row.get('mass_solar') or row.get('mass') or 1.0
        teff = row.get('teff') or row.get('teff_gspphot') or 5500
        create_star(i, mass, teff)

# parent and rotate
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
print("Saved", out_blend)

