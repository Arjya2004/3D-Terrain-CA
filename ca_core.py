"""
ca_core.py - the pieces shared by all rules.

* the 8 cell states
* the Moore neighbourhood (the 8 cells around a cell)
* small helpers used by every rule

Every rule in this project is a CELLULAR AUTOMATON step:
    1. each cell looks at its 8 Moore neighbours,
    2. the cell's new value is computed ONLY from the grids as they were at
       the start of the iteration (synchronous update),
    3. all new values are written together at the end of the iteration.
"""
import numpy as np

# ----------------------------------------------------------------------
# The 8 states
# ----------------------------------------------------------------------
EMPTY, WATER, SEDIMENT, SOIL, SLOPE, ROCK, PLATEAU, PEAK = range(8)

STATE_NAMES = {
    EMPTY: "EMPTY", WATER: "WATER", SEDIMENT: "SEDIMENT", SOIL: "SOIL",
    SLOPE: "SLOPE", ROCK: "ROCK", PLATEAU: "PLATEAU", PEAK: "PEAK",
}

# ----------------------------------------------------------------------
# Moore neighbourhood
# ----------------------------------------------------------------------
# Row/column offsets of the 8 neighbours (the cell itself is excluded).
MOORE_OFFSETS = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                 if (dr, dc) != (0, 0)]


def interior_cells(rows, cols):
    """Yield (r, c) for every cell that has all 8 neighbours.

    The outer ring of the grid is never updated (it has no full
    neighbourhood), so every cell returned here has exactly 8 neighbours.
    """
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            yield r, c


def neighbours(r, c):
    """The 8 Moore neighbours of an interior cell, as (row, col) pairs."""
    return [(r + dr, c + dc) for dr, dc in MOORE_OFFSETS]


def lower_neighbours(grid, r, c, min_drop=0.0):
    """Neighbours lower than cell (r, c) by MORE than `min_drop`.

    Returns a list of (row, col, drop) with drop = grid[r, c] - grid[nr, nc].
    `grid` is a terrain height grid, or a water-surface grid (height + water).
    """
    found = []
    for nr, nc in neighbours(r, c):
        drop = grid[r, c] - grid[nr, nc]
        if drop > min_drop:
            found.append((nr, nc, drop))
    return found


def clear_border(grid):
    """Open boundary: whatever reaches the outer ring leaves the map."""
    grid[0, :] = 0.0
    grid[-1, :] = 0.0
    grid[:, 0] = 0.0
    grid[:, -1] = 0.0


def state_counts_text(state):
    """One-line summary of how many cells are in each state."""
    return "  ".join(f"{STATE_NAMES[s]}={int(np.sum(state == s))}" for s in range(8))
