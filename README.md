# 3D Terrain CA (TerrCA-Evo)

A Cellular Automata-based framework for procedural three-dimensional terrain generation and evolution.

The framework generates terrain from a one-dimensional Cellular Automaton (CA) profile, transforms it into a heightmap, applies Voronoi-based variation, places the terrain on a destination grid, and evolves it using an eight-state Cellular Automaton.

## Requirements

- Python 3
- NumPy
- SciPy
- Matplotlib (optional; for preview images)
- PyVista (for 3D voxel visualization)
- Tkinter (for the viewer's file-selection dialog; included with most standard Windows Python installations)

## Installation

From the project root, install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Workflow

Run the following commands from the project directory containing `generate_heightmap.py`.

### 1. Generate a heightmap

```bash
python generate_heightmap.py
```

This script:

- Generates a vertical profile using a one-dimensional Cellular Automaton.
- Constructs terrain using rotation, extension, or hybrid stacking.
- Applies optional Voronoi-based height variation.
- Saves the generated heightmap in `HEIGHTMAP_FOLDER/`.

Follow the interactive prompts. Press Enter to accept the displayed default values.

**Parameter Guidelines:**

- **Number of cells:** Determines the width of the one-dimensional configuration.
- **Number of iterations (generations):** Increasing the iteration count extends the vertical profile, as more generations are produced.
- **Region size:** Determines how cells are divided into regions. For a single region, set the region size equal to the total number of cells. For multiple regions, use a smaller region size that divides the total cell count evenly.

For a single-region configuration, use the same value for the total number of cells and the region size.

**Recommended Settings for Terrain Evolution:** Since the terrain undergoes erosion and sediment transport during the R1–R5 stages, a slightly taller initial profile can provide more scope for observing these processes. Consider using more than 10 generations when generating the vertical profile, then adjust the iteration count based on the desired terrain features. The final morphology depends on the initial profile and the evolution parameters.

### 2. Place the terrain

```bash
python placement_engine.py
```

This script places the selected heightmap on a destination grid. The configurable options include:

- Terrain grid size
- Ground height
- Input heightmap
- Centre coordinates

Type `Q` at the heightmap-selection prompt to finish placement.

The combined terrain is saved to:

```text
OUTPUT/height_grid.npy
```

### 3. Run the eight-state Cellular Automaton

```bash
python run_pipeline.py
```

Enter the desired iteration count, or press Enter to use the configured default. To specify the count directly, run:

```bash
python run_pipeline.py 40
```

The model uses eight terrain states:

- `EMPTY`
- `WATER`
- `SEDIMENT`
- `SOIL`
- `SLOPE`
- `ROCK`
- `PLATEAU`
- `PEAK`

The five operators execute sequentially:

| Operator | Function |
|---|---|
| R1 | Boundary blending |
| R2 | Thermal erosion |
| R3 | Sediment transport and deposition |
| R4 | Hydraulic erosion |
| R5 | Final state and material update |

The specified iteration count applies to each operator individually, not to complete R1–R5 cycles.

The final terrain is saved to:

```text
OUTPUT/final_height_grid.npy
```

### 4. Visualize the terrain

```bash
python voxel_viewer.py
```

Select the NumPy heightmap you want to visualize, for example:

```text
OUTPUT/height_grid.npy
OUTPUT/final_height_grid.npy
```

The viewer displays the selected terrain as a three-dimensional voxel model.

## Project Structure

| File or directory | Purpose |
|---|---|
| `generate_heightmap.py` | Interactive terrain generation |
| `generator/profile_ca.py` | One-dimensional CA profile generation |
| `generator/shapes.py` | Rotation, extension, and hybrid stacking |
| `generator/voronoi.py` | Voronoi-based terrain variation |
| `placement_engine.py` | Terrain placement |
| `ca_core.py` | Shared CA states and functions |
| `initial_states.py` | Initial terrain-state assignment |
| `r1_blending.py` | Boundary blending |
| `r2_thermal_erosion.py` | Thermal erosion |
| `r3_sediment_transport.py` | Sediment transport and deposition |
| `r4_hydraulic_erosion.py` | Hydraulic erosion |
| `r5_state_coupling.py` | Final state and material update |
| `config.py` | CA configuration and parameters |
| `run_pipeline.py` | Executes the R1–R5 pipeline |
| `voxel_viewer.py` | Three-dimensional terrain visualization |
| `HEIGHTMAP_FOLDER/` | Example and generated heightmaps |
| `GENERATED/` | Cached profiles and preview images |
| `OUTPUT/` | Placed and evolved terrain arrays |

## Outputs

| Output | Description |
|---|---|
| `GENERATED/vertical_profile.npy` | Cached one-dimensional CA profile |
| `OUTPUT/height_grid.npy` | Terrain after placement |
| `OUTPUT/final_height_grid.npy` | Terrain after CA evolution |

Output arrays use NumPy's `.npy` format. Subsequent runs may overwrite existing output files, so copy any results you want to preserve.

## Reproducibility

For reproducible experiments, record the CA rule, profile dimensions, generation count, initial configuration, construction method, Voronoi parameters, placement settings, and iteration count. Preserve the input and output arrays associated with reported experimental results.

## Code Availability

Source code: [3D-Terrain-CA](https://github.com/Arjya2004/3D-Terrain-CA)
