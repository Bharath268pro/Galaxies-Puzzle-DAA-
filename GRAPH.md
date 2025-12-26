# Graph Data Structure & Algorithm (DAA)

## Overview

The Galaxies puzzle uses an **undirected, unweighted graph** to represent the cell connectivity of the grid. This graph structure enables efficient region detection via BFS traversal.

## Graph Representation

### Adjacency List (Preferred)
```python
adj = {
    cell_id: [neighbor_ids]
    # Example: 5 -> [4, 6, 12]  (cell 5 connected to cells 4, 6, 12)
}
```

### Cell ID Mapping
```
Grid (N=5):          Cell IDs:
  0 1 2 3 4           0  1  2  3  4
  5 6 7 8 9           5  6  7  8  9
 10 11 12 13 14      10 11 12 13 14
 15 16 17 18 19      15 16 17 18 19
 20 21 22 23 24      20 21 22 23 24

cell_id = y * N + x
(x, y) ↔ cell_id
```

## Building the Graph

### Method: `cell_adjacency_graph()`

```python
def cell_adjacency_graph(self, excluded_edges=None):
    """Build adjacency list from current edge state."""
    
    1. Initialize empty adjacency list
    2. For each cell (x, y) in grid:
       a. Check right neighbor: if no vertical edge at (x+1, y)
          → add neighbor_id to adjacency list
       b. Check bottom neighbor: if no horizontal edge at (x, y+1)
          → add neighbor_id to adjacency list
    3. Remove duplicate neighbors
    4. Return adjacency dict
```

### Time & Space Complexity

| Metric | Value |
|--------|-------|
| Time | O(N²) |
| Space | O(N²) |
| Justification | N² cells, each checked constant times, 2 edges per cell |

### Example Output
```python
# For a 3×3 grid with edge at ('v', 1, 0):
{
    0: [1, 3],        # Cell 0 connected to 1 (blocked) and 3
    1: [2, 4],        # Cell 1 connected to 2 and 4
    2: [5],           # Cell 2 connected only to 5
    3: [0, 4, 6],     # Cell 3 connected to 0, 4, 6
    4: [1, 3, 5, 7],  # Cell 4 central, 4 neighbors
    ...
}
```

## Graph Traversal: BFS for Region Detection

### Method: `build_regions_from_edges()`

Finds connected components (regions) using breadth-first search.

```python
def build_regions_from_edges(self):
    """Find all connected components (regions) via BFS."""
    
    1. Build adjacency list from current edges
    2. Initialize: seen = ∅, regions = []
    3. For each unvisited cell:
       a. Start BFS from this cell
       b. Queue = [cell]
       c. While queue not empty:
          - Dequeue cell
          - Add to current region
          - For each unvisited neighbor:
            • Mark visited
            • Enqueue neighbor
       d. Add region to results
    4. Return all regions
```

### BFS Algorithm Properties

| Property | Value |
|----------|-------|
| **Time** | O(V + E) = O(N²) |
| **Space** | O(N²) for queue + visited set |
| **Optimality** | Finds all connected components |
| **Completeness** | Guaranteed to find all regions |

### Pseudocode

```
BFS_REGIONS(adjacency_list, N):
    seen ← ∅
    regions ← []
    
    for start ← 0 to N²-1:
        if start in seen:
            continue
        
        region ← ∅
        queue ← [start]
        seen.add(start)
        
        while queue not empty:
            cell ← queue.dequeue()
            region.add(cell)
            
            for neighbor in adjacency[cell]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.enqueue(neighbor)
        
        regions.add(region)
    
    return regions
```

### Example Trace

```
Grid 3×3 with edge blocking cells 1-2:

Initial: [0][1]│[2]
         [3][4][5]
         [6][7][8]

Adjacency:
{0: [1,3], 1: [4], 2: [5], 3: [0,4,6], 4: [1,3,5,7], 5: [2,4,8], 6: [3,7], 7: [4,6,8], 8: [5,7]}

BFS from 0:
  Region 1: {0,1,3,4,6,7,8} (all except isolated 2,5)
  Region 2: {2,5} (isolated by edge)
```

## Edge Types in the Graph

### Boundary Edges (Fixed)
```
('h', x, y)  # Horizontal edge at position (x, y)
('v', x, y)  # Vertical edge at position (x, y)
```

### When Building Adjacency
- If edge exists between two cells → no adjacency
- If edge doesn't exist → cells are adjacent (can traverse)

### Edge Blocking

```
Vertical edge ('v', x+1, y) blocks right neighbor
Horizontal edge ('h', x, y+1) blocks bottom neighbor

Cell (x, y):
    ├─ Right: ('v', x+1, y) blocks → not adjacent
    ├─ Left:  ('v', x, y) blocks   → not adjacent
    ├─ Down:  ('h', x, y+1) blocks → not adjacent
    └─ Up:    ('h', x, y) blocks   → not adjacent
```

## Performance Analysis

### Graph Building: O(N²)
- Iterate all N² cells
- Check 2 neighbors per cell (constant time)
- Total: O(N²)

### BFS Traversal: O(N² + E)
- Visit each cell once: O(N²)
- Process each adjacency relation: O(E)
- Since grid graph has ≤ 4 edges per cell: E ≤ 2N²
- Total: O(N²)

### Region Detection Full Cost: O(N²)
- Build adjacency: O(N²)
- BFS all cells: O(N²)
- Total: O(N²)

## Integration with Game Logic

```
User draws edge
    ↓
GalaxiesModel.edges updated
    ↓
cell_adjacency_graph() called
    ↓
build_regions_from_edges() called
    ↓
Regions detected
    ↓
Game validates: exactly 1 dot per region?
    ↓
Display valid regions
```

## Advanced: Dynamic Graph Updates

For efficiency in repeated queries:

```python
class OptimizedGraph:
    def __init__(self):
        self._adjacency = None
        self._dirty = True
    
    def add_edge(self, edge):
        self._dirty = True
    
    def get_adjacency(self):
        if self._dirty:
            self._adjacency = self.build()
            self._dirty = False
        return self._adjacency
```

This avoids rebuilding the graph on every query.

## Key Takeaways

1. **Graph Type**: Undirected, unweighted, planar
2. **Representation**: Adjacency list (N²×degree space)
3. **Traversal**: BFS for connected components
4. **Complexity**: O(N²) for all operations
5. **Purpose**: Region detection from drawn edges
6. **Validation**: Ensures proper region enclosure
