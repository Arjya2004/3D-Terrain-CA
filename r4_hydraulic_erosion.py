"""
R4 - HYDRAULIC EROSION (rain, flow, carrying capacity)

One iteration = 5 steps, in this order:

1. RAIN         every cell with h > 0 gets   w += 0.02

2. EROSION / DEPOSITION  (for every cell with water w > 0)
       drop     = largest terrain drop to a lower neighbour (0 if none)
       capacity = 0.5 * w * drop
       sediment S > capacity  ->  deposit = min((S - capacity) * 0.35, 0.5)
                                   S -= deposit, h += deposit
                                   WATER / SEDIMENT cell becomes SOIL
       sediment S < capacity  ->  erosion = (capacity - S) * 0.10 * resistance(state)
                                   erosion = min(erosion, 0.5, h - 0.1)
                                   h -= erosion, S += erosion
                                   SOIL / SLOPE with erosion > 0.05 becomes SEDIMENT

3. FLOW         water surface  W = h + w.  Neighbours with a lower surface
                receive water in proportion to the surface difference:
                    movable = 0.20 * w ;  share_i = movable * diff_i / sum(diff)
                suspended sediment moves with the water:
                    carried_i = S * share_i / w
                (the outer ring's sediment is cleared afterwards)

4. EVAPORATION  w = w * (1 - 0.10)

5. STATES       not ROCK/PLATEAU/PEAK and w >= 0.30   ->  WATER
                WATER cell with w < 0.15              ->  SEDIMENT
"""
import numpy as np
from ca_core import (WATER, SEDIMENT, SOIL, SLOPE, ROCK, PLATEAU, PEAK,
                     lower_neighbours, interior_cells, clear_border, state_counts_text)
import config as cfg


def rain(height, water):
    water = water.copy()
    water[height > 0] += cfg.R4_RAIN_AMOUNT
    return water


def erode_and_deposit(height, state, water, sediment):
    rows, cols = height.shape
    height_change = np.zeros(height.shape, dtype=np.float32)
    sediment_change = np.zeros(height.shape, dtype=np.float32)
    new_state = state.copy()
    eroded, deposited = 0.0, 0.0

    for r, c in interior_cells(rows, cols):
        w = water[r, c]
        if w <= 0:
            continue
        s = int(state[r, c])
        current_height = height[r, c]

        downhill = lower_neighbours(height, r, c)
        if downhill:
            steepest_drop = max(downhill, key=lambda x: x[2])[2]
            capacity = cfg.R4_CARRYING_CAPACITY * w * steepest_drop
        else:
            capacity = 0.0                       # nowhere to flow: sediment must settle
        load = sediment[r, c]

        if load > capacity:                      # water carries too much -> deposit
            deposit = min((load - capacity) * cfg.R4_DEPOSITION_RATE, cfg.R4_MAX_DEPOSITION)
            if deposit > 0:
                sediment_change[r, c] -= deposit
                height_change[r, c] += deposit
                deposited += deposit
                if s in (WATER, SEDIMENT):
                    new_state[r, c] = SOIL
        elif load < capacity:                    # water can carry more -> erode
            resistance = cfg.R4_RESISTANCE.get(s, 0.0)
            if resistance <= 0:
                continue
            erosion = (capacity - load) * cfg.R4_EROSION_RATE * resistance
            erosion = min(erosion, cfg.R4_MAX_EROSION)
            erosion = min(erosion, max(0.0, current_height - cfg.R4_MIN_HEIGHT))
            if erosion <= 0:
                continue
            height_change[r, c] -= erosion
            sediment_change[r, c] += erosion
            eroded += erosion
            if s in (SOIL, SLOPE) and erosion > 0.05:
                new_state[r, c] = SEDIMENT

    return height + height_change, new_state, sediment + sediment_change, eroded, deposited


def flow(height, water, sediment):
    rows, cols = height.shape
    surface = height + water
    water_change = np.zeros(water.shape, dtype=np.float32)
    carried_change = np.zeros(sediment.shape, dtype=np.float32)
    moved = 0.0

    for r, c in interior_cells(rows, cols):
        w = water[r, c]
        if w <= 0:
            continue
        lower = lower_neighbours(surface, r, c)
        if not lower:
            continue
        total_difference = sum(d for _, _, d in lower)
        if total_difference <= 0:
            continue
        movable = min(w * cfg.R4_FLOW_RATE, w)
        for nr, nc, difference in lower:
            amount = movable * (difference / total_difference)
            water_change[r, c] -= amount
            water_change[nr, nc] += amount
            carried = sediment[r, c] * amount / w
            carried_change[r, c] -= carried
            carried_change[nr, nc] += carried
            moved += amount

    water = water + water_change
    sediment = sediment + carried_change
    clear_border(sediment)
    return water, sediment, moved


def update_water_states(state, water):
    new_state = state.copy()
    holds_water = ~np.isin(state, (ROCK, PLATEAU, PEAK))
    wet = holds_water & (water >= cfg.R4_WATER_THRESHOLD)
    dried = (state == WATER) & (water < 0.5 * cfg.R4_WATER_THRESHOLD)
    new_state[wet] = WATER
    new_state[dried] = SEDIMENT
    return new_state


def run_r4(height_grid, state_grid, sediment_grid, iterations):
    height = height_grid.astype(np.float32).copy()
    state = state_grid.astype(np.uint8).copy()
    sediment = sediment_grid.astype(np.float32).copy()
    water = np.zeros(height.shape, dtype=np.float32)

    print("\nR4 - HYDRAULIC EROSION")
    for i in range(1, iterations + 1):
        water = rain(height, water)
        height, state, sediment, eroded, deposited = erode_and_deposit(height, state, water, sediment)
        water, sediment, moved = flow(height, water, sediment)
        water *= (1.0 - cfg.R4_EVAPORATION_RATE)
        state = update_water_states(state, water)
        print(f"  R4 iteration {i:3d} | water moved: {moved:9.3f} | "
              f"eroded: {eroded:8.4f} | deposited: {deposited:9.4f}")
    print("  states:", state_counts_text(state))
    return height, state, sediment, water
