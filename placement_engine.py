"""
placement_engine.py - STEP 0 of the CA pipeline: put a heightmap on the terrain grid.

    python placement_engine.py

Asks: grid size, ground height, which heightmap from HEIGHTMAP_FOLDER, and the
centre (X, Y) where it is placed. Several heightmaps can be placed one after the
other; type Q to finish. Result: OUTPUT/height_grid.npy

Equation (for every patch cell (i, j) with value v > 0):

    x = centre_x - rows // 2 + i          y = centre_y - cols // 2 + j
    height(x, y) = max( height(x, y), ground + v )       if (x, y) is inside the grid

The `max` keeps the taller surface where heightmaps overlap; cells with v <= 0 are skipped,
so the rest of the grid stays at the ground height.
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HEIGHTMAP_FOLDER = os.path.join(HERE, "HEIGHTMAP_FOLDER")
OUTPUT_FOLDER = os.path.join(HERE, "OUTPUT")


def load_heightmaps(folder):
    """All .npy files in the folder, as {name: float32 array}, sorted by file name."""
    if not os.path.exists(folder):
        raise SystemExit(f"Folder '{folder}' not found.")
    heightmaps = {}
    for file in sorted(os.listdir(folder)):
        if file.endswith(".npy"):
            heightmaps[file[:-4]] = np.load(os.path.join(folder, file)).astype(np.float32)
    if not heightmaps:
        raise SystemExit("HEIGHTMAP_FOLDER has no .npy files. Run generate_heightmap.py first.")
    return heightmaps


def place_patch(grid, patch, ground, center_x, center_y):
    """Place one heightmap on the grid (see the equation at the top of this file)."""
    size = grid.shape[0]
    rows, cols = patch.shape
    for i in range(rows):
        for j in range(cols):
            value = patch[i, j]
            if value <= 0:
                continue
            x = center_x - rows // 2 + i
            y = center_y - cols // 2 + j
            if 0 <= x < size and 0 <= y < size:
                grid[x, y] = max(grid[x, y], ground + value)


def interactive_placement(grid, heightmaps, ground):
    names = list(heightmaps)
    while True:
        print("\n" + "=" * 60)
        print("AVAILABLE HEIGHTMAPS")
        print("=" * 60)
        for number, name in enumerate(names, 1):
            print(f"{number}. {name}")
        print("\nQ. Finish Placement")

        choice = input("\nChoose Heightmap : ").strip()
        if choice.upper() == "Q":
            break
        if not choice.isdigit() or not 1 <= int(choice) <= len(names):
            print("\nInvalid Heightmap Number.")
            continue
        name = names[int(choice) - 1]

        try:
            center_x = int(input("Center X : "))
            center_y = int(input("Center Y : "))
        except ValueError:
            print("\nInvalid Coordinates.")
            continue

        place_patch(grid, heightmaps[name], ground, center_x, center_y)
        print(f"\n{name} placed successfully.")


def main():
    print("=" * 60)
    print("TERRAIN PLACEMENT ENGINE")
    print("=" * 60)
    size = int(input("\nTerrain Grid Size : "))
    ground = float(input("Ground Height : "))

    heightmaps = load_heightmaps(HEIGHTMAP_FOLDER)
    grid = np.full((size, size), ground, dtype=np.float32)
    interactive_placement(grid, heightmaps, ground)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    np.save(os.path.join(OUTPUT_FOLDER, "height_grid.npy"), grid)
    print("\nPlacement finished. Saved OUTPUT/height_grid.npy")
    print("Now run:  python run_pipeline.py")


if __name__ == "__main__":
    main()
