# Blender script — run inside Blender: blender --background --python src/blender_export.py -- data/processed/simulations.json
import sys, json
argv = sys.argv
if '--' in argv: argv = argv[argv.index('--')+1:]
else: argv = []
simfile = argv[0] if argv else 'data/processed/simulations.json'

import bpy
from mathutils import Vector

with open(simfile) as f:
    sims = json.load(f)

bpy.ops.wm.read_factory_settings(use_empty=True)

x = 0.0
for s in sims[:10]:
    timeline = s['timeline']
    y = 0.0
    for stage in timeline:
        radius = max(0.1, (stage.get('mass',1.0))**0.33/2.0)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(x, y, 0))
        obj = bpy.context.active_object
        mat = bpy.data.materials.new(name=f"Mat_{s['source_id']}_{int(y)}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes['Principled BSDF']
        st = stage['stage']
        if 'white_dwarf' in st:
            color = (1.0,1.0,1.0,1)
        elif 'red' in st or 'giant' in st:
            color = (1.0,0.2,0.1,1)
        elif 'supergiant' in st or 'supernova' in st:
            color = (1.0,0.8,0.2,1)
        else:
            color = (0.7,0.8,1.0,1)
        bsdf.inputs['Base Color'].default_value = color
        obj.data.materials.append(mat)
        y += radius*3.0
    x += 4.0

bpy.ops.wm.save_mainfile(filepath='visualizations/sample_stars.blend')
print('Saved visualizations/sample_stars.blend')
