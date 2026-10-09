"""
R1 - BOUNDARY BLENDING

Where two different states touch, the placed terrain has a hard step.
R1 smooths those steps and remembers how long a cell has been on a boundary.

For every interior cell:

    u = number of Moore neighbours whose state differs from the cell's state
    if u == 0: nothing happens
    I = u / 8                                   boundary influence (0.125 ... 1.0)

    transition = min(1, transition + 0.20 * I)  grows with exposure

    for every LOWER neighbour (drop D = h - h_n > 0):
        amount = 0.15 * I * D / 8               mass-conserving exchange
        h(cell) -= amount ;  h(neighbour) += amount

    SOIL cell with transition >= 0.60           ->  SLOPE
    EMPTY floor raised above base + 0.05        ->  SOIL
"""
import numpy as np
from ca_core import (EMPTY, SOIL, SLOPE, interior_cells, neighbours,
                     state_counts_text)
import config as cfg


def r1_step(height, state, transition, base_height):
    """One synchronous R1 iteration. Returns new (height, state, transition)."""
    rows, cols = height.shape
    new_height = height.copy()
    new_state = state.copy()
    new_transition = transition.copy()
    boundary_cells = 0

    for r, c in interior_cells(rows, cols):
        current_state = int(state[r, c])
        around = neighbours(r, c)

        unlike = sum(1 for nr, nc in around if state[nr, nc] != current_state)
        if unlike == 0:
            continue
        boundary_cells += 1

        influence = unlike / 8.0
        new_transition[r, c] = min(
            1.0, transition[r, c] + cfg.R1_TRANSITION_GAIN * influence)

        # height exchange with every lower neighbour (volume is conserved)
        for nr, nc in around:
            drop = height[r, c] - height[nr, nc]
            if drop <= 0:
                continue
            amount = cfg.R1_EXCHANGE_RATE * influence * drop / 8.0
            new_height[r, c] -= amount
            new_height[nr, nc] += amount

        if current_state == SOIL and new_transition[r, c] >= cfg.R1_SOIL_TO_SLOPE:
            new_state[r, c] = SLOPE

    # empty floor that received material is no longer empty
    gained = (state == EMPTY) & (new_height > base_height + cfg.R1_EMPTY_GAIN)
    new_state[gained] = SOIL
    return new_height, new_state, new_transition, boundary_cells


def run_r1(height_grid, state_grid, iterations):
    height = height_grid.astype(np.float32).copy()
    state = state_grid.astype(np.uint8).copy()
    transition = np.zeros(height.shape, dtype=np.float32)
    base_height = float(np.min(height))

    print("\nR1 - BOUNDARY BLENDING")
    for i in range(1, iterations + 1):
        height, state, transition, boundary = r1_step(height, state, transition, base_height)
        print(f"  R1 iteration {i:3d} | boundary cells: {boundary:5d}")
    print("  states:", state_counts_text(state))
    return height, state
