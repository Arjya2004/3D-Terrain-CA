"""
initial_states.py - give every cell its first state (EMPTY ... PEAK).

The classifier uses PERCENTILES of the elevated terrain, so the thresholds
adapt to whatever heightmap was placed.

    slope = sqrt(gx^2 + gy^2)                         (np.gradient of the height)
    elevated = height > base_height                   (base_height = lowest height)

    h50, h75, h90, h97 = height percentiles of the elevated cells
    s50, s70           = slope  percentiles of the elevated cells

    SOIL     elevated, height <= h50, slope < s50
    SLOPE    elevated, h50 < height < h75, slope >= s50
    ROCK     elevated, (height >= h75 and slope >= s70) or (height >= h90 and slope >= s50)
    PLATEAU  elevated, height >= h75, slope < s50
    PEAK     elevated, height >= h97
    (any other elevated cell -> SLOPE)        flat base floor -> EMPTY

Later rules in the list overwrite earlier ones.
"""
import numpy as np
from ca_core import EMPTY, SOIL, SLOPE, ROCK, PLATEAU, PEAK


def classify_initial_states(height_grid):
    height = height_grid.astype(np.float32)
    gy, gx = np.gradient(height)
    slope = np.sqrt(gx * gx + gy * gy)

    state = np.zeros(height.shape, dtype=np.uint8)           # everything EMPTY

    terrain = height > 0
    base_height = np.min(height[terrain])
    elevated = terrain & (height > base_height)
    if not np.any(elevated):
        state[terrain] = SOIL
        return state

    h50, h75, h90, h97 = (np.percentile(height[elevated], p) for p in (50, 75, 90, 97))
    s50, s70 = (np.percentile(slope[elevated], p) for p in (50, 70))

    state[elevated & (height <= h50) & (slope < s50)] = SOIL
    state[elevated & (height > h50) & (height < h75) & (slope >= s50)] = SLOPE
    state[elevated & (((height >= h75) & (slope >= s70)) |
                      ((height >= h90) & (slope >= s50)))] = ROCK
    state[elevated & (height >= h75) & (slope < s50)] = PLATEAU
    state[elevated & (height >= h97)] = PEAK
    state[elevated & (state == EMPTY)] = SLOPE                # safety rule
    return state
