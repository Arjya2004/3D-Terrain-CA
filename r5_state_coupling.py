"""
R5 - FINAL STATE-AWARE MATERIAL COUPLING

Every iteration = (A) a small material pass, then (B) a state transition.

Normalised quantities (recomputed every iteration):
    slope_hat = min(slope / P95(slope), 1)        P95 = 95th percentile of non-zero slopes
    h_hat     = (h - h_min) / (h_max - h_min)

(A) MATERIAL PASS (all sub-passes read the grids from the start of the iteration)
    erosion    SOIL / SLOPE cell with slope_hat > 0.45:
                   e = (slope_hat - 0.45) * rate    rate: SOIL 0.025, SLOPE 0.040
                   e = min(e, 0.12, h - 0.01) ; h -= e ; sed += e
    transport  SLOPE / SEDIMENT cell sends  min(0.18 * sed, 0.05 + 0.02 * dh)
               to its single LOWEST neighbour   (dh = height difference)
    deposition cell with slope_hat < 0.45:
                   flatness = (0.45 - slope_hat) / 0.45
                   d = sed * 0.25 * flatness ; h += d ; sed -= d

(B) STATE TRANSITION (synchronous, see next_state() below)

After the last iteration the remaining sediment settles:  h = h + sed.
"""
import numpy as np
from ca_core import (EMPTY, WATER, SEDIMENT, SOIL, SLOPE, ROCK, PLATEAU, PEAK,
                     STATE_NAMES, neighbours, interior_cells, clear_border,
                     state_counts_text)
import config as cfg


# ----------------------------------------------------------------------
# normalised slope / height
# ----------------------------------------------------------------------
def normalised_slope(height):
    gy, gx = np.gradient(height)
    slope = np.sqrt(gx * gx + gy * gy)
    terrain = slope[height > 0]
    if len(terrain) == 0:
        return slope, np.zeros_like(slope)
    sloping = terrain[terrain > 0]
    if len(sloping) == 0:
        return slope, np.zeros_like(slope)
    p95 = np.percentile(sloping, 95)
    if p95 <= 0:
        return slope, np.zeros_like(slope)
    return slope, np.minimum(slope / p95, 1.0)


def normalised_height(height):
    terrain = height[height > 0]
    if len(terrain) == 0:
        return np.zeros_like(height)
    h_min, h_max = np.min(terrain), np.max(terrain)
    if h_max == h_min:
        return np.zeros_like(height)
    return (height - h_min) / (h_max - h_min)


def lowest_neighbour(height, r, c):
    """The neighbour with the lowest height, if it is lower than the cell."""
    best, best_height = None, float(height[r, c])
    for nr, nc in neighbours(r, c):
        h = float(height[nr, nc])
        if h < best_height:
            best, best_height = (nr, nc), h
    return best


# ----------------------------------------------------------------------
# (A) material pass
# ----------------------------------------------------------------------
def material_pass(height, state, sediment):
    rows, cols = height.shape
    _, slope_hat = normalised_slope(height)

    new_height = height.copy()
    new_sediment = sediment.copy()
    erosion_grid = np.zeros(height.shape, dtype=np.float32)
    deposition_grid = np.zeros(height.shape, dtype=np.float32)
    transport_grid = np.zeros(height.shape, dtype=np.float32)

    # erosion
    for r, c in interior_cells(rows, cols):
        s = int(state[r, c])
        erosion = 0.0
        if s in (SOIL, SLOPE) and slope_hat[r, c] > cfg.R5_SLOPE_THRESHOLD:
            rate = cfg.R5_SOIL_EROSION_RATE if s == SOIL else cfg.R5_SLOPE_EROSION_RATE
            erosion = (float(slope_hat[r, c]) - cfg.R5_SLOPE_THRESHOLD) * rate
        erosion = min(erosion, cfg.R5_MAX_EROSION)
        erosion = min(erosion, max(0.0, float(height[r, c]) - cfg.R5_MIN_HEIGHT))
        if erosion > 0:
            erosion_grid[r, c] = erosion
            new_height[r, c] -= erosion
            new_sediment[r, c] += erosion

    # transport to the lowest neighbour
    for r, c in interior_cells(rows, cols):
        amount = float(new_sediment[r, c])
        if amount <= 0 or int(state[r, c]) not in (SLOPE, SEDIMENT):
            continue
        target = lowest_neighbour(height, r, c)
        if target is None:
            continue
        nr, nc = target
        dh = float(height[r, c]) - float(height[nr, nc])
        if dh <= 0:
            continue
        moved = min(amount * cfg.R5_TRANSPORT_RATE, 0.05 + dh * 0.02)
        moved = min(moved, amount)
        if moved <= 0:
            continue
        new_sediment[r, c] -= moved
        transport_grid[nr, nc] += moved
    new_sediment += transport_grid
    clear_border(new_sediment)

    # deposition (stronger on flatter ground)
    for r, c in interior_cells(rows, cols):
        amount = float(new_sediment[r, c])
        if amount <= 0:
            continue
        gentle = float(slope_hat[r, c])
        if gentle < cfg.R5_SLOPE_THRESHOLD:
            flatness = (cfg.R5_SLOPE_THRESHOLD - gentle) / cfg.R5_SLOPE_THRESHOLD
            deposit = min(amount * cfg.R5_DEPOSITION_RATE * flatness, amount)
            if deposit > 0:
                new_height[r, c] += deposit
                new_sediment[r, c] -= deposit
                deposition_grid[r, c] = deposit

    new_height = np.maximum(new_height, cfg.R5_MIN_HEIGHT)
    new_sediment = np.maximum(new_sediment, 0.0)
    return new_height, new_sediment, slope_hat, erosion_grid, deposition_grid


# ----------------------------------------------------------------------
# (B) state transition
# ----------------------------------------------------------------------
def next_state(current, h_hat, s_hat, sed, erosion, deposition, sediment_neighbours):
    """The 8-state transition table. Rules are checked in the order written."""
    if current == SOIL:
        if s_hat >= cfg.R5_SLOPE_THRESHOLD:
            return SLOPE
        if h_hat >= 0.55 and s_hat < cfg.R5_PLATEAU_THRESHOLD:
            return PLATEAU

    elif current == SLOPE:
        if erosion >= 0.005 and sed >= cfg.R5_SEDIMENT_ACTIVATION:
            return SEDIMENT                                   # eroding and loaded
        if sediment_neighbours >= 2 and sed >= 0.015:
            return SEDIMENT                                   # inside a sediment zone
        if h_hat >= cfg.R5_PEAK_THRESHOLD and s_hat >= cfg.R5_STEEP_THRESHOLD:
            return ROCK
        if h_hat >= 0.55 and s_hat < cfg.R5_PLATEAU_THRESHOLD:
            return PLATEAU
        if s_hat < 0.35 and sed < cfg.R5_SEDIMENT_CLEAR:
            return SOIL

    elif current == SEDIMENT:
        if sed <= cfg.R5_SEDIMENT_CLEAR and s_hat < cfg.R5_SLOPE_THRESHOLD:
            return SOIL                                       # stable deposit
        if deposition > 0 and sed < cfg.R5_SEDIMENT_ACTIVATION:
            return SOIL                                       # being used up
        if sed >= cfg.R5_SEDIMENT_ACTIVATION:
            return SEDIMENT                                   # still active
        if s_hat < 0.35:
            return SOIL                                       # weak sediment, gentle ground

    elif current == ROCK:
        if h_hat >= cfg.R5_PEAK_THRESHOLD:
            return PEAK
        if s_hat < cfg.R5_PLATEAU_THRESHOLD and h_hat >= 0.55:
            return PLATEAU

    elif current == PLATEAU:
        if h_hat >= cfg.R5_PEAK_THRESHOLD:
            return PEAK
        if s_hat >= cfg.R5_STEEP_THRESHOLD:
            return ROCK

    elif current == PEAK:
        if h_hat < 0.70:
            return PLATEAU

    elif current == EMPTY:
        if sed >= cfg.R5_SEDIMENT_ACTIVATION:
            return SEDIMENT
        if h_hat > 0.02:
            return SOIL

    return current


def neighbour_state_rule(state, r, c, current):
    """Game-of-Life style smoothing.

    A cell that has NO neighbour in its own state, while at least 5 of its 8
    neighbours share another terrain state, joins that state.
    """
    counts = {}
    for nr, nc in neighbours(r, c):
        s = int(state[nr, nc])
        counts[s] = counts.get(s, 0) + 1
    if counts.get(current, 0) != 0:
        return current
    majority = max(counts, key=counts.get)
    if counts[majority] >= 5 and majority not in (EMPTY, WATER):
        return majority
    return current


def state_transition(height, state, sediment, slope_hat, erosion_grid, deposition_grid, transitions):
    rows, cols = height.shape
    h_hat = normalised_height(height)
    new_state = state.copy()
    changes = 0

    for r, c in interior_cells(rows, cols):
        current = int(state[r, c])
        sediment_neighbours = sum(1 for nr, nc in neighbours(r, c) if state[nr, nc] == SEDIMENT)

        new = next_state(current, float(h_hat[r, c]), float(slope_hat[r, c]),
                         float(sediment[r, c]), float(erosion_grid[r, c]),
                         float(deposition_grid[r, c]), sediment_neighbours)

        if new == current and current not in (EMPTY, WATER):
            new = neighbour_state_rule(state, r, c, current)

        if new != current:
            new_state[r, c] = new
            changes += 1
            key = (STATE_NAMES[current], STATE_NAMES[new])
            transitions[key] = transitions.get(key, 0) + 1
    return new_state, changes


# ----------------------------------------------------------------------
def run_r5(height_grid, state_grid, sediment_grid, iterations):
    height = height_grid.astype(np.float32).copy()
    state = state_grid.astype(np.uint8).copy()
    sediment = sediment_grid.astype(np.float32).copy()
    transitions = {}

    print("\nR5 - FINAL STATE COUPLING")
    for i in range(1, iterations + 1):
        height, sediment, slope_hat, erosion, deposition = material_pass(height, state, sediment)
        state, changes = state_transition(height, state, sediment, slope_hat,
                                          erosion, deposition, transitions)
        print(f"  R5 iteration {i:3d} | erosion: {erosion.sum():8.4f} | "
              f"deposition: {deposition.sum():9.4f} | sediment: {sediment.sum():9.4f} | "
              f"state changes: {changes}")

    height = height + sediment            # leftover sediment settles into the terrain
    print("  states:", state_counts_text(state))
    print("  state transitions:")
    for (old, new), n in sorted(transitions.items()):
        print(f"    {old:9s} -> {new:9s} : {n}")
    return height, state, sediment
