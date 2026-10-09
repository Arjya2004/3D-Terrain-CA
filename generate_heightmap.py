"""
generate_heightmap.py - make a heightmap and put it in HEIGHTMAP_FOLDER.

    python generate_heightmap.py

Steps (press Enter at any question to accept the [default]; the defaults
reproduce the heightmap used in the paper):

  1. 1D cellular automaton  -> vertical profile        (generator/profile_ca.py)
  2. rotation / extension / hybrid stacking -> heightmap (generator/shapes.py)
  3. Voronoi variation (seed, points, strength)          (generator/voronoi.py)
  4. you type a NAME -> saved as HEIGHTMAP_FOLDER/<name>.npy

Then run  python placement_engine.py : the new file is in its list.
"""
import os
import re
import numpy as np

from generator.profile_ca import initial_cells, generate_vertical_profile
from generator.shapes import rotation, extension, hybrid_stacking
from generator.voronoi import apply_voronoi

HERE = os.path.dirname(os.path.abspath(__file__))
HEIGHTMAP_FOLDER = os.path.join(HERE, "HEIGHTMAP_FOLDER")   # read by placement_engine.py
WORK_FOLDER = os.path.join(HERE, "GENERATED")               # profile + preview pictures


# ----------------------------------------------------------------------
# small input helpers
# ----------------------------------------------------------------------
def ask_int(text, default, minimum=None, maximum=None):
    while True:
        raw = input(f"{text} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            value = int(raw)
        except ValueError:
            print("  Enter a whole number.")
            continue
        if minimum is not None and value < minimum:
            print(f"  Must be at least {minimum}.")
        elif maximum is not None and value > maximum:
            print(f"  Must be at most {maximum}.")
        else:
            return value


def ask_float(text, default, minimum=None, maximum=None):
    while True:
        raw = input(f"{text} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            value = float(raw)
        except ValueError:
            print("  Enter a number.")
            continue
        if minimum is not None and value < minimum:
            print(f"  Must be at least {minimum}.")
        elif maximum is not None and value > maximum:
            print(f"  Must be at most {maximum}.")
        else:
            return value


def ask_yes_no(text, default=True):
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{text} [{hint}]: ").strip().lower()
        if raw == "":
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False


# ----------------------------------------------------------------------
# STEP 1 - vertical profile
# ----------------------------------------------------------------------
def ask_vertical_profile():
    profile_file = os.path.join(WORK_FOLDER, "vertical_profile.npy")
    if os.path.exists(profile_file):
        if ask_yes_no("A vertical profile from an earlier run exists. Reuse it?", default=False):
            profile = np.load(profile_file)
            print(f"  Loaded profile {profile.shape}")
            return profile

    print("\nSTEP 1 - 1D cellular automaton (vertical profile)")
    cells_no = ask_int("Number of cells", 80, minimum=3)
    iterations = ask_int("Number of iterations (generations)", 40, minimum=1)

    region_size = ask_int("Region size (cells per region)", cells_no, minimum=1, maximum=cells_no)
    while cells_no % region_size != 0:
        print("  Region size must divide the number of cells exactly.")
        region_size = ask_int("Region size", cells_no, minimum=1, maximum=cells_no)
    regions = cells_no // region_size
    print(f"  Regions: {regions}")

    print("\nRule numbers are 0-255 (EX: With Y in same rules in every generation and rule 222 for forming 2D Triangle).")
    same_rule = ask_yes_no("Use the same rules in every generation?", default=True)
    rule_matrix = []
    if same_rule:
        rules = [ask_int(f"  Rule for region {r + 1}", 222, 0, 255) for r in range(regions)]
        rule_matrix = [rules] * iterations
    else:
        for g in range(iterations):
            print(f"  Generation G{g:02d}")
            rule_matrix.append([ask_int(f"    Rule for region {r + 1}", 222, 0, 255)
                                for r in range(regions)])

    print("\nInitial configuration:  1 single seed   2 double seed   3 triple seed   "
          "4 random   5 custom [Normally we use 5]")
    choice = ask_int("Choice", 5, 1, 5)
    probability, custom = 0.5, ""
    if choice == 4:
        probability = ask_float("Probability of 1", 0.5, 0.0, 1.0)
    if choice == 5:
        while True:
            custom = input(f"  Enter {cells_no} binary digits[EX: For Triangle and 80 cells give 39 0's then 1 then 40 0's .....00100.....]: ").strip()
            if len(custom) == cells_no and set(custom) <= {"0", "1"}:
                break
            print("  Invalid input.")

    cells = initial_cells(cells_no, choice, probability, custom)
    profile = generate_vertical_profile(cells, rule_matrix, region_size)
    print(f"  Vertical profile created: {profile.shape[0]} generations x {profile.shape[1]} cells")

    os.makedirs(WORK_FOLDER, exist_ok=True)
    np.save(profile_file, profile)
    save_picture(profile, os.path.join(WORK_FOLDER, "vertical_profile.png"),
                 "Vertical profile (1D CA)", cmap="binary")
    return profile


# ----------------------------------------------------------------------
# STEP 2 + 3 - shape and variation
# ----------------------------------------------------------------------
def ask_methods():
    print("\nSTEP 2 - 3D method:  1 rotation   2 extension   3 hybrid stacking   4 all three")
    choice = ask_int("Method", 1, 1, 4)
    methods = {1: ["rotation"], 2: ["extension"], 3: ["hybrid"],
               4: ["rotation", "extension", "hybrid"]}[choice]
    settings = {}
    if "extension" in methods:
        settings["extension_depth"] = ask_int("  Extrusion depth (cells)", 20, minimum=1)
    if "hybrid" in methods:
        settings["hybrid_depth"] = ask_int("  Hybrid stacking: number of stacked profiles", 20, minimum=1)
        settings["hybrid_expand"] = ask_int("  Hybrid stacking: maximum expansion (cells)", 8, minimum=0)
    return methods, settings


def ask_voronoi():
    print("\nSTEP 3 - Voronoi variation (makes the shape irregular)")
    if not ask_yes_no("Apply Voronoi variation?", default=True):
        return None
    return {
        "seed": ask_int("  Seed (random pattern number)", 100),
        "points": ask_int("  Number of Voronoi points", 1000, minimum=1),
        "strength": ask_float("  Strength", 5, minimum=0.0),
    }


def build_heightmap(profile, method, settings, voronoi):
    if method == "rotation":
        heightmap = rotation(profile)
    elif method == "extension":
        heightmap = extension(profile, settings["extension_depth"])
    else:
        heightmap = hybrid_stacking(profile, settings["hybrid_depth"], settings["hybrid_expand"])
    if voronoi is not None:
        heightmap = apply_voronoi(heightmap, voronoi["seed"], voronoi["points"], voronoi["strength"])
    return heightmap


# ----------------------------------------------------------------------
# STEP 4 - name and save
# ----------------------------------------------------------------------
BAD_NAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def ask_name():
    print("\nSTEP 4 - name of the heightmap file (saved in HEIGHTMAP_FOLDER)")
    while True:
        name = input("File name: ").strip()
        if name.lower().endswith(".npy"):
            name = name[:-4]
        if not name:
            print("  A name is needed.")
        elif BAD_NAME_CHARS.search(name):
            print('  The name cannot contain  \\ / : * ? " < > |')
        else:
            return name


def save_heightmap(heightmap, name):
    os.makedirs(HEIGHTMAP_FOLDER, exist_ok=True)
    path = os.path.join(HEIGHTMAP_FOLDER, name + ".npy")
    if os.path.exists(path) and not ask_yes_no(f"  {name}.npy already exists. Overwrite?", default=False):
        return None
    np.save(path, heightmap)
    return path


def save_picture(array, path, title, cmap="terrain"):
    """Preview picture (skipped silently if matplotlib is not installed)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.figure(figsize=(6, 6))
    plt.imshow(array, cmap=cmap, origin="lower" if cmap == "terrain" else "upper",
               interpolation="nearest", aspect="auto" if cmap == "binary" else "equal")
    plt.title(title)
    if cmap == "terrain":
        plt.colorbar(label="Height")
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def list_position(name):
    """Number of this file in the placement engine's list (sorted .npy files)."""
    files = sorted(f[:-4] for f in os.listdir(HEIGHTMAP_FOLDER) if f.endswith(".npy"))
    return files.index(name) + 1, len(files)


# ----------------------------------------------------------------------
def main():
    print("=" * 60)
    print("HEIGHTMAP GENERATOR")
    print("=" * 60)

    profile = ask_vertical_profile()
    methods, settings = ask_methods()
    voronoi = ask_voronoi()
    base_name = ask_name()

    print()
    for method in methods:
        name = base_name if len(methods) == 1 else f"{base_name}_{method}"
        heightmap = build_heightmap(profile, method, settings, voronoi)
        path = save_heightmap(heightmap, name)
        if path is None:
            print(f"  {method}: not saved.")
            continue
        save_picture(heightmap, os.path.join(WORK_FOLDER, "previews", name + ".png"),
                     f"{name}  (max {heightmap.max():.2f})")
        number, total = list_position(name)
        print(f"  {method}: saved HEIGHTMAP_FOLDER/{name}.npy  shape={heightmap.shape}  "
              f"max={heightmap.max():.2f}   -> number {number} of {total} in the placement engine")

    print("\nNow run:  python placement_engine.py")


if __name__ == "__main__":
    main()
