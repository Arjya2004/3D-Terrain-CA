"""
shapes.py - STEP 2: turn the 2D vertical profile into a 3D shape, then into a
HEIGHTMAP (the height of the shape above every ground cell).

Profile: profile[z, x] = 1 means "solid" at generation z (height) and position x.

Three methods (the three files rotation.py, extension.py, hybridstack.py):

  rotation   spin the profile around its centre line -> a solid of revolution
             (mountain / cone / volcano shapes). Heightmap is size x size.
  extension  push the profile straight sideways by `depth` cells -> a ridge or
             canyon wall. Heightmap is (columns x depth).
  hybrid     stack `depth` copies of the profile; each next copy is wider by
             up to `max_expand` cells on each side -> a widening ridge.

heightmap(x, y) = number of solid voxels in the column above (x, y).
"""
import numpy as np


def rotation(profile):
    """Rotational sweep (solid disk at every generation)."""
    rows, cols = profile.shape
    radius = cols // 2
    size = radius * 2 + 1
    axis = cols // 2

    # distance of every ground cell from the rotation axis
    i, j = np.indices((size, size))
    distance = np.sqrt((i - radius) ** 2 + (j - radius) ** 2)

    heightmap = np.zeros((size, size), dtype=np.int64)
    positions = np.abs(np.arange(cols) - axis)          # distance of each profile column from the axis
    for z in range(rows):
        active = profile[z] != 0
        if not active.any():
            continue
        reach = positions[active].max()                 # widest active cell sets the disk radius
        heightmap += (distance <= reach)                # +1 height inside the disk
    return heightmap


def extension(profile, depth):
    """Extrusion: every profile column is copied `depth` times sideways."""
    column_height = (profile == 1).sum(axis=0)           # solid cells in each column
    return np.tile(column_height[:, None], (1, depth)).astype(np.int64)


def hybrid_stacking(profile, depth=20, max_expand=8):
    """Stack `depth` profiles; the y-th copy is expanded by up to `max_expand` cells."""
    rows, cols = profile.shape
    new_cols = cols + 2 * max_expand
    voxels = np.zeros((new_cols, depth, rows), dtype=bool)

    for y in range(depth):
        expand = int(max_expand * y / (depth - 1)) if depth > 1 else 0
        for z in range(rows):
            active = np.where(profile[z] == 1)[0]
            if len(active) == 0:
                continue
            left = max(active.min() - expand + max_expand, 0)
            right = min(active.max() + expand + max_expand, new_cols - 1)
            voxels[left:right + 1, y, z] = True
    return voxels.sum(axis=2)
