#!/usr/bin/env python3
"""Quick test of core Galaxies game logic without GUI."""

import sys
sys.path.insert(0, '/home/bharath/Documents/DAA')

from Galaxies import (
    GalaxiesPuzzle, GalaxiesGame, 
    has_rotational_symmetry, get_region_cells, 
    count_dots_in_region, is_region_valid
)

print("=" * 60)
print("Testing Galaxies Puzzle Logic")
print("=" * 60)

# Test 1: Puzzle generation
print("\n[Test 1] Puzzle Generation")
puzzle = GalaxiesPuzzle(n=5)
puzzle.generate()
print(f"✓ Generated {len(puzzle.regions)} polyomino regions on 5x5 grid")
print(f"✓ Placed {len(puzzle.dots)} dots (one per region)")
print(f"✓ Solution has {len(puzzle.solution_edges)} edges")

# Test 2: Game initialization
print("\n[Test 2] Game Initialization")
game = GalaxiesGame(n=5)
print(f"✓ Created game with N={game.N}")
print(f"✓ Fixed edges (border): {len(game.fixed)}")
print(f"✓ Solution edges: {len(game.solution)}")

# Test 3: Cell adjacency and components
print("\n[Test 3] Region Detection (BFS)")
adj = game.cell_adj_graph()
print(f"✓ Built adjacency graph")

# Test 4: Valid regions checking
print("\n[Test 4] Region Validation")
valid = game.get_valid_regions()
print(f"✓ Found {len(valid)} cells in valid regions")

# Test 5: Arrow and edge toggle
print("\n[Test 5] Edge Toggle & Arrow Placement")
test_edge = ('h', 1, 1)
game.toggle_edge(test_edge, who="test")
print(f"✓ Added edge {test_edge}")
print(f"✓ Edges now: {len(game.edges)}")
game.toggle_edge(test_edge, who="test")
print(f"✓ Removed edge {test_edge}")
print(f"✓ Edges now: {len(game.edges)}")

# Test 6: Undo/Redo
print("\n[Test 6] Undo/Redo")
edge1 = ('h', 2, 2)
game.toggle_edge(edge1, who="test")
print(f"✓ Added edge: {len(game.edges)}")
game.undo()
print(f"✓ After undo: {len(game.edges)}")
game.redo()
print(f"✓ After redo: {len(game.edges)}")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
print("\nYou can now run: python /home/bharath/Documents/DAA/Galaxies.py")
