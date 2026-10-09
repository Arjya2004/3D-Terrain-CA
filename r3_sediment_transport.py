"""
R3 - SEDIMENT TRANSPORT AND DEPOSITION

The loose sediment made by R2 flows downhill and settles in traps.

PASS 1 - transport.  For every cell with sediment S > 0:
    downhill = neighbours lower by MORE than 0.2
    movable  = 0.6 * S
    each downhill neighbour gets  movable * drop / (sum of all drops)
    (the outer ring is cleared afterwards: open boundary)

PASS 2 - deposition.  For every cell with S > 0 and NO downhill neighbour:
    deposit = min(0.35 * S, 0.5)
    sed(cell) -= deposit ;  h(cell) += deposit
    state -> SEDIMENT   if the state is EMPTY, WATER, SOIL, SLOPE or SEDIMENT
                        (ROCK / PLATEAU / PEAK keep their state)
"""
import numpy as np
from ca_core import (EMPTY, WATER, SEDIMENT, SOIL, SLOPE, lower_neighbours,
                     interior_cells, clear_border, state_counts_text)
import config as cfg

BURIED_BY_SEDIMENT = (EMPTY, WATER, SOIL, SLOPE, SEDIMENT)


def r3_step(height, state, sediment):
    rows, cols = height.shape
    new_state = state.copy()

    # ---- PASS 1: transport -------------------------------------------
    sediment_change = np.zeros(height.shape, dtype=np.float32)
    transported = 0.0
    for r, c in interior_cells(rows, cols):
        available = float(sediment[r, c])
        if available <= 0:
            continue
        downhill = lower_neighbours(height, r, c, cfg.R3_TRANSPORT_THRESHOLD)
        if not downhill:
            continue
        downhill.sort(key=lambda x: x[2], reverse=True)       # steepest first
        movable = min(available * cfg.R3_TRANSPORT_RATE, available)
        if movable <= 0:
            continue
        total_drop = sum(drop for _, _, drop in downhill)
        if total_drop <= 0:
            continue
        for nr, nc, drop in downhill:
            amount = movable * (drop / total_drop)
            if amount <= 0:
                continue
            sediment_change[r, c] -= amount
            sediment_change[nr, nc] += amount
            transported += amount
    sediment = sediment + sediment_change
    clear_border(sediment)

    # ---- PASS 2: deposition ------------------------------------------
    sediment_change = np.zeros(height.shape, dtype=np.float32)
    height_change = np.zeros(height.shape, dtype=np.float32)
    deposited = 0.0
    for r, c in interior_cells(rows, cols):
        available = float(sediment[r, c])
        if available <= 0:
            continue
        if lower_neighbours(height, r, c, cfg.R3_TRANSPORT_THRESHOLD):
            continue                                           # sediment can still flow
        deposit = min(available * cfg.R3_DEPOSITION_RATE, cfg.R3_MAX_DEPOSIT)
        if deposit <= 0:
            continue
        sediment_change[r, c] -= deposit
        height_change[r, c] += deposit
        deposited += deposit
        if int(state[r, c]) in BURIED_BY_SEDIMENT:
            new_state[r, c] = SEDIMENT
    sediment = sediment + sediment_change
    height = height + height_change
    return height, new_state, sediment, transported, deposited


def run_r3(height_grid, state_grid, sediment_grid, iterations):
    height = height_grid.astype(np.float32).copy()
    state = state_grid.astype(np.uint8).copy()
    sediment = sediment_grid.astype(np.float32).copy()

    print("\nR3 - SEDIMENT TRANSPORT AND DEPOSITION")
    for i in range(1, iterations + 1):
        height, state, sediment, moved, settled = r3_step(height, state, sediment)
        print(f"  R3 iteration {i:3d} | transported: {moved:11.2f} | deposited: {settled:9.4f}")
    print("  states:", state_counts_text(state))
    return height, state, sediment
