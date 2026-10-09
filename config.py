"""
config.py - every parameter of the terrain cellular automaton, in one place.

Only values that are really used by the rules are listed here.
ITERATIONS is only the DEFAULT: run_pipeline.py asks for the number of iterations
(press Enter to use this default).
"""
from ca_core import SOIL, SLOPE, SEDIMENT, ROCK, PLATEAU, PEAK

# ----------------------------------------------------------------------
# Run settings
# ----------------------------------------------------------------------
ITERATIONS = 70            # default number of CA steps, used for EVERY rule (R1 ... R5)

# ----------------------------------------------------------------------
# R1 - boundary blending
# ----------------------------------------------------------------------
R1_TRANSITION_GAIN = 0.20   # how fast "transition strength" builds up per iteration
R1_EXCHANGE_RATE   = 0.15   # share of a height drop handed to each lower neighbour
R1_SOIL_TO_SLOPE   = 0.60   # transition strength at which SOIL becomes SLOPE
R1_EMPTY_GAIN      = 0.05   # EMPTY floor raised by more than this becomes SOIL

# ----------------------------------------------------------------------
# R2 - state-aware thermal (gradient) erosion
# ----------------------------------------------------------------------
R2_TALUS            = 0.5   # base talus threshold (largest stable height drop)
R2_EROSION_STRENGTH = 0.8   # overall erosion speed
R2_MAX_MOVE         = 0.5   # most material one cell may lose per iteration
R2_MIN_HEIGHT       = 0.1   # a cell is never eroded below this height
R2_SEDIMENT_RATIO   = 0.08  # SOIL/SLOPE becomes SEDIMENT if loss/height >= this
# talus threshold of a state = R2_TALUS * factor
R2_THRESHOLD_FACTOR = {SOIL: 0.75, SLOPE: 1.00, ROCK: 1.50, PLATEAU: 1.75, PEAK: 2.00}
# how easily a state erodes (bigger = softer)
R2_RESISTANCE       = {SOIL: 0.35, SLOPE: 0.25, ROCK: 0.10, PLATEAU: 0.05, PEAK: 0.02}

# ----------------------------------------------------------------------
# R3 - sediment transport and deposition
# ----------------------------------------------------------------------
R3_TRANSPORT_RATE      = 0.60   # share of a cell's sediment that moves per iteration
R3_TRANSPORT_THRESHOLD = 0.20   # a neighbour is "downhill" only if lower by more than this
R3_DEPOSITION_RATE     = 0.35   # share of sediment that settles in a trap cell
R3_MAX_DEPOSIT         = 0.50   # most a cell can receive per iteration

# ----------------------------------------------------------------------
# R4 - hydraulic erosion (rain, flow, carrying capacity)
# ----------------------------------------------------------------------
R4_RAIN_AMOUNT        = 0.02    # water added to every cell each iteration
R4_EVAPORATION_RATE   = 0.10    # share of water that evaporates each iteration
R4_FLOW_RATE          = 0.20    # share of a cell's water that flows downhill
R4_CARRYING_CAPACITY  = 0.50    # capacity = this * water * slope drop
R4_EROSION_RATE       = 0.10
R4_DEPOSITION_RATE    = 0.35
R4_MAX_EROSION        = 0.50
R4_MAX_DEPOSITION     = 0.50
R4_WATER_THRESHOLD    = 0.30    # water depth at which a cell becomes WATER
R4_MIN_HEIGHT         = 0.10    # a cell is never eroded below this height
# how easily a state is eroded by water (EMPTY / WATER cannot erode)
R4_RESISTANCE = {SOIL: 1.00, SLOPE: 0.75, SEDIMENT: 1.20,
                 ROCK: 0.20, PLATEAU: 0.10, PEAK: 0.05}

# ----------------------------------------------------------------------
# R5 - final state coupling
# ----------------------------------------------------------------------
R5_SLOPE_THRESHOLD   = 0.45   # normalised slope above this = sloping
R5_STEEP_THRESHOLD   = 0.70   # normalised slope above this = steep (ROCK)
R5_PLATEAU_THRESHOLD = 0.20   # normalised slope below this = flat
R5_PEAK_THRESHOLD    = 0.80   # normalised height above this = PEAK
R5_SOIL_EROSION_RATE   = 0.025
R5_SLOPE_EROSION_RATE  = 0.040
R5_MAX_EROSION         = 0.12
R5_TRANSPORT_RATE      = 0.18
R5_DEPOSITION_RATE     = 0.25
R5_SEDIMENT_ACTIVATION = 0.025   # sediment needed to count as "active"
R5_SEDIMENT_CLEAR      = 0.008   # sediment below this counts as "cleared"
R5_MIN_HEIGHT          = 0.01

# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------
import os
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OUTPUT")
