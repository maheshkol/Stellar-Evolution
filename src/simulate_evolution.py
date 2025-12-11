import pandas as pd
import json
from pathlib import Path
import os

os.makedirs('data/processed', exist_ok=True)

def simulate_one(row):
    m = float(row['mass_solar']); t = float(row['teff'])
    timeline = [{'stage':'main_sequence','mass':m,'teff':t,'notes':'hydrogen burning'}]
    if m < 0.8:
        timeline.append({'stage':'red_giant','mass':m*0.98,'teff':t*0.6})
        timeline.append({'stage':'white_dwarf','mass':max(0.5,m*0.6),'teff':10000})
        end = 'white_dwarf'
    elif m < 8:
        timeline.append({'stage':'red_giant','mass':m*0.95,'teff':t*0.5})
        timeline.append({'stage':'planetary_nebula','mass':m*0.6,'teff':15000})
        timeline.append({'stage':'white_dwarf','mass':0.6*m,'teff':8000})
        end = 'white_dwarf'
    else:
        timeline.append({'stage':'supergiant','mass':m*0.9,'teff':t*0.8})
        if m >= 20:
            timeline.append({'stage':'core_collapse','mass':m*0.5,'teff':1e6,'notes':'likely black hole'})
            end = 'black_hole'
        else:
            timeline.append({'stage':'core_collapse','mass':m*0.7,'teff':1e6,'notes':'likely neutron star'})
            end = 'neutron_star'
    return {'source_id':int(row['source_id']), 'timeline':timeline, 'end_state': end}

def simulate_all(infile='data/processed/processed_stars.csv', outfile='data/processed/simulations.json'):
    df = pd.read_csv(infile)
    sims = [simulate_one(row) for _, row in df.iterrows()]
    Path(outfile).write_text(json.dumps(sims, indent=2))
    print(f'Wrote {outfile}')
    return sims

if __name__ == '__main__':
    simulate_all()
