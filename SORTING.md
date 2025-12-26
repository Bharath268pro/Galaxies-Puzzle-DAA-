# Sorting Algorithms (DAA)

## Overview

The Galaxies game uses multiple sorting techniques to optimize performance and improve algorithm efficiency. Sorting is applied to edges, regions, and candidates.

## Sorting Techniques

### 1. Sort by Greedy Score (Descending)

#### Method: `sort_edges_by_score()`

Sorts all edges by their greedy score in descending order.

```python
def sort_edges_by_score(self):
    """Order edges by score for ranked candidate selection."""
    
    1. Compute all edge scores via compute_edge_scores()
    2. Sort edges by score descending
    3. Return [(edge, score), ...] list
```

#### Algorithm Details
```
INPUT: dictionary {edge → score}
OUTPUT: list of (edge, score) tuples sorted descending by score

SORT(scores):
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

#### Complexity Analysis

| Metric | Value |
|--------|-------|
| Time | O(E log E) |
| Space | O(E) |
| Sorting Algorithm | Python's Timsort (hybrid merge/insertion sort) |

Where E = number of candidate edges

#### Use Case: Heuristic-Guided Search
```
sorted_edges = model.sort_edges_by_score()

# Return top-3 suggestions to user
for i, (edge, score) in enumerate(sorted_edges[:3]):
    print(f"Option {i+1}: {edge} (score: {score:.1f})")
```

#### Example Output
```
[
    (('v', 3, 0), 28.0),   # Highest score
    (('h', 2, 3), 19.5),   # Second
    (('v', 1, 2), 15.0),   # Third
    ...
]
```

### 2. Sort by Region Size (Ascending)

#### Method: `sort_regions_by_size()`

Sorts regions by size for efficient validation.

```python
def sort_regions_by_size(self, regions):
    """Order regions by size for efficient checking."""
    
    1. For each region: calculate len(region)
    2. Sort regions ascending by size
    3. Return sorted regions
```

#### Algorithm Details
```
INPUT: list of regions (each region = set of cell_ids)
OUTPUT: same regions sorted by size (ascending)

SORT_BY_SIZE(regions):
    return sorted(regions, key=lambda r: len(r))
```

#### Complexity Analysis

| Metric | Value |
|--------|-------|
| Time | O(R log R) |
| Space | O(R) |
| R | Number of regions |

#### Why Ascending Order?

**Optimization**: **Fail fast on invalid regions**

```
Region validation (simplified):
    if num_dots_in_region != 1:
        return False
    if not has_rotational_symmetry():
        return False
    ...

With small regions first:
    - Dot checking is O(D) per region
    - Symmetry checking is O(|region|)
    - Small regions fail faster
    - Total time: O(Σ(|region|)) = O(N²) regardless of order
    - But: Practical speedup by catching invalid early
```

#### Example Trace

```
Unsorted regions:
    Region 1: {0,1,2,3,4,5,6,7,8}       (9 cells)
    Region 2: {9,10}                     (2 cells)
    Region 3: {11,12,13,14,15,16,17}    (7 cells)

After sort_regions_by_size():
    Region 2: {9,10}                     (2 cells)  ← Check first
    Region 3: {11,12,13,14,15,16,17}    (7 cells)
    Region 1: {0,1,2,3,4,5,6,7,8}       (9 cells)  ← Check last
```

### 3. Sort by Heuristic (Custom)

#### Method: `sort_candidates_by_heuristic()`

Sorts candidates by a problem-specific heuristic.

```python
def sort_candidates_by_heuristic(self, candidates):
    """Order candidates by heuristic value."""
    
    1. For each candidate edge: compute heuristic value
    2. Sort descending by heuristic
    3. Return sorted candidates
```

#### Heuristic: Grid Center Distance

```python
def heuristic(edge):
    edge_type, x, y = edge
    n = self.N
    center_x = abs(x - n / 2)
    center_y = abs(y - n / 2)
    return -(center_x + center_y)  # Negative for descending sort
```

**Intuition**: Edges near grid center likely to create balanced splits

#### Complexity Analysis

| Metric | Value |
|--------|-------|
| Time | O(C log C + C) |
| Space | O(C) |
| C | Number of candidates |

Where: O(C log C) for sort + O(C) for heuristic computation

#### Example: 7×7 Grid

```
Grid center: (3.5, 3.5)

Edge ('v', 3, 3):  distance = |3-3.5| + |3-3.5| = 1.0 (high priority)
Edge ('v', 1, 1):  distance = |1-3.5| + |1-3.5| = 5.0 (low priority)
Edge ('v', 6, 6):  distance = |6-3.5| + |6-3.5| = 5.0 (low priority)

Sorted (high priority first):
    1. ('v', 3, 3) - distance 1.0
    2. ('h', 3, 3) - distance 1.0
    3. ('v', 2, 3) - distance 2.0
    4. ('h', 3, 2) - distance 2.0
    ...
    50. ('v', 0, 0) - distance 7.0
```

## Combined Sorting Pipeline

### Use Case: Top-K Hints

```python
def get_top_k_hints(self, k=3):
    """Get top-k sorted edge suggestions."""
    
    # Sort all edges by greedy score
    sorted_edges = self.sort_edges_by_score()
    
    # Return top-k
    return sorted_edges[:k]
```

**Complexity**: O(E log E) to sort all, O(1) to get top-k

### Use Case: Efficient Validation

```python
def validate_all_regions(self):
    """Check all regions efficiently."""
    
    regions = self.build_regions_from_edges()
    
    # Sort by size (fail fast)
    sorted_regions = self.sort_regions_by_size(regions)
    
    for region in sorted_regions:
        if not self.is_valid_region(region):
            return False
    
    return True
```

**Complexity**: O(R log R + R·V) where V = validation time

## Sorting Algorithm Choice: Timsort

Python's `sorted()` uses **Timsort**, a hybrid algorithm.

### Timsort Properties
```
Algorithm: Merge sort + Insertion sort
Best Case: O(n) - already sorted
Average: O(n log n) - random data
Worst Case: O(n log n) - reverse sorted

Space: O(n)
Stability: Yes (equal elements maintain relative order)
```

### Why Timsort?

1. ✅ Stable: Maintains relative order of equal elements
2. ✅ Adaptive: Fast on partially-sorted data
3. ✅ Efficient: Optimal O(n log n) worst-case
4. ✅ Cache-friendly: Uses insertion sort for small runs

## Sorting Patterns in Galaxies

### Pattern 1: Score-Based Ranking
```
Edges ranked by quality → User sees best options first
Example: Hint system shows top 3 suggestions
```

### Pattern 2: Size-Based Optimization
```
Regions checked in ascending size → Fail early on invalid
Example: Validation stops at first invalid region
```

### Pattern 3: Distance-Based Heuristic
```
Candidates near center preferred → Better balance
Example: Large search spaces pruned to center edges
```

## Performance Impact

### Without Sorting (Brute Force)
```
Check all regions randomly: O(R·V) where V = avg validation time
Risk: Check huge invalid regions before small valid ones
```

### With Sorting (Smart Selection)
```
Check regions by size: O(R log R + R·V)
Benefit: Small regions checked first (faster failure)
```

### Example: 7×7 Grid, 10 Regions

```
Without sorting:
    Region 1 (size 9): 450μs validation
    Region 2 (size 2): 100μs validation  ← Fast but checked late
    Total: 9000μs

With sorting:
    Region 2 (size 2): 100μs validation  ← Fast and checked first
    Region 1 (size 9): 450μs validation  ← (only if needed)
    Total: 550μs (if region 2 invalid) → 6x speedup!
```

## Key Takeaways

1. **Sort by Score**: O(E log E) for hint ranking
2. **Sort by Size**: O(R log R) for validation efficiency
3. **Sort by Heuristic**: O(C log C) for search pruning
4. **Timsort**: Python's optimal O(n log n) algorithm
5. **Stability**: Sorting preserves relative order of equal elements
6. **Practical Benefit**: Often 2-10x speedup in real scenarios
7. **Space Cost**: O(E), O(R), or O(C) for each sort

## Advanced: Multi-Key Sorting

For complex prioritization:

```python
def sort_edges_multi_key(self):
    """Sort by primary (score) then secondary (distance) key."""
    
    scores = self.compute_edge_scores()
    
    def sort_key(edge):
        score = scores[edge]
        distance = self._heuristic_distance(edge)
        # Tuple: sort by score desc, then distance asc
        return (-score, distance)
    
    sorted_edges = sorted(self.all_edges(), key=sort_key)
    return sorted_edges
```

**Complexity**: O(E log E) + O(E) heuristic = O(E log E)
