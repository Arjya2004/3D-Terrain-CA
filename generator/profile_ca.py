"""
profile_ca.py - STEP 1 (was c.py): the 1D cellular automaton -> vertical profile.

An elementary cellular automaton (ECA) is a row of cells, each 0 or 1.
Each generation, a cell looks at (left, itself, right) and its new state is
read from the RULE NUMBER (0-255), written in binary:

        new state = bit number ( 4*left + 2*centre + right )  of the rule number

Hybrid version: the row is cut into equal REGIONS. Every region has its own rule
(and the rule may change from generation to generation). Each region wraps
around inside itself (its left end sees its right end), so regions are independent.

Stacking the generations one under the other gives a 2D picture, the
"vertical profile": row g = generation g, column = cell position.
"""
import numpy as np


def next_generation(cells, rule_per_cell, region_size):
    """One CA generation. `cells` and `rule_per_cell` are 1D integer arrays."""
    regions = cells.reshape(-1, region_size)
    rules = rule_per_cell.reshape(-1, region_size)
    left = np.roll(regions, 1, axis=1)        # wraps inside each region
    right = np.roll(regions, -1, axis=1)
    pattern = 4 * left + 2 * regions + right  # 0 ... 7
    return ((rules >> pattern) & 1).reshape(-1)


def initial_cells(cells_no, choice, probability=0.5, custom=""):
    """First row. choice: 1 single seed, 2 double, 3 triple, 4 random, 5 custom."""
    cells = np.zeros(cells_no, dtype=np.int64)
    mid = cells_no // 2
    if choice == 1:
        cells[mid] = 1
    elif choice == 2:
        cells[mid] = 1
        if mid + 1 < cells_no:
            cells[mid + 1] = 1
    elif choice == 3:
        if mid - 1 >= 0:
            cells[mid - 1] = 1
        cells[mid] = 1
        if mid + 1 < cells_no:
            cells[mid + 1] = 1
    elif choice == 4:
        cells = np.random.choice([0, 1], size=cells_no,
                                 p=[1 - probability, probability]).astype(np.int64)
    elif choice == 5:
        cells = np.array([int(ch) for ch in custom], dtype=np.int64)
    else:
        raise ValueError("choice must be 1 to 5")
    return cells


def generate_vertical_profile(cells, rule_matrix, region_size):
    """Run the hybrid ECA.

    cells        first row (1D array, length = number of cells)
    rule_matrix  one list per generation, one rule per region
    region_size  cells per region (must divide the number of cells)

    Returns an array of shape (generations + 1, cells): row 0 is the first row.
    """
    cells = np.asarray(cells, dtype=np.int64)
    history = [cells.copy()]
    for rules_of_regions in rule_matrix:
        rule_per_cell = np.repeat(np.asarray(rules_of_regions, dtype=np.int64), region_size)
        cells = next_generation(cells, rule_per_cell, region_size)
        history.append(cells.copy())
    return np.array(history)
