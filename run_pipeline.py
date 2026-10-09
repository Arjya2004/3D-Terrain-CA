"""
run_pipeline.py - run the whole 8-state terrain CA.

    python placement_engine.py    # step 0   : OUTPUT/height_grid.npy
    python run_pipeline.py        # CA rules : OUTPUT/final_height_grid.npy (the only file it writes)

The number of iterations is asked when you start (press Enter for the default
in config.py), or give it directly:   python run_pipeline.py 100

Pipeline
    initial states -> R1 blending -> R2 thermal erosion -> R3 sediment
                   -> R4 hydraulic erosion -> R5 final state coupling
"""
import os
import sys
import numpy as np
import config as cfg
from initial_states import classify_initial_states
from r1_blending import run_r1
from r2_thermal_erosion import run_r2
from r3_sediment_transport import run_r3
from r4_hydraulic_erosion import run_r4
from r5_state_coupling import run_r5
from ca_core import state_counts_text


def save(name, array):
    np.save(os.path.join(cfg.OUTPUT_FOLDER, name), array)


def ask_iterations():
    """Iterations from the command line, else ask (Enter = config default)."""
    if len(sys.argv) > 1:
        text = sys.argv[1]
        if not text.isdigit() or int(text) <= 0:
            raise SystemExit("Iterations must be a whole number greater than zero.")
        return int(text)
    while True:
        text = input(f"Iterations [{cfg.ITERATIONS}]: ").strip()
        if text == "":
            return cfg.ITERATIONS
        if text.isdigit() and int(text) > 0:
            return int(text)
        print("Enter a whole number greater than zero.")


def main():
    path = os.path.join(cfg.OUTPUT_FOLDER, "height_grid.npy")
    if not os.path.exists(path):
        raise SystemExit("OUTPUT/height_grid.npy not found - run  python placement_engine.py  first.")

    n = ask_iterations()
    height0 = np.load(path)
    print(f"Terrain {height0.shape}, {n} iterations per rule")

    state0 = classify_initial_states(height0)
    print("initial states:", state_counts_text(state0))

    h1, s1 = run_r1(height0, state0, n)
    h2, s2, sed2 = run_r2(h1, s1, n)
    h3, s3, sed3 = run_r3(h2, s2, sed2, n)
    h4, s4, sed4, water4 = run_r4(h3, s3, sed3, n)
    h5, _, _ = run_r5(h4, s4, sed4, n)

    save("final_height_grid.npy", h5)
    print(f"\nFinal height range: {h5.min():.4f} to {h5.max():.4f}")
    print(f"Saved {cfg.OUTPUT_FOLDER}/final_height_grid.npy")
    # \033[96m sets the color to Cyan, and \033[0m resets it back to normal
    print("\033[96mYou can use lesser iterations for lesser changes of the terrain by erosion\033[0m")


if __name__ == "__main__":
    main()
