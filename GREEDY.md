# Greedy Algorithm for Hint Generation (DAA)

## Overview

The hint system uses a **greedy algorithm** to suggest the next best move. It evaluates all candidate edges, scores them based on heuristics, and greedily selects the edge with the maximum score.

## Algorithm Concept

### Greedy Strategy
```
For each possible edge E:
    Score(E) = heuristic value that measures "goodness"
    
Best Move = argmax Score(E) over all edges E
```

### Why Greedy?
- ✅ Fast: Single pass to find best candidate
- ✅ Good results: Heuristics guide toward valid regions
- ❌ Not optimal: May miss better sequences
- ⚠️ Trade-off: Speed vs. optimality

## Implementation

### Method 1: `compute_edge_scores()`

Evaluates all potential edges and assigns scores.

```python
def compute_edge_scores(self):
    """Score all edges based on region separation & validity."""
    
    1. Get all possible edges in grid
    2. Filter out: border edges, already-drawn edges
    3. For each candidate edge E:
       a. Temporarily add E to drawn edges
       b. Detect regions using BFS
       c. Calculate score:
          - Score += len(region) * 0.5  # Prefer balanced regions
          - Score += valid_count * 10    # Heavily reward valid regions
       d. Remove E from drawn edges
       e. Store Score[E]
    4. Return scores dictionary
```

### Scoring Metrics

#### Metric 1: Region Size Balance
```python
score += len(region) * 0.5
```
- Reason: Balanced regions (not too big/small) more likely valid
- Weight: 0.5 (lower priority)
- Effect: Prevents creating extremely imbalanced splits

#### Metric 2: Valid Region Count
```python
valid_count = sum(1 for region if count_dots(region) == 1)
score += valid_count * 10
```
- Reason: Regions with exactly 1 dot are valid candidates
- Weight: 10.0 (high priority, incentivize)
- Effect: Strongly prefer moves that create valid regions

#### Combined Score
```
Total Score = Balance Score + Validity Score
           = Σ(len(region) * 0.5) + 10 * valid_count
```

### Time & Space Complexity

| Metric | Value | Justification |
|--------|-------|---------------|
| **Time** | O(E · R · D) | E edges × O(R) BFS × O(D) dot checking |
| **Space** | O(E) | Store scores for all E candidate edges |

Where: E = number of candidate edges, R = avg region size, D = number of dots

### Code Example

```python
# For a 5×5 grid with some edges drawn
scores = model.compute_edge_scores()

# Output:
# {
#     ('v', 1, 0): 12.5,     # Good separation
#     ('h', 2, 2): 8.0,      # Moderate
#     ('v', 3, 4): 15.0,     # Excellent (creates valid region)
#     ...
# }
```

### Method 2: `select_best_edge()`

Greedily selects the edge with maximum score.

```python
def select_best_edge(self):
    """Return (edge, score) with maximum score."""
    
    1. Compute scores for all edges
    2. Find max_score edge
    3. Return (best_edge, best_score)
```

**Greedy Choice**: Pick the single edge with highest score

```python
best_edge = max(scores.items(), key=lambda x: x[1])
```

- Time: O(1) if scores pre-computed, O(E) to compute
- Correctness: Always returns highest-scored edge
- Optimality: Not guaranteed to be globally optimal

## Algorithm Correctness & Completeness

### Correctness
✅ Always returns valid hint (real edge, drawable)
✅ Score reflects actual region separation
✅ Heuristics based on puzzle rules (1 dot per region)

### Completeness
⚠️ Finds some good moves, not necessarily best sequence
⚠️ May suggest moves leading to unsolvable state
⚠️ Local optimization (greedy) ≠ global optimization

## Example Trace

### Initial State
```
Grid 5×5, partially solved:
  ┌─┬─┬─┬─┬─┐
  │ │ │●│ │ │
  ├─┼─┴─┼─┼─┤
  │●│ │ │●│ │
  ├─┼─┬─┼─┼─┤
  │ │ │ │ │ │
  ├─┼─┼─┼─┴─┤
  │●│ │ │ │●│
  ├─┼─┼─┼─┬─┤
  │ │ │●│ │ │
  └─┴─┴─┴─┴─┘

Current edges: {('v', 2, 1), ('h', 0, 1), ...}
```

### Candidate Edges & Scoring

| Edge | Regions Created | Score | Reason |
|------|-----------------|-------|--------|
| ('v', 1, 2) | [R1=9, R2=10, ...] | 19.5 | Balanced split |
| ('h', 2, 3) | [R1=5, R2=20] | 12.5 | Imbalanced |
| ('v', 3, 0) | [R1=8, R2=17, ...] | **28.0** | ✓ Creates valid region |
| ('h', 4, 4) | [R1=6, R2=19] | 12.5 | Imbalanced |

### Greedy Selection

```
Best Edge = ('v', 3, 0) with score 28.0

Hint to user: "Draw vertical edge between columns 3-4, row 0"
```

## Performance Considerations

### Bottleneck: Edge Scoring
- Computing scores for all E edges is expensive
- For 7×7 grid: ~70 edges to evaluate
- Each requires BFS (O(N²)) → Total O(E · N²)

### Optimization 1: Score Caching
```python
class CachedGreedy:
    def __init__(self):
        self.cached_scores = None
        self.cached_edges = None
    
    def get_best_edge(self):
        if self.cached_scores is None:
            self.cached_scores = self.compute_edge_scores()
        return max(self.cached_scores.items(), key=lambda x: x[1])
    
    def invalidate_cache(self):
        self.cached_scores = None
```

### Optimization 2: Early Termination
```python
def compute_edge_scores_fast(self, top_k=10):
    """Return top-k edges by score only."""
    # Sample edges, compute scores
    # Keep running top-k
    # Return when confidence high
    pass
```

### Optimization 3: Pruning
```python
def select_best_edge_pruned(self):
    """Skip edges unlikely to be good."""
    candidates = self.get_promising_edges()  # O(E) filter
    scores = {e: self.score(e) for e in candidates}
    return max(scores.items(), key=lambda x: x[1])
```

## Alternative Strategies

### Strategy 1: Exhaustive Search (Optimal)
```
For all possible move sequences:
    Simulate game
    Check if leads to valid solution
Select move from best sequence
```
- **Pros**: Finds optimal move
- **Cons**: Exponential time O(E^depth)
- **Use**: Small grids, offline analysis

### Strategy 2: Random Selection (Baseline)
```
edges = all_candidate_edges()
return random.choice(edges)
```
- **Pros**: Very fast O(1)
- **Cons**: No intelligence
- **Use**: Casual mode, testing

### Strategy 3: Greedy (Current, Balance)
```
scores = compute_edge_scores()
return argmax(scores)
```
- **Pros**: Fast O(E·N²), good results
- **Cons**: Not globally optimal
- **Use**: Normal play, hints

### Strategy 4: Monte Carlo Tree Search (MCTS)
```
For N iterations:
    Simulate random game from state
    Track winning sequences
Return most-simulated edge
```
- **Pros**: Balances exploration/exploitation
- **Cons**: Slower, probabilistic
- **Use**: Hard puzzles, learning

## Code Integration

### How Hint System Works
```
User clicks "Hint" button
    ↓
UI calls game.get_hint()
    ↓
game.get_hint() calls model.select_best_edge()
    ↓
model.compute_edge_scores()  [O(E·N²)]
    ↓
model.select_best_edge()     [O(E)]
    ↓
Returns best_edge to UI
    ↓
UI highlights suggested edge
    ↓
User clicks to accept hint
```

## Key Takeaways

1. **Greedy**: Makes locally optimal choice at each step
2. **Fast**: O(E·N²) per hint (acceptable for game)
3. **Smart**: Scores based on puzzle rules, not random
4. **Practical**: Balances speed and hint quality
5. **Cacheable**: Scores remain valid until edges change
6. **Optimizable**: Early termination, pruning, caching available
