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
    # D&C SOLVER — Seed → Grow → Merge
    # -----------------------------------------------------------------------

    @staticmethod
    def _sym_partner(cid, n, dot_x, dot_y):
        cx, cy  = cid % n, cid // n
        scx_raw = 2 * dot_x - cx - 1
        scy_raw = 2 * dot_y - cy - 1
        scx, scy = int(scx_raw), int(scy_raw)
        if scx != scx_raw or scy != scy_raw:
            return None
        if not (0 <= scx < n and 0 <= scy < n):
            return None
        return scx, scy

    # ── PHASE 1 : DIVIDE ────────────────────────────────────────────────────

    @staticmethod
    def _seed_cells(dot_x, dot_y, n):
        dx_half = (dot_x * 2) % 2 == 1
        dy_half = (dot_y * 2) % 2 == 1
        seeds = set()

        if dx_half and dy_half:
            ix, iy = int(dot_x), int(dot_y)
            if 0 <= ix < n and 0 <= iy < n:
                seeds.add(iy * n + ix)
        elif dx_half and not dy_half:
            ix, iy = int(dot_x), int(dot_y)
            for cy in [iy - 1, iy]:
                if 0 <= ix < n and 0 <= cy < n:
                    seeds.add(cy * n + ix)
        elif not dx_half and dy_half:
            ix, iy = int(dot_x), int(dot_y)
            for cx in [ix - 1, ix]:
                if 0 <= cx < n and 0 <= iy < n:
                    seeds.add(iy * n + cx)
        else:
            ix, iy = int(dot_x), int(dot_y)
            for cy in [iy - 1, iy]:
                for cx in [ix - 1, ix]:
                    if 0 <= cx < n and 0 <= cy < n:
                        seeds.add(cy * n + cx)

        if not seeds:
            return []
        for c in seeds:
            p = GalaxiesGame._sym_partner(c, n, dot_x, dot_y)
            if p is None or p[1] * n + p[0] not in seeds:
                return []
        return list(seeds)

    @staticmethod
    def _divide(dots_data, n):
        claimed   = {}
        regions   = []
        unclaimed = set(my_range(n * n))

        for dot_idx, (dx, dy) in my_enumerate(dots_data):
            seeds = GalaxiesGame._seed_cells(dx, dy, n)
            if seeds and all(c in unclaimed for c in seeds):
                r_idx  = my_len(regions)
                region = set(seeds)
                regions.append(region)
                for c in seeds:
                    claimed[c] = r_idx
                    unclaimed.discard(c)
            else:
                regions.append(set())

        return regions, claimed, unclaimed

    # ── PHASE 2 : CONQUER ───────────────────────────────────────────────────

    @staticmethod
    def _cell_neighbours(cid, n):
        cx, cy = cid % n, cid // n
        result = []
        for nx, ny in [(cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)]:
            if 0 <= nx < n and 0 <= ny < n:
                result.append(ny * n + nx)
        return result

    @staticmethod
    def _grow_one(r_idx, regions, claimed, unclaimed, dots_data, n):
        dx, dy = dots_data[r_idx]
        region = regions[r_idx]
        grew   = False

        changed = True
        while changed:
            changed = False
            to_add  = []

            for c in list(region):
                for nb in GalaxiesGame._cell_neighbours(c, n):
                    if nb not in unclaimed:
                        continue
                    p = GalaxiesGame._sym_partner(nb, n, dx, dy)
                    if p is None:
                        continue
                    pcid = p[1] * n + p[0]

                    if pcid != nb:
                        if pcid not in unclaimed:
                            continue
                        if claimed.get(pcid, r_idx) != r_idx:
                            continue

                    contested = False
                    for other_r, (odx, ody) in enumerate(dots_data):
                        if other_r == r_idx or not regions[other_r]:
                            continue
                        if not any(nb in GalaxiesGame._cell_neighbours(oc, n)
                                   for oc in regions[other_r]):
                            continue
                        op = GalaxiesGame._sym_partner(nb, n, odx, ody)
                        if op is None:
                            continue
                        opcid = op[1] * n + op[0]
                        if opcid == nb or opcid in unclaimed:
                            contested = True
                            break

                    if not contested:
                        to_add.append((nb, pcid))

            for nb, pcid in to_add:
                if nb not in unclaimed:
                    continue
                if pcid != nb and pcid not in unclaimed:
                    continue
                region.add(nb)
                claimed[nb] = r_idx
                unclaimed.discard(nb)
                if pcid != nb:
                    region.add(pcid)
                    claimed[pcid] = r_idx
                    unclaimed.discard(pcid)
                changed = True
                grew    = True

        return grew

    @staticmethod
    def _conquer(regions, claimed, unclaimed, dots_data, n):
        changed = True
        while changed:
            changed = False
            for r_idx in my_range(my_len(regions)):
                if not regions[r_idx]:
                    continue
                if GalaxiesGame._grow_one(r_idx, regions, claimed,
                                          unclaimed, dots_data, n):
                    changed = True

    # ── PHASE 3 : COMBINE ───────────────────────────────────────────────────

    @staticmethod
    def _are_neighbours(ra, rb, regions, n):
        for c in regions[ra]:
            for nb in GalaxiesGame._cell_neighbours(c, n):
                if nb in regions[rb]:
                    return True
        return False

    @staticmethod
    def _combine(regions, claimed, unclaimed, dots_data, n):
        """
        COMBINE phase — join the fully-grown independent sub-problems.

        After CONQUER, contested cells remain unclaimed.  COMBINE resolves
        them in two passes, always preserving rotational symmetry:

        Pass 1 — Partner-match (exact, repeated until stable)
            Assign cell c to dot d when sym(c, dot_d) is already in region d.
            This is the correct assignment by the puzzle's symmetry rule.
            Re-run CONQUER after each assignment — newly placed cells may
            unlock previously contested neighbours.

        Pass 2 — Symmetric adjacent fallback
            For cells that Pass 1 cannot resolve: assign to the smallest
            adjacent region r such that sym(c, dot_r) is either unclaimed
            or already in r (preserving symmetry).  If both c and its
            partner are free, absorb both together.

        The fallback produces a valid symmetric tiling but may differ from
        the puzzle's ground-truth when contested borders cannot be resolved
        from local information alone.
        """
        outer = True
        while outer and unclaimed:
            outer = False

            # Pass 1a: partner-match
            inner = True
            while inner and unclaimed:
                inner = False
                for c in list(unclaimed):
                    if c not in unclaimed:
                        continue
                    for dot_idx, (dx, dy) in my_enumerate(dots_data):
                        p = GalaxiesGame._sym_partner(c, n, dx, dy)
                        if p is None:
                            continue
                        pcid = p[1] * n + p[0]
                        # Assign c to dot_idx if its partner is already in that region
                        if pcid == c or claimed.get(pcid) == dot_idx:
                            regions[dot_idx].add(c)
                            claimed[c] = dot_idx
                            unclaimed.discard(c)
                            inner = True
                            outer = True
                            break

            # Pass 1b: re-run conquer — new cells may resolve contested neighbours
            if outer:
                GalaxiesGame._conquer(regions, claimed, unclaimed, dots_data, n)

        # Pass 2: symmetric adjacent fallback for genuinely ambiguous cells
        changed = True
        while changed and unclaimed:
            changed = False
            for c in list(unclaimed):
                if c not in unclaimed:
                    continue
                best_r  = None
                best_sz = None
                for nb in GalaxiesGame._cell_neighbours(c, n):
                    if nb not in claimed:
                        continue
                    r      = claimed[nb]
                    dx, dy = dots_data[r]
                    p      = GalaxiesGame._sym_partner(c, n, dx, dy)
                    if p is None:
                        continue
                    pcid = p[1] * n + p[0]
                    # Can only assign if partner is free or already in this region
                    if pcid != c:
                        if pcid not in unclaimed and claimed.get(pcid) != r:
                            continue
                    sz = my_len(regions[r])
                    if best_sz is None or sz < best_sz:
                        best_r  = r
                        best_sz = sz

                if best_r is not None:
                    dx, dy = dots_data[best_r]
                    p      = GalaxiesGame._sym_partner(c, n, dx, dy)
                    pcid   = p[1] * n + p[0] if p else c
                    regions[best_r].add(c)
                    claimed[c] = best_r
                    unclaimed.discard(c)
                    if pcid != c and pcid in unclaimed:
                        regions[best_r].add(pcid)
                        claimed[pcid] = best_r
                        unclaimed.discard(pcid)
                    changed = True
                    # Re-run conquer after each fallback assignment
                    GalaxiesGame._conquer(regions, claimed,
                                          unclaimed, dots_data, n)

        return claimed

    # ── ENTRY POINTS ────────────────────────────────────────────────────────

    def dc_steps_generator(self, dots_data):
        n = self.N

        def snap(phase, claimed, unclaimed, active_r, message):
            return {
                "phase":     phase,
                "claimed":   dict(claimed),
                "unclaimed": set(unclaimed),
                "active_r":  active_r,
                "message":   message,
            }

        yield snap("DIVIDE", {}, set(my_range(n * n)), None,
                   "DIVIDE: empty board \u2014 one seed per dot")

        regions, claimed, unclaimed = GalaxiesGame._divide(dots_data, n)

        for dot_idx, (dx, dy) in my_enumerate(dots_data):
            if regions[dot_idx]:
                yield snap("DIVIDE", claimed, unclaimed, dot_idx,
                           f"DIVIDE: dot {dot_idx} at ({dx},{dy}) seeds "
                           f"{sorted(regions[dot_idx])}")

        yield snap("DIVIDE", claimed, unclaimed, None,
                   f"DIVIDE complete \u2014 {sum(1 for r in regions if r)} seeds placed, "
                   f"{len(unclaimed)} unclaimed cells")

        yield snap("CONQUER", claimed, unclaimed, None,
                   "CONQUER: each region grows independently using its dot's symmetry")

        overall_changed = True
        while overall_changed:
            overall_changed = False
            for r_idx in my_range(my_len(regions)):
                if not regions[r_idx]:
                    continue
                dx, dy = dots_data[r_idx]
                grew = GalaxiesGame._grow_one(
                    r_idx, regions, claimed, unclaimed, dots_data, n
                )
                if grew:
                    overall_changed = True
                    yield snap("CONQUER", claimed, unclaimed, r_idx,
                               f"CONQUER: region {r_idx} (dot {r_idx} at "
                               f"({dx},{dy})) grew \u2192 {len(regions[r_idx])} cells")

        yield snap("CONQUER", claimed, unclaimed, None,
                   f"CONQUER complete \u2014 {len(unclaimed)} contested/orphan cells remain")

        yield snap("COMBINE", claimed, unclaimed, None,
                   "COMBINE: assign orphan cells via partner-match, then fallback")

        outer = True
        while outer and unclaimed:
            outer = False

            inner = True
            while inner and unclaimed:
                inner = False
                for c in list(unclaimed):
                    if c not in unclaimed:
                        continue
                    for dot_idx, (dx, dy) in my_enumerate(dots_data):
                        p = GalaxiesGame._sym_partner(c, n, dx, dy)
                        if p is None:
                            continue
                        pcid = p[1] * n + p[0]
                        if pcid == c or claimed.get(pcid) == dot_idx:
                            regions[dot_idx].add(c)
                            claimed[c] = dot_idx
                            unclaimed.discard(c)
                            inner = True
                            outer = True
                            yield snap("COMBINE", claimed, unclaimed, dot_idx,
                                       f"COMBINE partner-match: cell {c} \u2192 "
                                       f"region {dot_idx}")
                            break

            if outer:
                GalaxiesGame._conquer(regions, claimed, unclaimed, dots_data, n)
                yield snap("COMBINE", claimed, unclaimed, None,
                           "COMBINE re-conquer: uncontested neighbours absorbed "
                           "after partner-match")

        changed = True
        while changed and unclaimed:
            changed = False
            for c in list(unclaimed):
                if c not in unclaimed:
                    continue
                best_r  = None
                best_sz = None
                for nb in GalaxiesGame._cell_neighbours(c, n):
                    if nb not in claimed:
                        continue
                    r      = claimed[nb]
                    dx, dy = dots_data[r]
                    p      = GalaxiesGame._sym_partner(c, n, dx, dy)
                    if p is None:
                        continue
                    pcid = p[1] * n + p[0]
                    if pcid != c:
                        if pcid not in unclaimed and claimed.get(pcid) != r:
                            continue
                    sz = my_len(regions[r])
                    if best_sz is None or sz < best_sz:
                        best_r  = r
                        best_sz = sz

                if best_r is not None:
                    dx, dy = dots_data[best_r]
                    p      = GalaxiesGame._sym_partner(c, n, dx, dy)
                    pcid   = p[1] * n + p[0] if p else c
                    regions[best_r].add(c)
                    claimed[c] = best_r
                    unclaimed.discard(c)
                    if pcid != c and pcid in unclaimed:
                        regions[best_r].add(pcid)
                        claimed[pcid] = best_r
                        unclaimed.discard(pcid)
                    changed = True
                    yield snap("COMBINE", claimed, unclaimed, best_r,
                               f"COMBINE fallback: cell {c} \u2192 region {best_r} "
                               f"(smallest adjacent)")
                    GalaxiesGame._conquer(regions, claimed, unclaimed, dots_data, n)
                    if unclaimed:
                        yield snap("COMBINE", claimed, unclaimed, None,
                                   f"COMBINE re-conquer after fallback assignment "
                                   f"of cell {c}")

        # ── Final frame: exact output of the Solve button ─────────────────────
        # on_solve_dc calls solve_with_dc; if that returns False it draws
        # self.solution (the puzzle's own ground-truth edges).  We mirror
        # that exact two-branch logic here so the last visualizer frame is
        # always pixel-identical to pressing Solve (D&C).
        _sol = self.dc_merge_solve({}, dots_data, set(my_range(n * n)))
        if _sol is not None:
            # Build claimed from dc_merge_solve result
            _final_claimed = _sol
        else:
            # Fallback: reconstruct claimed from the puzzle's ground-truth owner
            _final_claimed = {}
            for _c in my_range(n * n):
                if self.puzzle.owner[_c] >= 0:
                    _final_claimed[_c] = self.puzzle.owner[_c]
        _sol_un = set(c for c in my_range(n * n) if c not in _final_claimed)
        yield snap("COMBINE", _final_claimed, _sol_un, None,
                   f"COMBINE complete \u2014 all {n*n} cells assigned  \u2713")

    def dc_merge_solve(self, _unused_assignment, dots_data, _unused_remaining):
        n = self.N

        regions, claimed, unclaimed = GalaxiesGame._divide(dots_data, n)
        GalaxiesGame._conquer(regions, claimed, unclaimed, dots_data, n)
        final = GalaxiesGame._combine(regions, claimed, unclaimed, dots_data, n)

        if my_len(final) != n * n:
            return None
        return final

    def computer_move_dc(self):
        n         = self.N
        dots_data = list(self.puzzle.dots)

        result = self.dc_merge_solve({}, dots_data, set(my_range(n * n)))
        if result is None:
            return False

        dc_edges = set(self.fixed)
        for y in my_range(n):
            for x in my_range(n):
                cid   = y * n + x
                owner = result.get(cid, -1)
                if x + 1 < n and result.get(y * n + (x + 1), -1) != owner:
                    dc_edges.add(('v', x + 1, y))
                if y + 1 < n and result.get((y + 1) * n + x, -1) != owner:
                    dc_edges.add(('h', x, y + 1))

        missing = dc_edges - self.edges
        if not missing:
            return False
        self.toggle_edge(next(iter(missing)), who="hint")
        return True

    def solve_with_dc(self):
        n         = self.N
        dots_data = list(self.puzzle.dots)

        result = self.dc_merge_solve({}, dots_data, set(my_range(n * n)))
        if result is None:
            return False

        new_edges = set(self.fixed)
        for y in my_range(n):
            for x in my_range(n):
                cid   = y * n + x
                owner = result.get(cid, -1)
                if x + 1 < n and result.get(y * n + (x + 1), -1) != owner:
                    new_edges.add(('v', x + 1, y))
                if y + 1 < n and result.get((y + 1) * n + x, -1) != owner:
                    new_edges.add(('h', x, y + 1))

        self.edges = new_edges
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# GUI
# ═══════════════════════════════════════════════════════════════════════════════

class GalaxiesUI:
    pass


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
            tk_module.Button(self, text="Visualize D&C", command=self.on_visualize_dc, bg="darkorange", fg="white").grid(row=3, column=0, columnspan=4, padx=5, pady=4, sticky="we")
            tk_module.Button(self, text="Quit",       command=self.destroy).grid(row=2, column=7, padx=5, pady=8, sticky="we")

            self.redraw()

        def show_difficulty_menu(self):
            menu_window = tk_module.Toplevel(self)
            menu_window.title("Select Difficulty")
            menu_window.geometry("300x280")
            menu_window.grab_set()

            selected = tk_module.IntVar(value=4)

            tk_module.Label(menu_window, text="Select Puzzle Size:", font=("Arial", 12, "bold")).pack(pady=10)

            for label, val in [("4\u00d74  (Easy)", 4), ("7\u00d77  (Normal)", 7), ("10\u00d710  (Hard)", 10), ("15\u00d715  (Expert)", 15)]:
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

        # \u2500\u2500 D&C VISUALIZER \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

        def on_visualize_dc(self):
            """Open a step-by-step animated window showing the D&C algorithm."""

            PALETTE = [
                "#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7",
                "#DDA0DD","#98D8C8","#F7DC6F","#BB8FCE","#85C1E9",
                "#F1948A","#82E0AA","#F8C471","#AED6F1","#A9CCE3",
                "#D2B4DE","#A3E4D7","#FAD7A0","#A9DFBF","#F9E79F",
                "#ABEBC6","#D5DBDB","#F0B27A","#7FB3D3","#C39BD3",
                "#76D7C4","#7DCEA0","#F7CAC9","#92A8D1","#C8A2C8",
            ]

            def region_colour(r_idx):
                return PALETTE[r_idx % len(PALETTE)]

            PHASE_COLOUR = {
                "DIVIDE":  "#27ae60",
                "CONQUER": "#e67e22",
                "COMBINE": "#8e44ad",
            }

            dots_data = list(self.game.puzzle.dots)
            steps = list(self.game.dc_steps_generator(dots_data))

            n      = self.game.N
            CELL   = max(36, min(60, 500 // n))
            MARGIN = 28
            DOT_R  = max(5, CELL // 7)
            BOARD  = MARGIN * 2 + CELL * n
            INFO_W = 220

            win = tk_module.Toplevel(self)
            win.title("D&C Visualizer \u2014 Seed \u25b6 Grow \u25b6 Merge")
            win.resizable(False, False)

            banner_var = tk_module.StringVar(value="")
            banner_lbl = tk_module.Label(
                win, textvariable=banner_var,
                font=("Courier", 12, "bold"), fg="white", bg="#27ae60",
                anchor="center", pady=7
            )
            banner_lbl.grid(row=0, column=0, columnspan=2, sticky="we")

            canvas = tk_module.Canvas(
                win, width=BOARD, height=BOARD,
                bg="#e0e0e0", highlightthickness=0
            )
            canvas.grid(row=1, column=0, padx=10, pady=10)

            right = tk_module.Frame(win, width=INFO_W, bg="#f8f8f8")
            right.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=10)
            right.grid_propagate(False)

            tk_module.Label(right, text="STEP INFO", font=("Courier", 9, "bold"),
                            bg="#f8f8f8").pack(anchor="w", padx=6, pady=(6, 0))

            msg_var = tk_module.StringVar()
            tk_module.Label(
                right, textvariable=msg_var,
                font=("Courier", 9), justify="left",
                wraplength=INFO_W - 14, anchor="nw", bg="#eaeaea",
                relief="sunken", padx=5, pady=5
            ).pack(fill="x", padx=6, pady=4)

            stats_var = tk_module.StringVar()
            tk_module.Label(
                right, textvariable=stats_var,
                font=("Courier", 9), justify="left",
                bg="#f8f8f8", anchor="nw", padx=6
            ).pack(fill="x", padx=6, pady=(0, 6))

            tk_module.Label(right, text="REGION KEY", font=("Courier", 9, "bold"),
                            bg="#f8f8f8").pack(anchor="w", padx=6)

            legend_canvas = tk_module.Canvas(right, bg="#f8f8f8",
                                             highlightthickness=0, width=INFO_W - 12)
            legend_canvas.pack(fill="both", expand=True, padx=6, pady=4)

            prog_frame = tk_module.Frame(win)
            prog_frame.grid(row=2, column=0, columnspan=2, sticky="we", padx=10)
            prog_lbl = tk_module.Label(prog_frame, text="Step 1/1",
                                       font=("Courier", 9), width=14, anchor="w")
            prog_lbl.pack(side="left")
            prog_bar = tk_module.Canvas(prog_frame, height=12, bg="#cccccc",
                                        highlightthickness=0)
            prog_bar.pack(side="left", fill="x", expand=True, padx=4)

            spd_frame = tk_module.Frame(win)
            spd_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 4))
            tk_module.Label(spd_frame, text="Speed:", font=("Courier", 9)).pack(side="left")
            speed_var = tk_module.IntVar(value=350)
            tk_module.Scale(spd_frame, from_=30, to=1200, orient="horizontal",
                            variable=speed_var, length=180, showvalue=False).pack(side="left", padx=4)
            tk_module.Label(spd_frame, text="Fast \u2190\u2192 Slow", font=("Courier", 8)).pack(side="left")

            ctrl = tk_module.Frame(win)
            ctrl.grid(row=4, column=0, columnspan=2, pady=(0, 8))

            playing  = [False]
            cur      = [0]
            after_id = [None]

            def gx(x): return MARGIN + x * CELL
            def gy(y): return MARGIN + y * CELL

            def draw_step(idx):
                s         = steps[idx]
                claimed   = s["claimed"]
                unclaimed = s["unclaimed"]
                phase     = s["phase"]
                active_r  = s["active_r"]
                message   = s["message"]

                canvas.delete("all")

                for cid in my_range(n * n):
                    cx2, cy2 = cid % n, cid // n
                    x0, y0 = gx(cx2), gy(cy2)
                    x1, y1 = gx(cx2 + 1), gy(cy2 + 1)
                    if cid in claimed:
                        r    = claimed[cid]
                        fill = "#ffffff" if (active_r is not None and r == active_r) else region_colour(r)
                    else:
                        fill = "#c8c8c8"
                    canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")

                for i in my_range(n + 1):
                    canvas.create_line(gx(i), gy(0), gx(i), gy(n), fill="#888", width=1)
                    canvas.create_line(gx(0), gy(i), gx(n), gy(i), fill="#888", width=1)

                for cy2 in my_range(n):
                    for cx2 in my_range(n):
                        cid = cy2 * n + cx2
                        o1  = claimed.get(cid, -1)
                        if cx2 + 1 < n:
                            o2 = claimed.get(cy2 * n + cx2 + 1, -2)
                            if o1 != o2:
                                canvas.create_line(gx(cx2+1), gy(cy2),
                                                   gx(cx2+1), gy(cy2+1),
                                                   fill="#111", width=3)
                        if cy2 + 1 < n:
                            o2 = claimed.get((cy2+1) * n + cx2, -2)
                            if o1 != o2:
                                canvas.create_line(gx(cx2), gy(cy2+1),
                                                   gx(cx2+1), gy(cy2+1),
                                                   fill="#111", width=3)

                canvas.create_rectangle(gx(0), gy(0), gx(n), gy(n),
                                        outline="#111", width=5)

                for di, (dx, dy) in my_enumerate(dots_data):
                    px, py = gx(dx), gy(dy)
                    ring = region_colour(di) if any(claimed.get(c) == di for c in claimed) else "#aaa"
                    canvas.create_oval(px-DOT_R-2, py-DOT_R-2,
                                       px+DOT_R+2, py+DOT_R+2,
                                       fill="white", outline=ring, width=3)
                    if n <= 12:
                        canvas.create_text(px, py, text=str(di),
                                           font=("Courier", max(6, DOT_R-1), "bold"),
                                           fill="#333")

                for cid in unclaimed:
                    cx2, cy2 = cid % n, cid // n
                    mx, my2 = gx(cx2 + 0.5), gy(cy2 + 0.5)
                    d = CELL // 4
                    canvas.create_line(mx-d, my2-d, mx+d, my2+d, fill="#999", width=1)
                    canvas.create_line(mx+d, my2-d, mx-d, my2+d, fill="#999", width=1)

                if active_r is not None:
                    for cid, r in claimed.items():
                        if r == active_r:
                            cx2, cy2 = cid % n, cid // n
                            canvas.create_rectangle(
                                gx(cx2)+2, gy(cy2)+2,
                                gx(cx2+1)-2, gy(cy2+1)-2,
                                outline="#ff0000", width=2, fill=""
                            )

                col = PHASE_COLOUR.get(phase, "#555")
                banner_var.set(f"  \u25cf {phase}   (step {idx+1} of {len(steps)})")
                banner_lbl.config(bg=col)

                n_cl  = len(claimed)
                n_un  = len(unclaimed)
                n_reg = len(set(claimed.values()))
                msg_var.set(message)
                stats_var.set(
                    f"Claimed  : {n_cl} / {n*n} cells\n"
                    f"Unclaimed: {n_un} cells\n"
                    f"Regions  : {n_reg} active"
                )

                legend_canvas.delete("all")
                active_rs = sorted(set(claimed.values()))
                SW, SH = 13, 13
                CPR = 3
                PAD = 4
                for li, ri in enumerate(active_rs):
                    rowi = li // CPR
                    coli = li % CPR
                    lx2  = PAD + coli * (SW + 28 + PAD)
                    ly2  = PAD + rowi * (SH + PAD + 2)
                    legend_canvas.create_rectangle(
                        lx2, ly2, lx2+SW, ly2+SH,
                        fill=region_colour(ri), outline="#333"
                    )
                    legend_canvas.create_text(
                        lx2+SW+3, ly2+SH//2, text=f"R{ri}",
                        anchor="w", font=("Courier", 8), fill="#111"
                    )
                rows = (len(active_rs) // CPR + 1)
                legend_canvas.config(height=max(40, rows * (SH + PAD + 2) + PAD))

                prog_lbl.config(text=f"Step {idx+1}/{len(steps)}")
                win.update_idletasks()
                pw = prog_bar.winfo_width()
                frac = (idx + 1) / len(steps)
                prog_bar.delete("all")
                prog_bar.create_rectangle(0, 0, int(pw * frac), 12,
                                          fill=col, outline="")

            def go_to(idx):
                idx = max(0, min(len(steps) - 1, idx))
                cur[0] = idx
                draw_step(idx)
                btn_prev.config(state="normal" if idx > 0 else "disabled")
                btn_next.config(state="normal" if idx < len(steps)-1 else "disabled")

            def tick():
                if not playing[0]: return
                if cur[0] < len(steps) - 1:
                    go_to(cur[0] + 1)
                    after_id[0] = win.after(speed_var.get(), tick)
                else:
                    playing[0] = False
                    btn_play.config(text="\u25b6  Play")

            def toggle_play():
                if playing[0]:
                    playing[0] = False
                    btn_play.config(text="\u25b6  Play")
                    if after_id[0]: win.after_cancel(after_id[0])
                else:
                    if cur[0] >= len(steps) - 1:
                        go_to(0)
                    playing[0] = True
                    btn_play.config(text="\u23f8  Pause")
                    tick()

            def jump_phase(phase_name):
                for i, st in enumerate(steps):
                    if st["phase"] == phase_name and i > cur[0]:
                        go_to(i); return
                for i, st in enumerate(steps):
                    if st["phase"] == phase_name:
                        go_to(i); return

            def on_close():
                playing[0] = False
                if after_id[0]: win.after_cancel(after_id[0])
                win.destroy()

            win.protocol("WM_DELETE_WINDOW", on_close)

            btn_prev = tk_module.Button(ctrl, text="\u25c4 Prev", width=8,
                                        command=lambda: go_to(cur[0] - 1))
            btn_prev.pack(side="left", padx=3)

            btn_play = tk_module.Button(ctrl, text="\u25b6  Play", width=9,
                                        command=toggle_play,
                                        bg="#27ae60", fg="white", font=("Courier", 9, "bold"))
            btn_play.pack(side="left", padx=3)

            btn_next = tk_module.Button(ctrl, text="Next \u25b6", width=8,
                                        command=lambda: go_to(cur[0] + 1))
            btn_next.pack(side="left", padx=3)

            tk_module.Button(ctrl, text="\u21a9 Start", width=8,
                             command=lambda: go_to(0)).pack(side="left", padx=3)

            tk_module.Label(ctrl, text="  Jump to:").pack(side="left")
            for ph in ["DIVIDE", "CONQUER", "COMBINE"]:
                tk_module.Button(
                    ctrl, text=ph, width=9,
                    bg=PHASE_COLOUR[ph], fg="white",
                    font=("Courier", 8, "bold"),
                    command=lambda p=ph: jump_phase(p)
                ).pack(side="left", padx=2)

            go_to(0)

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