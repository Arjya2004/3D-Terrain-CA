"""
R2 - STATE-AWARE THERMAL (GRADIENT) EROSION

A cell that stands too steeply above its lowest neighbour loses material.
Each state has its own stability limit and its own resistance.

Only SOIL, SLOPE, ROCK, PLATEAU, PEAK erode. For each such cell:

    D_max  = largest drop to a lower Moore neighbour (steepest direction)
    T      = R2_TALUS * factor(state)             stability limit of the state
    excess = D_max - T                            nothing happens if excess <= 0

    amount = excess * erosion_strength * resistance(state)
    amount = min(amount, max_move, h - 0.1)

    h(cell)  -= amount          the solid terrain gets lower
    sed(cell) += amount         the material becomes loose sediment (same cell)

    SOIL / SLOPE cell with  amount / max(h, 1) >= 0.08   ->  SEDIMENT
"""
import numpy as np
from ca_core import SOIL, SLOPE, SEDIMENT, lower_neighbours, interior_cells, state_counts_text
import config as cfg


def r2_step(height, state, sediment):
    """One synchronous R2 iteration. Returns new (height, state, sediment)."""
    rows, cols = height.shape
    height_change = np.zeros(height.shape, dtype=np.float32)
    sediment_change = np.zeros(height.shape, dtype=np.float32)
    new_state = state.copy()
    active_cells = 0
    eroded_total = 0.0

    for r, c in interior_cells(rows, cols):
        s = int(state[r, c])
        if s not in cfg.R2_RESISTANCE:           # EMPTY, WATER, SEDIMENT do not erode
            continue

        current_height = float(height[r, c])
        downhill = lower_neighbours(height, r, c)
        if not downhill:
            continue

        steepest_drop = max(downhill, key=lambda x: x[2])[2]
        limit = cfg.R2_TALUS * cfg.R2_THRESHOLD_FACTOR[s]
        excess = steepest_drop - limit
        if excess <= 0:
            continue
        active_cells += 1

        amount = excess * cfg.R2_EROSION_STRENGTH * cfg.R2_RESISTANCE[s]
        amount = min(amount, cfg.R2_MAX_MOVE)
        amount = min(amount, max(0.0, current_height - cfg.R2_MIN_HEIGHT))
        if amount <= 0:
            continue

        height_change[r, c] -= amount
        sediment_change[r, c] += amount
        eroded_total += amount

        if s in (SOIL, SLOPE) and amount / max(current_height, 1.0) >= cfg.R2_SEDIMENT_RATIO:
            new_state[r, c] = SEDIMENT

    return height + height_change, new_state, sediment + sediment_change, active_cells, eroded_total


def run_r2(height_grid, state_grid, iterations):
    height = height_grid.astype(np.float32).copy()
    state = state_grid.astype(np.uint8).copy()
    sediment = np.zeros(height.shape, dtype=np.float32)

    print("\nR2 - THERMAL EROSION")
    for i in range(1, iterations + 1):
        height, state, sediment, active, eroded = r2_step(height, state, sediment)
        print(f"  R2 iteration {i:3d} | active cells: {active:5d} | eroded: {eroded:10.4f}")
    print("  states:", state_counts_text(state))
    return height, state, sediment
