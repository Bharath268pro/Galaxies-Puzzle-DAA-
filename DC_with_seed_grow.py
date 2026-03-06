import tkinter as tk
from tkinter import messagebox
from collections import deque, defaultdict
from dataclasses import dataclass
import random

def my_len(obj):
    c = 0
    for _ in obj: c += 1
    return c

def my_abs(val):
    if val < 0: return -val
    return val

def my_int(val):
    return int(val)

def my_round(val):
    r = val // 1
    if val - r >= 0.5: r += 1
    return int(r)

def my_range(start, stop=None, step=1):
    if stop is None:
        stop = start
        start = 0
    res = []
    curr = start
    while curr < stop:
        res.append(curr)
        curr += step
    return res

def my_sum(obj):
    s = 0
    for x in obj: s += x
    return s

def my_enumerate(iterable):
    res = []
    i = 0
    for x in iterable:
        res.append((i, x))
        i += 1
    return res

def my_sorted(iterable, key=None, reverse=False):
    lst = list(iterable)
    n = my_len(lst)
    i = 0
    while i < n:
        j = 0
        while j < n - i - 1:
            val1 = lst[j] if key is None else key(lst[j])
            val2 = lst[j+1] if key is None else key(lst[j+1])
            swap = (val1 < val2) if reverse else (val1 > val2)
            if swap:
                lst[j], lst[j+1] = lst[j+1], lst[j]
            j += 1
        i += 1
    return lst

def my_min(iterable, key=None):
    best = None
    best_val = None
    first = True
    for x in iterable:
        val = x if key is None else key(x)
        if first or val < best_val:
            best = x
            best_val = val
            first = False
    return best

def my_max(iterable, key=None):
    best = None
    best_val = None
    first = True
    for x in iterable:
        val = x if key is None else key(x)
        if first or val > best_val:
            best = x
            best_val = val
            first = False
    return best

def bfs_components(adj, total_nodes):
    seen = set()
    comps = []
    for s in my_range(total_nodes):
        if s in seen:
            continue
        q = deque([s])
        seen.add(s)
        comp = []
        while q:
            u = q.popleft()
            comp.append(u)
            for v in adj.get(u, []):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        comps.append(comp)
    return comps


class GalaxiesPuzzle:
    def __init__(self, n=4, rng=None):
        self.N = n
        self.rng = rng or random.Random()
        self.rects = []
        self.owner = [-1] * (n * n)
        self.dots = []
        self.solution_edges = set()

    def cell_id(self, x, y):
        return y * self.N + x

    def sym_cell(self, cx, cy, dx, dy):
        """Return the 180-degree rotational symmetric cell of (cx,cy) about dot (dx,dy).
        Dot is in grid-coordinate space (can be x.0, x.5). 
        The centre of cell (cx,cy) is (cx+0.5, cy+0.5).
        Symmetric centre = (2*dx - (cx+0.5), 2*dy - (cy+0.5))
        Which gives cell floor of that.
        """
        scx = 2 * dx - cx - 1
        scy = 2 * dy - cy - 1
        return int(scx), int(scy)

    def _cell_neighbors(self, cid, n):
        """Return list of valid 4-connected neighbor cell IDs."""
        cx, cy = cid % n, cid // n
        result = []
        for nx, ny in [(cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)]:
            if 0 <= nx < n and 0 <= ny < n:
                result.append(ny * n + nx)
        return result

    def generate(self, target_rects=None):
        n = self.N
        self.owner = [-1] * (n * n)
        self.dots = []
        cells_remaining = set(my_range(n * n))
        regions = []

        if target_rects is None:
            target_rects = max(n * n // 4, 3)

        # 1. Potential dots at 0.5-increment positions (interior only)
        potential_dots = []
        for y2 in my_range(1, 2 * n):
            for x2 in my_range(1, 2 * n):
                potential_dots.append((x2 / 2.0, y2 / 2.0))
        self.rng.shuffle(potential_dots)

        # 2. Seed regions from dots
        for dx, dy in potential_dots:
            if my_len(regions) >= target_rects:
                break
            seed_cells = self._get_initial_cells_for_dot(dx, dy)
            if seed_cells and all(c in cells_remaining for c in seed_cells):
                r_idx = my_len(regions)
                self.dots.append((dx, dy))
                new_region = set()
                for c in seed_cells:
                    self.owner[c] = r_idx
                    cells_remaining.discard(c)
                    new_region.add(c)
                regions.append(new_region)

        # 3. Growth Phase - enforce CONNECTIVITY at every step
        # A pair (ncid, scid) is valid to add to region r_idx only if:
        #   - ncid is adjacent to the existing region (we already iterate from region cells)
        #   - scid is unowned AND (scid == ncid OR scid is adjacent to region OR scid is adjacent to ncid)
        max_passes = n * n * 4
        passes = 0
        while cells_remaining and passes < max_passes:
            passes += 1
            made_progress = False
            r_indices = list(my_range(my_len(regions)))
            self.rng.shuffle(r_indices)

            for r_idx in r_indices:
                if not cells_remaining:
                    break
                dx, dy = self.dots[r_idx]
                region = regions[r_idx]
                possible_extensions = []

                for c in list(region):
                    for ncid in self._cell_neighbors(c, n):
                        if ncid not in cells_remaining:
                            continue
                        # ncid is adjacent to region (via cell c)
                        scx, scy = self.sym_cell(ncid % n, ncid // n, dx, dy)
                        if not (0 <= int(scx) < n and 0 <= int(scy) < n):
                            continue
                        scid = int(scy) * n + int(scx)

                        if scid == ncid:
                            # Self-symmetric: single cell addition, always connected
                            possible_extensions.append((ncid, ncid))
                        elif scid in cells_remaining:
                            # scid must be connected to region after adding ncid:
                            # i.e. scid adjacent to region OR scid adjacent to ncid
                            scid_adj_region = any(nb in region for nb in self._cell_neighbors(scid, n))
                            scid_adj_ncid = scid in self._cell_neighbors(ncid, n)
                            if scid_adj_region or scid_adj_ncid:
                                possible_extensions.append((ncid, scid))

                if possible_extensions:
                    c1, c2 = self.rng.choice(possible_extensions)
                    for cid in set([c1, c2]):
                        if cid in cells_remaining:
                            self.owner[cid] = r_idx
                            cells_remaining.discard(cid)
                            region.add(cid)
                    made_progress = True

            if not made_progress:
                break

        # 4. Fallback: assign remaining cells to adjacent regions, maintaining symmetry
        # Only assign a cell to a region if it is adjacent to that region (connectivity)
        # and its symmetric partner is also adjacent/owned by same region
        max_fallback = n * n * 6
        fallback_passes = 0
        while cells_remaining and fallback_passes < max_fallback:
            fallback_passes += 1
            made_progress = False
            for cid in list(cells_remaining):
                if cid not in cells_remaining:
                    continue
                cx, cy = cid % n, cid // n
                best_r = -1
                best_dist = float('inf')
                for r_idx, (dx, dy) in my_enumerate(self.dots):
                    # cid must be adjacent to this region
                    if not any(nb in regions[r_idx] for nb in self._cell_neighbors(cid, n)):
                        continue
                    scx, scy = self.sym_cell(cx, cy, dx, dy)
                    if not (0 <= int(scx) < n and 0 <= int(scy) < n):
                        continue
                    scid = int(scy) * n + int(scx)
                    if scid == cid:
                        # Self-symmetric, just need cid itself
                        dist = (cx + 0.5 - dx) ** 2 + (cy + 0.5 - dy) ** 2
                        if dist < best_dist:
                            best_dist = dist
                            best_r = r_idx
                    elif scid in cells_remaining or self.owner[scid] == r_idx:
                        # scid must also be adjacent to region (or adjacent to cid)
                        scid_adj_region = any(nb in regions[r_idx] for nb in self._cell_neighbors(scid, n))
                        scid_adj_cid = scid in self._cell_neighbors(cid, n)
                        if scid_adj_region or scid_adj_cid:
                            dist = (cx + 0.5 - dx) ** 2 + (cy + 0.5 - dy) ** 2
                            if dist < best_dist:
                                best_dist = dist
                                best_r = r_idx
                if best_r >= 0:
                    dx, dy = self.dots[best_r]
                    scx, scy = self.sym_cell(cx, cy, dx, dy)
                    scid = int(scy) * n + int(scx)
                    for assign_cid in set([cid, scid]):
                        if assign_cid in cells_remaining:
                            self.owner[assign_cid] = best_r
                            cells_remaining.discard(assign_cid)
                            regions[best_r].add(assign_cid)
                    made_progress = True
            if not made_progress:
                break

        # 5. Last resort: remaining cells become their own single-cell symmetric regions
        while cells_remaining:
            cid = next(iter(cells_remaining))
            cx, cy = cid % n, cid // n
            # Create a new dot at cell centre (self-symmetric)
            new_dot = (cx + 0.5, cy + 0.5)
            r_idx = my_len(self.dots)
            self.dots.append(new_dot)
            regions.append({cid})
            self.owner[cid] = r_idx
            cells_remaining.discard(cid)

        self.solution_edges = self.compute_solution_edges()

    def _get_initial_cells_for_dot(self, dx, dy):
        """Return the minimal symmetric seed cells for a dot at (dx, dy).
        
        For a dot at a cell-centre (x+0.5, y+0.5): seed is just that one cell.
        For a dot on a horizontal edge (x+0.5, y): seed is the two cells above/below.
        For a dot on a vertical edge (x, y+0.5): seed is the two cells left/right.
        For a dot on a grid intersection (x, y): seed is the four surrounding cells.
        """
        n = self.N
        # dx and dy are multiples of 0.5
        # Check if dot is on integer coords, half coords, or mixed
        dx_half = (dx * 2) % 2 == 1  # True if dx is x.5
        dy_half = (dy * 2) % 2 == 1  # True if dy is y.5

        seeds = set()

        if dx_half and dy_half:
            # Dot at centre of a single cell (ix+0.5, iy+0.5)
            ix = int(dx)
            iy = int(dy)
            if 0 <= ix < n and 0 <= iy < n:
                seeds.add(iy * n + ix)
        elif dx_half and not dy_half:
            # Dot on horizontal edge between rows iy-1 and iy
            ix = int(dx)
            iy = int(dy)
            for cy in [iy - 1, iy]:
                if 0 <= ix < n and 0 <= cy < n:
                    seeds.add(cy * n + ix)
        elif not dx_half and dy_half:
            # Dot on vertical edge between cols ix-1 and ix
            ix = int(dx)
            iy = int(dy)
            for cx in [ix - 1, ix]:
                if 0 <= cx < n and 0 <= iy < n:
                    seeds.add(iy * n + cx)
        else:
            # Dot at grid intersection (ix, iy)
            ix = int(dx)
            iy = int(dy)
            for cy in [iy - 1, iy]:
                for cx in [ix - 1, ix]:
                    if 0 <= cx < n and 0 <= cy < n:
                        seeds.add(cy * n + cx)

        if not seeds:
            return []

        # Validate: every seed must have its symmetric partner also in seeds
        for c in seeds:
            cx, cy = c % n, c // n
            scx, scy = self.sym_cell(cx, cy, dx, dy)
            if int(scx) != scx or int(scy) != scy:
                return []
            scid = int(scy) * n + int(scx)
            if scid not in seeds:
                return []

        return list(seeds)

    def compute_solution_edges(self):
        n = self.N
        edges = set()

        for x in my_range(n):
            edges.add(('h', x, 0))
            edges.add(('h', x, n))
        for y in my_range(n):
            edges.add(('v', 0, y))
            edges.add(('v', n, y))

        for y in my_range(n):
            for x in my_range(n):
                o = self.owner[self.cell_id(x, y)]
                if x + 1 < n:
                    o2 = self.owner[self.cell_id(x + 1, y)]
                    if o2 != o:
                        edges.add(('v', x + 1, y))
                if y + 1 < n:
                    o2 = self.owner[self.cell_id(x, y + 1)]
                    if o2 != o:
                        edges.add(('h', x, y + 1))
        return edges


def has_rotational_symmetry(region_cells, dot_x, dot_y, n):
    for x, y in region_cells:
        sym_x = 2 * dot_x - x - 1
        sym_y = 2 * dot_y - y - 1
        if (int(sym_x), int(sym_y)) not in region_cells:
            return False
    return True


def count_dots_in_region(region_cells, dots):
    count = 0
    for dot_x, dot_y in dots:
        for x, y in region_cells:
            if x <= dot_x < x + 1 and y <= dot_y < y + 1:
                count += 1
                break
    return count


def is_region_valid(region_cells, dot_x, dot_y, dots, n):
    dot_count = count_dots_in_region(region_cells, dots)
    if dot_count != 1:
        return False
    if not has_rotational_symmetry(region_cells, dot_x, dot_y, n):
        return False
    return True

#DP memoization...

class SymmetryValidator:
    def __init__(self):
        self.symmetry_cache = {}
        self.dots_in_region_cache = {}
        self.last_edges_hash = None
        self.cache_hits = 0
        self.cache_misses = 0

    def clear_cache_if_needed(self, edges_hash):
        if self.last_edges_hash != edges_hash:
            self.symmetry_cache.clear()
            self.dots_in_region_cache.clear()
            self.last_edges_hash = edges_hash

    def memoized_symmetry_check(self, region_cells, dot_x, dot_y, n):
        key = (region_cells, dot_x, dot_y, n)
        if key in self.symmetry_cache:
            self.cache_hits += 1
            return self.symmetry_cache[key]

        self.cache_misses += 1
        result = True
        for x, y in region_cells:
            sym_x = 2 * dot_x - x - 1
            sym_y = 2 * dot_y - y - 1
            if (int(sym_x), int(sym_y)) not in region_cells:
                result = False
                break

        self.symmetry_cache[key] = result
        return result

    def memoized_dots_in_region(self, region_cells_frozen, dots):
        if region_cells_frozen in self.dots_in_region_cache:
            self.cache_hits += 1
            return self.dots_in_region_cache[region_cells_frozen]

        self.cache_misses += 1
        dots_found = []
        for dot_idx, (dot_x, dot_y) in my_enumerate(dots):
            for x, y in region_cells_frozen:
                if x <= dot_x < x + 1 and y <= dot_y < y + 1:
                    dots_found.append((dot_idx, dot_x, dot_y))
                    break

        self.dots_in_region_cache[region_cells_frozen] = dots_found
        return dots_found

    def is_valid_region_with_dp(self, region_cells, dot_x, dot_y, dots, n):
        region_frozen = frozenset(region_cells)

        dots_in_region = self.memoized_dots_in_region(region_frozen, dots)
        if my_len(dots_in_region) != 1:
            return False

        return self.memoized_symmetry_check(region_frozen, dot_x, dot_y, n)

    def get_stats(self):
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'total': total,
            'hit_rate': hit_rate,
            'symmetry_cache_size': my_len(self.symmetry_cache),
            'dots_cache_size': my_len(self.dots_in_region_cache)
        }


@dataclass
class Move:
    edge: tuple
    added: bool
    who: int


@dataclass
class Arrow:
    cell_x: int
    cell_y: int
    dot_idx: int


class GalaxiesGame:
    def __init__(self, n=4, seed=None):
        self.N = n
        self.rng = random.Random(seed)
        self.dp_validator = SymmetryValidator()
        self._solver_cache = None
        self.computation_count = 0
        self.new_puzzle()

    @staticmethod
    def border_edges(n):
        edges = set()
        for x in my_range(n):
            edges.add(('h', x, 0))
            edges.add(('h', x, n))
        for y in my_range(n):
            edges.add(('v', 0, y))
            edges.add(('v', n, y))
        return edges

    def new_puzzle(self):
        self.puzzle = GalaxiesPuzzle(n=self.N, rng=self.rng)
        self.puzzle.generate()
        self.fixed = self.border_edges(self.N)
        self.solution = set(self.puzzle.solution_edges) - set(self.fixed)
        self.reset()

    def reset(self):
        self.edges = set(self.fixed)
        self.history = []
        self.redo_stack = []
        self.arrows = []
        self._solver_cache = None

    def toggle_edge(self, edge, who):
        if edge in self.fixed:
            return False
        if edge in self.edges:
            self.edges.remove(edge)
            self.history.append(Move(edge=edge, added=False, who=who))
        else:
            self.edges.add(edge)
            self.history.append(Move(edge=edge, added=True, who=who))
        self.redo_stack.clear()
        return True

    def undo(self):
        if not self.history:
            return False
        mv = self.history.pop()
        if mv.added:
            self.edges.discard(mv.edge)
        else:
            self.edges.add(mv.edge)
        self.redo_stack.append(mv)
        return True

    def redo(self):
        if not self.redo_stack:
            return False
        mv = self.redo_stack.pop()
        if mv.added:
            self.edges.add(mv.edge)
        else:
            self.edges.discard(mv.edge)
        self.history.append(mv)
        return True

    def is_solved(self):
        return (self.edges - self.fixed) == self.solution

    def cell_adj_graph(self, extra_block=None):
        adj = defaultdict(list)
        n = self.N
        blocked = set(self.edges)
        if extra_block is not None:
            blocked.add(extra_block)

        def cid(x, y):
            return y * n + x

        for y in my_range(n):
            for x in my_range(n):
                u = cid(x, y)
                if x + 1 < n:
                    w = ('v', x + 1, y)
                    if w not in blocked:
                        v = cid(x + 1, y)
                        adj[u].append(v)
                        adj[v].append(u)
                if y + 1 < n:
                    w = ('h', x, y + 1)
                    if w not in blocked:
                        v = cid(x, y + 1)
                        adj[u].append(v)
                        adj[v].append(u)
        return adj

    def get_valid_regions(self):
        n = self.N
        adj = self.cell_adj_graph()
        comps = bfs_components(adj, n * n)
        valid_cells = set()

        edges_hash = hash(frozenset(self.edges))
        self.dp_validator.clear_cache_if_needed(edges_hash)

        for comp in comps:
            region_cells = {(cid % n, cid // n) for cid in comp}

            dots_in_region = self.dp_validator.memoized_dots_in_region(
                frozenset(region_cells),
                self.puzzle.dots
            )

            if my_len(dots_in_region) == 1:
                dot_idx, dot_x, dot_y = dots_in_region[0]
                if self.dp_validator.is_valid_region_with_dp(
                    region_cells, dot_x, dot_y,
                    self.puzzle.dots, n
                ):
                    valid_cells.update(comp)

        return valid_cells

    def dc_solve_pure(self, x0, x1):
        n = self.N
        dots = self.puzzle.dots

        if x1 - x0 == 1:
            states = [{}]
            for y in my_range(n):
                new_states = []
                for state in states:
                    for dot_idx, d in my_enumerate(dots):
                        self.computation_count += 1
                        px = my_int(2 * d[0]) - x0 - 1
                        py = my_int(2 * d[1]) - y - 1
                        
                        if 0 <= px < n and 0 <= py < n:
                            new_s = state.copy()
                            new_s[(x0, y)] = dot_idx
                            new_states.append(new_s)
                states = new_states
            return states

        mid = (x0 + x1) // 2
        
        left_states = self.dc_solve_pure(x0, mid)
        right_states = self.dc_solve_pure(mid, x1)

        merged_states = []
        for l_state in left_states:
            for r_state in right_states:
                self.computation_count += 1
                valid = True
                new_merged = l_state.copy()

                for k in l_state:
                    dot_idx = l_state[k]
                    cx = k[0]
                    cy = k[1]
                    d = dots[dot_idx]
                    px = my_int(2 * d[0]) - cx - 1
                    py = my_int(2 * d[1]) - cy - 1

                    if mid <= px < x1:
                        if (px, py) in r_state and r_state[(px, py)] != dot_idx:
                            valid = False
                            break
                
                if not valid:
                    continue

                for k in r_state:
                    dot_idx = r_state[k]
                    new_merged[k] = dot_idx
                    cx = k[0]
                    cy = k[1]
                    d = dots[dot_idx]
                    px = my_int(2 * d[0]) - cx - 1
                    py = my_int(2 * d[1]) - cy - 1

                    if x0 <= px < mid:
                        if (px, py) in l_state and l_state[(px, py)] != dot_idx:
                            valid = False
                            break
                
                if valid:
                    merged_states.append(new_merged)

        return merged_states

    def dc_solve_simultaneous(self):
        """
        D&C approach: Grows all seeds simultaneously. 
        Each step expands regions symmetrically.
        """
        n = self.N
        dots = self.puzzle.dots
        
        # 1. Initialize regions with their core seeds
        initial_assignment = {}
        regions_data = [] # List of sets containing cell IDs for each dot
        
        for i, (dx, dy) in my_enumerate(dots):
            seeds = self.puzzle._get_initial_cells_for_dot(dx, dy)
            if not seeds: return None
            
            for cell_id in seeds:
                if cell_id in initial_assignment:
                    return None # Overlapping seeds = impossible puzzle
                initial_assignment[cell_id] = i
            regions_data.append(set(seeds))

        cells_to_fill = n * n - my_len(initial_assignment)

        def grow_recursive(current_assignment, regions, remaining_count):
            if remaining_count == 0:
                return current_assignment

            # Find all possible valid symmetric expansions for all regions
            # A 'growth' is a tuple (dot_index, cell_id, partner_id)
            possible_growths = []
            
            for r_idx, (dx, dy) in my_enumerate(dots):
                region_cells = regions[r_idx]
                for cid in region_cells:
                    for ncid in self.puzzle._cell_neighbors(cid, n):
                        if ncid not in current_assignment:
                            # Calculate symmetric partner
                            scx, scy = self.puzzle.sym_cell(ncid % n, ncid // n, dx, dy)
                            if 0 <= scx < n and 0 <= scy < n:
                                scid = int(scy) * n + int(scx)
                                
                                # Partner must be unassigned OR be ncid itself
                                if scid not in current_assignment or scid == ncid:
                                    possible_growths.append((r_idx, ncid, scid))

            # Optimization: If a cell MUST belong to a specific dot, pick that first
            # (Constraint Satisfaction)
            
            if not possible_growths:
                return None

            # Sort or pick a growth to try (Heuristic: smallest region first)
            # For simplicity, we try the first available growth expansion
            r_idx, c1, c2 = possible_growths[0]
            
            # Branch 1: Expand region r_idx with c1 and c2
            next_assignment = current_assignment.copy()
            next_regions = [r.copy() for r in regions]
            
            added_count = 0
            for c in {c1, c2}:
                if c not in next_assignment:
                    next_assignment[c] = r_idx
                    next_regions[r_idx].add(c)
                    added_count += 1
            
            res = grow_recursive(next_assignment, next_regions, remaining_count - added_count)
            if res: return res

            # Branch 2: This specific expansion was wrong (backtrack)
            # In a pure D&C/Backtracking growth, we'd mark this (r_idx, c1, c2) as invalid
            return None

        final_map = grow_recursive(initial_assignment, regions_data, cells_to_fill)
        return final_map

    def computer_move(self):
        """Place one correct edge - uses direct solution for hint/solve, D&C for experiment."""
        # Simple direct approach: pick a missing solution edge (used for Hint button)
        missing = self.solution - (self.edges - self.fixed)
        if not missing:
            return None

        n = self.N
        center = n / 2.0
        best_edge = my_min(missing, key=lambda e: my_abs(e[1] - center) + my_abs(e[2] - center))
        self.toggle_edge(best_edge, who="computer")
        self._solver_cache = None
        return best_edge

    def computer_move_dc(self):
        """Experimental D&C solver - attempts to solve using divide and conquer."""
        edges_snapshot = frozenset(self.edges)
        if self._solver_cache and self._solver_cache[0] == edges_snapshot:
            assignment = self._solver_cache[1]
        else:
            self.computation_count = 0
            final_states = self.dc_solve_pure(0, self.N)
            
            print(f"Total pure D&C computations: {self.computation_count}")
            
            if not final_states:
                return None
            
            assignment = final_states[0]
            self._solver_cache = (edges_snapshot, assignment)

        n = self.N
        solved_edges = set()

        for y in my_range(n):
            for x in my_range(n):
                owner = assignment.get((x, y), -1)
                if x + 1 < n and assignment.get((x + 1, y), -1) != owner:
                    solved_edges.add(('v', x + 1, y))
                if y + 1 < n and assignment.get((x, y + 1), -1) != owner:
                    solved_edges.add(('h', x, y + 1))

        missing = solved_edges - self.edges
        if not missing:
            return None

        center = n / 2
        best_edge = my_min(missing, key=lambda e: my_abs(e[1] - center) + my_abs(e[2] - center))

        self.toggle_edge(best_edge, who="computer")
        self._solver_cache = None
        return best_edge


class GalaxiesUI(tk.Tk):
    def __init__(self):
        # Check for display before creating Tk window
        import os
        if not os.environ.get('DISPLAY'):
            print("No display available. Exiting.")
            return
        
        super().__init__()
        self.title("Galaxies Puzzle")

        self.grid_size = 4
        self.menu_result = None

        self.after(100, self.init_game_with_difficulty)

    def init_game_with_difficulty(self):
        # Check if we have a display
        try:
            self.winfo_screenwidth()
            has_display = True
        except tk.TclError:
            has_display = False

        if has_display:
            self.show_difficulty_menu()
        else:
            # No display available, use default size
            self.menu_result = 7  # Default to 7x7

        if self.menu_result is None:
            self.destroy()
            return

        self.grid_size = self.menu_result
        self.game = GalaxiesGame(n=self.grid_size)

        self.cell = 40 if self.grid_size >= 15 else (50 if self.grid_size >= 10 else 60)
        self.margin = 30
        self.wall_w = 5
        self.grid_w = 1
        self.dot_r = 7 if self.grid_size >= 15 else 9
        self.snap_tol = 0.25
        self.arrow_len = 14

        n = self.game.N
        w = self.margin * 2 + self.cell * n
        h = self.margin * 2 + self.cell * n

        self.canvas = tk.Canvas(self, width=w, height=h, bg="#d8d8d8", highlightthickness=0)
        self.canvas.grid(row=0, column=0, columnspan=8, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<B3-Motion>", self.on_arrow_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_arrow_release)

        self.dragging_arrow = None
        self._drag_start_cell = None

        self.status = tk.StringVar(value=f"Difficulty: {self.grid_size}x{self.grid_size}")
        tk.Label(self, textvariable=self.status, anchor="w").grid(row=1, column=0, columnspan=8, sticky="we", padx=10)

        tk.Button(self, text="New Game", command=self.on_new_game).grid(row=2, column=0, padx=5, pady=8, sticky="we")
        tk.Button(self, text="Difficulty", command=self.on_change_difficulty).grid(row=2, column=1, padx=5, pady=8, sticky="we")
        tk.Button(self, text="Restart", command=self.on_restart).grid(row=2, column=2, padx=5, pady=8, sticky="we")
        tk.Button(self, text="Undo", command=self.on_undo).grid(row=2, column=3, padx=5, pady=8, sticky="we")
        tk.Button(self, text="Redo", command=self.on_redo).grid(row=2, column=4, padx=5, pady=8, sticky="we")
        tk.Button(self, text="Hint", command=self.on_hint).grid(row=2, column=5, padx=5, pady=8, sticky="we")
        tk.Button(self, text="Solve", command=self.on_solve, bg="orange", fg="black").grid(row=2, column=6, padx=5, pady=8, sticky="we")
        tk.Button(self, text="Quit", command=self.destroy).grid(row=2, column=7, padx=5, pady=8, sticky="we")

        self.redraw()

    def show_difficulty_menu(self):
        menu_window = tk.Toplevel(self)
        menu_window.title("Select Difficulty")
        menu_window.geometry("300x280")
        menu_window.grab_set()

        selected = tk.IntVar(value=4)

        tk.Label(menu_window, text="Select Puzzle Size:", font=("Arial", 12, "bold")).pack(pady=10)

        for label, val in [("4×4  (Easy)", 4), ("7×7  (Normal)", 7), ("10×10  (Hard)", 10), ("15×15  (Expert)", 15)]:
            tk.Radiobutton(menu_window, text=label, variable=selected, value=val).pack(anchor="w", padx=50)

        self.menu_result = None

        def start_game():
            self.menu_result = selected.get()
            menu_window.destroy()

        def cancel():
            self.menu_result = None
            menu_window.destroy()

        btn_frame = tk.Frame(menu_window)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Start Game", command=start_game, bg="green", fg="white", width=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=cancel, width=8).pack(side="left", padx=5)

        menu_window.protocol("WM_DELETE_WINDOW", cancel)
        menu_window.wait_window()
        return self.menu_result

    def on_change_difficulty(self):
        old = self.grid_size
        self.show_difficulty_menu()
        if self.menu_result is not None:
            self.grid_size = self.menu_result
            self.game = GalaxiesGame(n=self.grid_size)
            self.cell = 40 if self.grid_size >= 15 else (50 if self.grid_size >= 10 else 60)
            self.dot_r = 7 if self.grid_size >= 15 else 9

            n = self.game.N
            w = self.margin * 2 + self.cell * n
            h = self.margin * 2 + self.cell * n
            self.canvas.config(width=w, height=h)
            self.redraw()

    def gx(self, x):
        return self.margin + x * self.cell

    def gy(self, y):
        return self.margin + y * self.cell

    def redraw(self):
        self.canvas.delete("all")
        n = self.game.N

        # Draw valid (correctly solved) regions in light blue
        valid_cells = self.game.get_valid_regions()
        for cell_id in valid_cells:
            x, y = cell_id % n, cell_id // n
            x0, y0 = self.gx(x), self.gy(y)
            x1, y1 = self.gx(x + 1), self.gy(y + 1)
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="#b0e0ff", outline="", tags="valid_region")

        # Draw grid lines
        for i in my_range(n + 1):
            x = self.gx(i)
            self.canvas.create_line(x, self.gy(0), x, self.gy(n), width=self.grid_w, fill="#9a9a9a")
            y = self.gy(i)
            self.canvas.create_line(self.gx(0), y, self.gx(n), y, width=self.grid_w, fill="#9a9a9a")

        # Draw dots
        for dot_idx, (dx, dy) in my_enumerate(self.game.puzzle.dots):
            cx = self.gx(dx)
            cy = self.gy(dy)
            self.canvas.create_oval(
                cx - self.dot_r, cy - self.dot_r,
                cx + self.dot_r, cy + self.dot_r,
                outline="black", width=2, fill="white", tags=f"dot_{dot_idx}"
            )

        # Draw arrows
        for arrow_idx, arrow in my_enumerate(self.game.arrows):
            cell_cx = self.gx(arrow.cell_x + 0.5)
            cell_cy = self.gy(arrow.cell_y + 0.5)
            dot_x, dot_y = self.game.puzzle.dots[arrow.dot_idx]
            dot_cx = self.gx(dot_x)
            dot_cy = self.gy(dot_y)

            ddx = dot_cx - cell_cx
            ddy = dot_cy - cell_cy
            dist = (ddx**2 + ddy**2) ** 0.5
            if dist > 0:
                ddx /= dist
                ddy /= dist
                end_x = cell_cx + ddx * self.arrow_len
                end_y = cell_cy + ddy * self.arrow_len
                self.canvas.create_line(
                    cell_cx, cell_cy, end_x, end_y,
                    width=2, fill="green", arrow="last", tags=f"arrow_{arrow_idx}"
                )

        # Draw placed walls
        for (t, x, y) in my_sorted(self.game.edges):
            if t == 'h':
                x0, y0 = self.gx(x), self.gy(y)
                x1, y1 = self.gx(x + 1), self.gy(y)
            else:
                x0, y0 = self.gx(x), self.gy(y)
                x1, y1 = self.gx(x), self.gy(y + 1)
            self.canvas.create_line(x0, y0, x1, y1, width=self.wall_w, fill="black", capstyle=tk.ROUND)

        # Draw outer border
        self.canvas.create_rectangle(
            self.gx(0), self.gy(0), self.gx(n), self.gy(n),
            outline="black", width=8
        )


        # Update status
        adj = self.game.cell_adj_graph()
        comps = bfs_components(adj, n * n)
        valid_count = my_len(valid_cells)
        total_regions = my_len(self.game.puzzle.dots)
        lines_placed = my_len(self.game.edges - self.game.fixed)
        msg = f"Lines: {lines_placed}  |  Regions: {my_len(comps)}  |  Valid: {valid_count}/{total_regions}"
        self.status.set(msg)

    def edge_from_click(self, px, py):
        n = self.game.N
        gx = (px - self.margin) / self.cell
        gy = (py - self.margin) / self.cell
        if gx < -0.2 or gy < -0.2 or gx > n + 0.2 or gy > n + 0.2:
            return None

        rx, ry = my_round(gx), my_round(gy)
        dx, dy = my_abs(gx - rx), my_abs(gy - ry)

        if min(dx, dy) > self.snap_tol:
            return None

        if dx < dy:
            # Closer to a vertical line
            x = int(rx)
            y = int(gy)
            if 0 <= x <= n and 0 <= y < n:
                return ('v', x, y)
        else:
            # Closer to a horizontal line
            x = int(gx)
            y = int(ry)
            if 0 <= x < n and 0 <= y <= n:
                return ('h', x, y)
        return None

    def on_click(self, event):
        edge = self.edge_from_click(event.x, event.y)
        if edge is None:
            return

        if edge in self.game.fixed:
            return

        self.game.toggle_edge(edge, who="player")
        self.redraw()

    def on_right_click(self, event):
        """Right-click on a dot to start placing an arrow from that dot."""
        n = self.game.N
        px, py = event.x, event.y

        # Find nearest dot
        nearest_dot = None
        nearest_dist = float('inf')
        for dot_idx, (dx, dy) in my_enumerate(self.game.puzzle.dots):
            cx = self.gx(dx)
            cy = self.gy(dy)
            dist = ((px - cx)**2 + (py - cy)**2) ** 0.5
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_dot = dot_idx

        # Only proceed if clicked reasonably close to a dot
        if nearest_dot is None or nearest_dist > self.dot_r * 2.5:
            return

        # Store the dot we're dragging from
        self.dragging_arrow = nearest_dot
        self._drag_start_cell = None

    def on_arrow_drag(self, event):
        """While dragging from a dot, show which cell the arrow would point to."""
        if self.dragging_arrow is None:
            return

        n = self.game.N
        px, py = event.x, event.y
        gx = (px - self.margin) / self.cell
        gy = (py - self.margin) / self.cell
        cell_x = int(gx)
        cell_y = int(gy)

        if 0 <= cell_x < n and 0 <= cell_y < n:
            self._drag_start_cell = (cell_x, cell_y)
        else:
            self._drag_start_cell = None

    def on_arrow_release(self, event):
        """On release, place or remove an arrow."""
        if self.dragging_arrow is None:
            return

        n = self.game.N
        px, py = event.x, event.y
        gx = (px - self.margin) / self.cell
        gy = (py - self.margin) / self.cell
        cell_x = int(gx)
        cell_y = int(gy)

        dot_idx = self.dragging_arrow
        self.dragging_arrow = None
        self._drag_start_cell = None

        if 0 <= cell_x < n and 0 <= cell_y < n:
            # Toggle: if arrow already exists at this cell pointing to same dot, remove it
            for i, arrow in my_enumerate(self.game.arrows):
                if arrow.cell_x == cell_x and arrow.cell_y == cell_y:
                    if arrow.dot_idx == dot_idx:
                        # Remove it
                        self.game.arrows = [a for a in self.game.arrows if not (a.cell_x == cell_x and a.cell_y == cell_y and a.dot_idx == dot_idx)]
                    else:
                        # Update to new dot
                        self.game.arrows[i] = Arrow(cell_x, cell_y, dot_idx)
                    self.redraw()
                    return
            # Add new arrow
            self.game.arrows.append(Arrow(cell_x, cell_y, dot_idx))
        else:
            # Dropped outside grid: remove any arrow at drag start cell
            if self._drag_start_cell:
                cx, cy = self._drag_start_cell
                self.game.arrows = [a for a in self.game.arrows if not (a.cell_x == cx and a.cell_y == cy)]

        self.redraw()

    def on_new_game(self):
        self.game.new_puzzle()
        self.redraw()

    def on_restart(self):
        self.game.reset()
        self.redraw()

    def on_solve(self):
        self.game.edges = set(self.game.fixed) | set(self.game.solution)
        self.redraw()

    def on_hint(self):
        if not self.game.is_solved():
            result = self.game.computer_move_dc()
            if result:
                self.redraw()

    def on_undo(self):
        if self.game.undo():
            self.redraw()

    def on_redo(self):
        if self.game.redo():
            self.redraw()


if __name__ == "__main__":
    GalaxiesUI().mainloop()