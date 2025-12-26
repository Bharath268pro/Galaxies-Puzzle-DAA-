# Galaxies Model Architecture (DAA)

## Overview

The `GalaxiesModel` class encapsulates the complete puzzle state and game logic, providing a clean separation of concerns between the puzzle engine and UI.

## Class Structure

```python
class GalaxiesModel:
    def __init__(self, n=7, seed=None)
    
    Attributes:
    -----------
    - puzzle: GalaxiesPuzzle          # Puzzle generation & solution
    - edges: set                      # Currently drawn edges
    - arrows: list                    # User-placed arrow markers
    - undo_stack: list                # Move history for undo
    - redo_stack: list                # Move history for redo
    - solution_edges: set             # Target solution edges
    - N: int                          # Grid size (N x N)
    - rng: Random                     # Random number generator
```

## Core Responsibilities

### 1. Puzzle Management
- **`new_puzzle()`**: Generate new puzzle with fresh state
  - Creates new `GalaxiesPuzzle` instance
  - Initializes solution edges
  - Resets drawn edges and arrows
  - Clears undo/redo stacks

### 2. State Tracking
- **`edges`**: Set of all drawn edges by user
- **`arrows`**: List of user-placed arrow markers
- **`undo_stack`**: History of moves for undo operation
- **`redo_stack`**: History of moves for redo operation

### 3. Algorithms Integration
- **Graph Building**: `cell_adjacency_graph()`, `build_regions_from_edges()`
- **Greedy Hints**: `compute_edge_scores()`, `select_best_edge()`
- **Sorting**: `sort_edges_by_score()`, `sort_regions_by_size()`, `sort_candidates_by_heuristic()`

## Method Categories

### Graph Operations
```
cell_adjacency_graph()           # Build undirected grid graph
build_regions_from_edges()       # Find connected components via BFS
```

### Greedy Hint Algorithm
```
compute_edge_scores()            # Score all potential edges
select_best_edge()               # Choose best edge (greedy)
_count_region_dots()             # Helper: count dots in region
```

### Sorting Functions
```
sort_edges_by_score()            # Sort edges by greedy score
sort_regions_by_size()           # Sort regions by size (ascending)
sort_candidates_by_heuristic()   # Sort by custom heuristic
```

## Data Flow

```
Puzzle Creation
    ↓
GalaxiesPuzzle.generate()
    ↓
GalaxiesModel created with puzzle
    ↓
User draws edges via UI
    ↓
GalaxiesModel.edges updated
    ↓
Graph operations detect regions
    ↓
Game logic validates regions
    ↓
Hint system uses greedy algorithm to suggest next move
```

## Integration with Game Loop

The model serves as the **data layer** between:
- **UI** (reads model state, sends edge/arrow actions)
- **Puzzle Engine** (generates solution)
- **Game Logic** (validates moves, tracks history)

```
GalaxiesUI
    ↓
(draw edge) → GalaxiesGame (game logic) ↔ GalaxiesModel ↔ GalaxiesPuzzle
    ↓
(render state)
```

## Key Design Principles

1. **Separation of Concerns**: Model handles state; UI handles display
2. **Encapsulation**: All puzzle operations go through model methods
3. **Single Source of Truth**: One model instance per game session
4. **Undo/Redo Support**: Stack-based history for move reversibility
5. **Algorithm Integration**: Model implements DAA algorithms (Graph, Greedy, Sorting)

## Performance Characteristics

| Operation | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| `cell_adjacency_graph()` | O(N²) | O(N²) |
| `build_regions_from_edges()` | O(N²) | O(N²) |
| `compute_edge_scores()` | O(E·R·D) | O(E) |
| `sort_edges_by_score()` | O(E log E) | O(E) |
| `sort_regions_by_size()` | O(R log R) | O(R) |

Where: N=grid size, E=edges, R=regions, D=dots

## Future Extensions

- Caching of adjacency graphs (rebuild only when edges change)
- Difficulty rating based on minimum moves to solve
- Pruning strategies for hint generation
- Machine learning for move prediction
