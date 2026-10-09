"""
voronoi.py - STEP 3 (was rotationV.py): Voronoi variation.

Makes the smooth shape irregular, like natural terrain.

  1. Drop `points` random seed points on the map; each seed gets a random value in [-1, 1].
  2. Every cell takes the value of its NEAREST seed (a Voronoi diagram of flat patches).
  3. Blur the patches slightly (Gaussian filter, sigma = 1) -> `variation` in [-1, 1].
  4. New height = old height * (1 + strength * variation), never below 0.

The three numbers you can vary: SEED (which random pattern), POINTS (how many
patches, more = finer detail), STRENGTH (how strongly the pattern changes the height).
"""
import numpy as np
from scipy.ndimage import gaussian_filter


def voronoi_field(rows, cols, points, seed):
    rng = np.random.default_rng(seed)
    seeds = rng.integers(0, [rows, cols], size=(points, 2))
    values = rng.uniform(-1, 1, points)

    y, x = np.indices((rows, cols))
    field = np.zeros((rows, cols))
    best = np.full((rows, cols), np.inf)             # squared distance to the nearest seed so far

    for (sy, sx), value in zip(seeds, values):
        d = (y - sy) ** 2 + (x - sx) ** 2
        closer = d < best
        best[closer] = d[closer]
        field[closer] = value
    return gaussian_filter(field, sigma=1)


def apply_voronoi(heightmap, seed, points, strength):
    rows, cols = heightmap.shape
    variation = voronoi_field(rows, cols, points, seed)
    modified = heightmap * (1 + strength * variation)
    return np.maximum(modified, 0)
