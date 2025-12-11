# Stellar Evolution Predictor and Visualizer

## Overview
Predict life cycle endpoints for stars and visualize evolution stages. This project is a scaffold for: data ingestion (Gaia/SDSS), preprocessing, simple evolutionary simulation, ML prediction, and Blender visualizations. Based on provided project brief. :contentReference[oaicite:1]{index=1}

## Quickstart
1. Create virtualenv and install requirements:
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt

2. Create toy data:
   python example_toy_data.py

3. Process data:
   python src/process_data.py

4. Simulate evolution:
   python src/simulate_evolution.py

5. Train models:
   python src/train_model.py
   python src/classifier_rf.py

6. Visualize (2D):
   python quick_visual.py

7. Blender visualization (requires Blender installed):
   blender --background --python src/blender_export.py -- data/processed/simulations.json

## Data
- For real science, download Gaia DR3 and SDSS data and place CSVs in `data/raw/`.

