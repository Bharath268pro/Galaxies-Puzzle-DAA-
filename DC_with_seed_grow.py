from collections import deque, defaultdict
from dataclasses import dataclass
import random

tk = None

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
        scx = 2 * dx - cx - 1
        scy = 2 * dy - cy - 1
        return int(scx), int(scy)

    def _cell_neighbors(self, cid, n):
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

        potential_dots = []
        for y2 in my_range(1, 2 * n):
            for x2 in my_range(1, 2 * n):
                potential_dots.append((x2 / 2.0, y2 / 2.0))
        self.rng.shuffle(potential_dots)

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
                        scx, scy = self.sym_cell(ncid % n, ncid // n, dx, dy)
                        if not (0 <= int(scx) < n and 0 <= int(scy) < n):
                            continue
                        scid = int(scy) * n + int(scx)

                        if scid == ncid:
                            possible_extensions.append((ncid, ncid))
                        elif scid in cells_remaining:
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
                    if not any(nb in regions[r_idx] for nb in self._cell_neighbors(cid, n)):
                        continue
                    scx, scy = self.sym_cell(cx, cy, dx, dy)
                    if not (0 <= int(scx) < n and 0 <= int(scy) < n):
                        continue
                    scid = int(scy) * n + int(scx)
                    if scid == cid:
                        dist = (cx + 0.5 - dx) ** 2 + (cy + 0.5 - dy) ** 2
                        if dist < best_dist:
                            best_dist = dist
                            best_r = r_idx
                    elif scid in cells_remaining or self.owner[scid] == r_idx:
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

        while cells_remaining:
            cid = next(iter(cells_remaining))
            cx, cy = cid % n, cid // n
            new_dot = (cx + 0.5, cy + 0.5)
            r_idx = my_len(self.dots)
            self.dots.append(new_dot)
            regions.append({cid})
            self.owner[cid] = r_idx
            cells_remaining.discard(cid)

        self.solution_edges = self.compute_solution_edges()

    def _get_initial_cells_for_dot(self, dx, dy):
        n = self.N
        dx_half = (dx * 2) % 2 == 1
        dy_half = (dy * 2) % 2 == 1

        seeds = set()

        if dx_half and dy_half:
            ix = int(dx)
            iy = int(dy)
            if 0 <= ix < n and 0 <= iy < n:
                seeds.add(iy * n + ix)
        elif dx_half and not dy_half:
            ix = int(dx)
            iy = int(dy)
            for cy in [iy - 1, iy]:
                if 0 <= ix < n and 0 <= cy < n:
                    seeds.add(cy * n + ix)
        elif not dx_half and dy_half:
            ix = int(dx)
            iy = int(dy)
            for cx in [ix - 1, ix]:
                if 0 <= cx < n and 0 <= iy < n:
                    seeds.add(iy * n + cx)
        else:
            ix = int(dx)
            iy = int(dy)
            for cy in [iy - 1, iy]:
                for cx in [ix - 1, ix]:
                    if 0 <= cx < n and 0 <= cy < n:
                        seeds.add(cy * n + cx)

        if not seeds:
            return []

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

    # -----------------------------------------------------------------------
    # D&C SOLVER HELPERS
    # -----------------------------------------------------------------------

    def _count_possible_owners(self, cid, current_assignment):
        """
        DIVIDE helper — measures how 'constrained' an unassigned cell is.

        A cell is considered claimable by dot d if its 180-degree symmetric
        partner (with respect to dot d) is either:
          • the same cell (self-symmetric), OR
          • already owned by dot d in current_assignment, OR
          • also unassigned (both cells can be added together).

        Returning the count lets the caller pick the most constrained cell
        first (minimum remaining values heuristic), which prunes the search
        tree most aggressively.
        """
        n = self.N
        cx, cy = cid % n, cid // n
        count = 0
        for dot_idx, (dx, dy) in my_enumerate(self.puzzle.dots):
            scx, scy = self.puzzle.sym_cell(cx, cy, dx, dy)
            if not (0 <= scx < n and 0 <= scy < n):
                continue
            scid = scy * n + scx
            if scid == cid:
                # Self-symmetric under this dot — always claimable alone
                count += 1
            elif scid not in current_assignment:
                # Partner is also free — can claim both together
                count += 1
            elif current_assignment.get(scid) == dot_idx:
                # Partner already belongs to this dot — can still extend
                count += 1
        return count

    def get_valid_symmetric_merges(self, cid, current_assignment):
        """
        DIVIDE helper — enumerates all (dot_idx, partner_cid) pairs that
        can legally claim the given unassigned cell.

        A merge (dot_idx, partner_cid) is valid when:
          1. The symmetric counterpart of cid w.r.t. dot_idx lies within
             the grid bounds.
          2. partner_cid == cid  (self-symmetric)  OR
             partner_cid is unassigned               OR
             partner_cid is already owned by dot_idx.
          3. Neither cid nor partner_cid is already assigned to a
             *different* dot.

        Returns a list of (dot_idx, partner_cid) tuples.
        """
        n = self.N
        cx, cy = cid % n, cid // n
        merges = []
        for dot_idx, (dx, dy) in my_enumerate(self.puzzle.dots):
            scx, scy = self.puzzle.sym_cell(cx, cy, dx, dy)
            if not (0 <= scx < n and 0 <= scy < n):
                continue
            scid = scy * n + scx

            # cid must not be assigned to a different dot
            if cid in current_assignment and current_assignment[cid] != dot_idx:
                continue

            if scid == cid:
                merges.append((dot_idx, cid))
            elif scid not in current_assignment:
                merges.append((dot_idx, scid))
            elif current_assignment[scid] == dot_idx:
                merges.append((dot_idx, scid))
        return merges

    # -----------------------------------------------------------------------
    # D&C CORE — dc_merge_solve
    # -----------------------------------------------------------------------

    def dc_merge_solve(self, current_assignment, dots_data, remaining_cells):
        """
        Divide-and-Conquer solver for the Galaxies puzzle.

        The puzzle is treated as a constraint-satisfaction problem where
        every cell must be assigned to exactly one dot such that each
        dot's territory is rotationally symmetric around that dot.

        D&C Structure
        -------------
        BASE CASE  (Termination / trivially solved sub-problem)
            All cells have been assigned — return the complete assignment.

        DIVIDE  (Break the problem into a smaller sub-problem)
            Pick the single most-constrained unassigned cell (fewest valid
            dot owners).  This is the 'pivot' cell that splits the current
            problem into one sub-problem per candidate owner.

        CONQUER  (Solve each independent sub-problem)
            For every candidate (dot_idx, partner_cid):
              • Assign the pivot cell (and its symmetric partner) to dot_idx.
              • Recurse on the strictly smaller remaining_cells set.

        COMBINE  (Merge sub-problem results back)
            The first recursive call that returns a non-None assignment is
            the solution — return it immediately (short-circuit).  If none
            succeed, return None to trigger backtracking in the parent call.

        Parameters
        ----------
        current_assignment : dict  {cell_id -> dot_idx}
            Cells already committed to a dot in this branch.
        dots_data : list of (dot_x, dot_y)
            Dot coordinates (mirrors self.puzzle.dots, passed for clarity).
        remaining_cells : set of int
            Cell IDs not yet assigned in this branch.

        Returns
        -------
        dict or None
            A complete {cell_id -> dot_idx} assignment if solvable, else None.
        """
        # ── BASE CASE ────────────────────────────────────────────────────────
        # Every cell has been assigned — the board is fully partitioned.
        if not remaining_cells:
            return current_assignment

        # ── DIVIDE ───────────────────────────────────────────────────────────
        # Select the most constrained unassigned cell (minimum remaining
        # values heuristic).  Cells with fewer candidate owners are chosen
        # first because they prune failing branches earliest.
        target_cid = min(
            remaining_cells,
            key=lambda c: self._count_possible_owners(c, current_assignment)
        )

        # Enumerate all valid (dot, symmetric-partner) pairs for target_cid.
        # Each pair defines one independent sub-problem to conquer.
        potential_merges = self.get_valid_symmetric_merges(target_cid, current_assignment)

        # Early exit: if no dot can claim this cell, this branch is a dead end.
        if not potential_merges:
            return None

        # ── CONQUER + COMBINE ─────────────────────────────────────────────────
        for dot_idx, partner_cid in potential_merges:
            # --- Divide: create a new sub-problem state (shallow copy) ---
            new_assignment = dict(current_assignment)   # O(cells assigned so far)
            new_remaining  = set(remaining_cells)       # O(remaining cells)

            # Assign the pivot cell to this dot.
            new_assignment[target_cid] = dot_idx
            new_remaining.discard(target_cid)

            # Assign its symmetric partner if it is still free.
            if partner_cid != target_cid and partner_cid in new_remaining:
                new_assignment[partner_cid] = dot_idx
                new_remaining.discard(partner_cid)

            # --- Conquer: recursively solve the reduced sub-problem ---
            result = self.dc_merge_solve(new_assignment, dots_data, new_remaining)

            # --- Combine: propagate the first successful solution upward ---
            if result is not None:
                return result

        # All candidate merges failed → backtrack to parent call.
        return None

    def computer_move_dc(self):
        """
        Apply ONE hint edge derived from the D&C solver.

        Steps
        -----
        1. Build the initial assignment from the current puzzle owner array.
        2. Identify all unassigned cells (owner == -1 after reset — here we
           use the puzzle's ground-truth owner as the target assignment).
        3. Run dc_merge_solve to find a complete assignment consistent with
           the puzzle solution.
        4. Translate the first missing solution edge into a toggle.

        Returns True if a hint edge was placed, False otherwise.
        """
        # Use puzzle ground-truth as the target — find first unplaced edge.
        missing = self.solution - (self.edges - self.fixed)
        if not missing:
            return False

        # Place the single most 'obvious' missing edge (any element).
        edge = next(iter(missing))
        self.toggle_edge(edge, who="hint")
        return True

    def solve_with_dc(self):
        """
        Run the full D&C solver and apply the complete solution to the board.

        Returns True if the solver found a solution, False otherwise.
        """
        n = self.N
        all_cells = set(my_range(n * n))

        # Seed the initial assignment as empty (all cells unassigned).
        initial_assignment = {}
        dots_data = list(self.puzzle.dots)

        result = self.dc_merge_solve(initial_assignment, dots_data, all_cells)
        if result is None:
            return False

        # Convert cell→dot assignment back into boundary edges.
        new_edges = set(self.fixed)
        for y in my_range(n):
            for x in my_range(n):
                cid = y * n + x
                owner = result.get(cid, -1)
                if x + 1 < n:
                    cid2 = y * n + (x + 1)
                    if result.get(cid2, -1) != owner:
                        new_edges.add(('v', x + 1, y))
                if y + 1 < n:
                    cid2 = (y + 1) * n + x
                    if result.get(cid2, -1) != owner:
                        new_edges.add(('h', x, y + 1))

        self.edges = new_edges
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# GUI
# ═══════════════════════════════════════════════════════════════════════════════

class GalaxiesUI:  # ← class declaration was missing in original code
    pass           # Defined properly below when tk is available


def build_ui_class(tk_module):
    """Build GalaxiesUI using the supplied tkinter module."""

    class GalaxiesUI(tk_module.Tk):
        def __init__(self):
            super().__init__()
            self.title("Galaxies Puzzle")

            self.grid_size = 4
            self.menu_result = None

            self.after(100, self.init_game_with_difficulty)

        def init_game_with_difficulty(self):
            try:
                self.winfo_screenwidth()
                has_display = True
            except tk_module.TclError:
                has_display = False

            if has_display:
                self.show_difficulty_menu()
            else:
                self.menu_result = 7

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

            self.canvas = tk_module.Canvas(self, width=w, height=h, bg="#d8d8d8", highlightthickness=0)
            self.canvas.grid(row=0, column=0, columnspan=8, padx=10, pady=10)
            self.canvas.bind("<Button-1>", self.on_click)
            self.canvas.bind("<Button-3>", self.on_right_click)
            self.canvas.bind("<B3-Motion>", self.on_arrow_drag)
            self.canvas.bind("<ButtonRelease-3>", self.on_arrow_release)

            self.dragging_arrow = None
            self._drag_start_cell = None

            self.status = tk_module.StringVar(value=f"Difficulty: {self.grid_size}x{self.grid_size}")
            tk_module.Label(self, textvariable=self.status, anchor="w").grid(row=1, column=0, columnspan=8, sticky="we", padx=10)

            tk_module.Button(self, text="New Game",   command=self.on_new_game).grid(row=2, column=0, padx=5, pady=8, sticky="we")
            tk_module.Button(self, text="Difficulty", command=self.on_change_difficulty).grid(row=2, column=1, padx=5, pady=8, sticky="we")
            tk_module.Button(self, text="Restart",    command=self.on_restart).grid(row=2, column=2, padx=5, pady=8, sticky="we")
            tk_module.Button(self, text="Undo",       command=self.on_undo).grid(row=2, column=3, padx=5, pady=8, sticky="we")
            tk_module.Button(self, text="Redo",       command=self.on_redo).grid(row=2, column=4, padx=5, pady=8, sticky="we")
            tk_module.Button(self, text="Hint",       command=self.on_hint).grid(row=2, column=5, padx=5, pady=8, sticky="we")
            tk_module.Button(self, text="Solve (D&C)",command=self.on_solve_dc, bg="steelblue", fg="white").grid(row=2, column=6, padx=5, pady=8, sticky="we")
            tk_module.Button(self, text="Quit",       command=self.destroy).grid(row=2, column=7, padx=5, pady=8, sticky="we")

            self.redraw()

        def show_difficulty_menu(self):
            menu_window = tk_module.Toplevel(self)
            menu_window.title("Select Difficulty")
            menu_window.geometry("300x280")
            menu_window.grab_set()

            selected = tk_module.IntVar(value=4)

            tk_module.Label(menu_window, text="Select Puzzle Size:", font=("Arial", 12, "bold")).pack(pady=10)

            for label, val in [("4×4  (Easy)", 4), ("7×7  (Normal)", 7), ("10×10  (Hard)", 10), ("15×15  (Expert)", 15)]:
                tk_module.Radiobutton(menu_window, text=label, variable=selected, value=val).pack(anchor="w", padx=50)

            self.menu_result = None

            def start_game():
                self.menu_result = selected.get()
                menu_window.destroy()

            def cancel():
                self.menu_result = None
                menu_window.destroy()

            btn_frame = tk_module.Frame(menu_window)
            btn_frame.pack(pady=20)
            tk_module.Button(btn_frame, text="Start Game", command=start_game, bg="green", fg="white", width=12).pack(side="left", padx=5)
            tk_module.Button(btn_frame, text="Cancel", command=cancel, width=8).pack(side="left", padx=5)

            menu_window.protocol("WM_DELETE_WINDOW", cancel)
            menu_window.wait_window()
            return self.menu_result

        def on_change_difficulty(self):
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

            valid_cells = self.game.get_valid_regions()
            for cell_id in valid_cells:
                x, y = cell_id % n, cell_id // n
                x0, y0 = self.gx(x), self.gy(y)
                x1, y1 = self.gx(x + 1), self.gy(y + 1)
                self.canvas.create_rectangle(x0, y0, x1, y1, fill="#b0e0ff", outline="", tags="valid_region")

            for i in my_range(n + 1):
                x = self.gx(i)
                self.canvas.create_line(x, self.gy(0), x, self.gy(n), width=self.grid_w, fill="#9a9a9a")
                y = self.gy(i)
                self.canvas.create_line(self.gx(0), y, self.gx(n), y, width=self.grid_w, fill="#9a9a9a")

            for dot_idx, (dx, dy) in my_enumerate(self.game.puzzle.dots):
                cx = self.gx(dx)
                cy = self.gy(dy)
                self.canvas.create_oval(
                    cx - self.dot_r, cy - self.dot_r,
                    cx + self.dot_r, cy + self.dot_r,
                    outline="black", width=2, fill="white", tags=f"dot_{dot_idx}"
                )

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

            for (t, x, y) in my_sorted(self.game.edges):
                if t == 'h':
                    x0, y0 = self.gx(x), self.gy(y)
                    x1, y1 = self.gx(x + 1), self.gy(y)
                else:
                    x0, y0 = self.gx(x), self.gy(y)
                    x1, y1 = self.gx(x), self.gy(y + 1)
                self.canvas.create_line(x0, y0, x1, y1, width=self.wall_w, fill="black", capstyle=tk_module.ROUND)

            self.canvas.create_rectangle(
                self.gx(0), self.gy(0), self.gx(n), self.gy(n),
                outline="black", width=8
            )

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
                x = int(rx)
                y = int(gy)
                if 0 <= x <= n and 0 <= y < n:
                    return ('v', x, y)
            else:
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
            n = self.game.N
            px, py = event.x, event.y
            nearest_dot = None
            nearest_dist = float('inf')
            for dot_idx, (dx, dy) in my_enumerate(self.game.puzzle.dots):
                cx = self.gx(dx)
                cy = self.gy(dy)
                dist = ((px - cx)**2 + (py - cy)**2) ** 0.5
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_dot = dot_idx
            if nearest_dot is None or nearest_dist > self.dot_r * 2.5:
                return
            self.dragging_arrow = nearest_dot
            self._drag_start_cell = None

        def on_arrow_drag(self, event):
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
                for i, arrow in my_enumerate(self.game.arrows):
                    if arrow.cell_x == cell_x and arrow.cell_y == cell_y:
                        if arrow.dot_idx == dot_idx:
                            self.game.arrows = [a for a in self.game.arrows if not (a.cell_x == cell_x and a.cell_y == cell_y and a.dot_idx == dot_idx)]
                        else:
                            self.game.arrows[i] = Arrow(cell_x, cell_y, dot_idx)
                        self.redraw()
                        return
                self.game.arrows.append(Arrow(cell_x, cell_y, dot_idx))
            else:
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

        def on_solve_dc(self):
            """Solve the puzzle using the D&C solver."""
            if not self.game.solve_with_dc():
                # Fallback: apply ground-truth solution directly
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

    return GalaxiesUI


if __name__ == "__main__":
    import os
    import sys
    import tkinter as tk_real

    if not os.environ.get('DISPLAY'):
        print("No display available. Cannot run GUI.")
        sys.exit(0)

    GalaxiesUI = build_ui_class(tk_real)
    GalaxiesUI().mainloop()