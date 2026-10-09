import tkinter as tk
from tkinter import filedialog

import numpy as np
import pyvista as pv

# ============================================================
# CA TERRAIN VOXEL VIEWER
# VERSION 2
# ============================================================

print("="*60)
print("CA TERRAIN VOXEL VIEWER")
print("="*60)

# ------------------------------------------------------------
# Select Heightmap
# ------------------------------------------------------------

root = tk.Tk()
root.withdraw()

filename = filedialog.askopenfilename(

    title="Select Heightmap",

    filetypes=[
        ("NumPy Heightmap","*.npy")
    ]

)

if filename == "":

    print("No file selected.")
    quit()

print("\nLoading Heightmap...")

terrain = np.load(filename)

rows, cols = terrain.shape

max_height = int(np.max(terrain))

print("Rows :",rows)
print("Columns :",cols)
print("Maximum Height :",max_height)
print("Minimum Height :",int(np.min(terrain)))
print("Average Height :",round(np.mean(terrain),2))

# ============================================================
# PARAMETERS
# ============================================================

VOXEL_SIZE = 1.0

BASE_HEIGHT = 2

SHOW_BASE = True




# ============================================================
# RECONSTRUCT VOXELS
# ============================================================

print("\nReconstructing Cellular Voxels...")

points = []
heights = []

total_voxels = 0

for x in range(rows):

    for y in range(cols):

        h = int(terrain[x, y])

        if not SHOW_BASE:
            h = max(0, h - BASE_HEIGHT)

        if h == 0:
            continue

        for z in range(h):

            points.append([

                x * VOXEL_SIZE,

                y * VOXEL_SIZE,

                z * VOXEL_SIZE

            ])

            heights.append(z)

            total_voxels += 1

points = np.array(points)

heights = np.array(heights)

print("Voxel Reconstruction Complete")

print("Total Voxels :", total_voxels)

# ============================================================
# CREATE POINT CLOUD
# ============================================================

cloud = pv.PolyData(points)

cloud["Height"] = heights




# ============================================================
# CREATE A SINGLE CUBE
# ============================================================

print("\nCreating Cube Glyph...")

cube = pv.Cube(

    center=(0, 0, 0),

    x_length=VOXEL_SIZE,

    y_length=VOXEL_SIZE,

    z_length=VOXEL_SIZE

)

# ============================================================
# CREATE GLYPHS
# ============================================================

glyphs = cloud.glyph(

    geom=cube,

    scale=False,

    orient=False

)

print("Glyphs Created.")

# ============================================================
# CREATE VIEWER
# ============================================================

plotter = pv.Plotter()

plotter.set_background("white")

plotter.show_grid()

plotter.add_axes()

# ============================================================
# ADD GLYPHS
# ============================================================

# ============================================================
# CREATE DISCRETE COLOURS
# ============================================================

print("Assigning Colours...")

cell_centers = glyphs.cell_centers().points

z_values = cell_centers[:, 2]

rgb = np.zeros((len(z_values), 3), dtype=np.uint8)

for i, z in enumerate(z_values):

    level = int(z)

    if level < BASE_HEIGHT:
        rgb[i] = [170,170,170]

    elif level <= 4:
        rgb[i] = [40,90,255]

    elif level <= 8:
        rgb[i] = [40,190,40]

    elif level <= 12:
        rgb[i] = [215,200,120]

    elif level <= 16:
        rgb[i] = [120,90,70]

    else:
        rgb[i] = [245,245,245]

glyphs["RGB"] = rgb

plotter.add_mesh(

    glyphs,

    scalars="RGB",

    rgb=True,

    show_edges=True,

    edge_color="black",

    line_width=0.3,

    ambient=0.35,

    diffuse=0.70,

    specular=0.08,

    smooth_shading=False

)

# ============================================================
# CAMERA
# ============================================================

plotter.camera_position = "iso"

plotter.camera.zoom(1.4)

plotter.add_text(

    f"Rows : {rows}\n"
    f"Columns : {cols}\n"
    f"Maximum Height : {max_height}\n"
    f"Total Voxels : {total_voxels}",

    position="upper_left",

    font_size=10

)

print("Scene Ready.")




# ============================================================
# SCREENSHOT
# ============================================================

def screenshot():

    plotter.screenshot("terrain_screenshot.png")

    print("\nScreenshot Saved")

plotter.add_key_event(

    "s",

    screenshot

)

# ============================================================
# HELP
# ============================================================

print("\n==============================================")

print("Mouse Left   : Rotate")

print("Mouse Right  : Zoom")

print("Mouse Middle : Pan")

print("S            : Save Screenshot")

print("Q            : Quit")

print("==============================================")

# ============================================================
# SHOW
# ============================================================

plotter.show(
    title="CA Terrain Viewer"
)

print("\nViewer Closed.")