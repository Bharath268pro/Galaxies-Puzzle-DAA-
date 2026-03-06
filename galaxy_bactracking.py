"""
Galaxies Puzzle — Pure Backtracking Solver
==========================================

Backtracking Algorithm:
  Phase 1 — SEED:   Cells touching a dot are immediately assigned to it.
  Phase 2 — BACKTRACK: MRV(minimum remaining values) cell selection, symmetric-pair assignment, undo on failure.
  Phase 3 — BFS:    Connectivity check after all cells are assigned.
"""

import tkinter as tk
from tkinter import messagebox
from collections import deque
import random
import time

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

OUTER_PAD  = 20
BORDER_W   = 5
GRID_COL   = "#b8b8b8"
WALL_COL   = "#111111"
BG_OUTER   = "#c0c0c0"
BG_INNER   = "#ffffff"
VALID_COL  = "#cce8ff"
DOT_R      = 10
DOT_W      = 2

CELL_FOR_SIZE = {5: 82, 7: 62, 9: 50, 11: 42}


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def my_len(obj):
    c = 0
    for _ in obj:
        c += 1
    return c

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

def my_enumerate(iterable):
    res = []
    i = 0
    for x in iterable:
        res.append((i, x))
        i += 1
    return res


# ══════════════════════════════════════════════════════════════════════════════
# PUZZLE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class PuzzleGenerator:
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
        for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
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


# ══════════════════════════════════════════════════════════════════════════════
# BACKTRACKING SOLVER
# ══════════════════════════════════════════════════════════════════════════════

class BacktrackSolver:
    def __init__(self, N, dots):
        self.N = N
        self.dots = dots
        self.backtracks = 0
        self.computations = 0
        self.start_time = None
        self.end_time = None

    def _sym(self, cx, cy, di):
        dx, dy = self.dots[di]
        scx_f = 2*dx - cx - 1
        scy_f = 2*dy - cy - 1
        if abs(scx_f - round(scx_f)) > 1e-9 or abs(scy_f - round(scy_f)) > 1e-9:
            return None
        scx, scy = int(round(scx_f)), int(round(scy_f))
        if 0 <= scx < self.N and 0 <= scy < self.N:
            return scx, scy
        return None

    def _touches(self, cx, cy, di):
        dx, dy = self.dots[di]
        return cx <= dx <= cx+1 and cy <= dy <= cy+1

    def _options(self, cx, cy, assign):
        count = 0
        for di in range(len(self.dots)):
            sym = self._sym(cx, cy, di)
            if sym is None:
                dx, dy = self.dots[di]
                if abs(dx-(cx+0.5)) < 1e-9 and abs(dy-(cy+0.5)) < 1e-9:
                    count += 1
            else:
                scx, scy = sym
                if assign[scy][scx] in (-1, di):
                    count += 1
        return count

    def _pick(self, assign):
        best, bval = None, 999
        for cy in range(self.N):
            for cx in range(self.N):
                if assign[cy][cx] != -1:
                    continue
                v = self._options(cx, cy, assign)
                if v == 0:
                    return cx, cy
                if v < bval:
                    bval, best = v, (cx, cy)
        return best

    def _dot_order(self, cx, cy, assign):
        adj = set()
        for dcx, dcy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = cx+dcx, cy+dcy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                d = assign[ny][nx]
                if d != -1:
                    adj.add(d)
        order = list(adj)
        for di in range(len(self.dots)):
            if di not in adj:
                order.append(di)
        return order

    def _connected(self, assign):
        N = self.N
        for di in range(len(self.dots)):
            region = [(cx, cy) for cy in range(N) for cx in range(N) if assign[cy][cx] == di]
            if not region:
                return False
            rs = set(region)
            vis = {region[0]}
            q = deque([region[0]])
            while q:
                cx, cy = q.popleft()
                for dcx, dcy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nb = (cx+dcx, cy+dcy)
                    if nb in rs and nb not in vis:
                        vis.add(nb); q.append(nb)
            if len(vis) != len(rs):
                return False
        return True

    def _bt(self, assign):
        cell = self._pick(assign)
        if cell is None:
            return self._connected(assign)
        cx, cy = cell
        tried = set()
        for di in self._dot_order(cx, cy, assign):
            self.computations += 1
            if di in tried:
                continue
            tried.add(di)
            sym = self._sym(cx, cy, di)
            if sym is not None:
                scx, scy = sym
                if assign[scy][scx] not in (-1, di):
                    continue
            else:
                dx, dy = self.dots[di]
                if abs(dx-(cx+0.5)) > 1e-9 or abs(dy-(cy+0.5)) > 1e-9:
                    continue
            assign[cy][cx] = di
            sym_a = None
            if sym is not None:
                scx, scy = sym
                if assign[scy][scx] == -1:
                    assign[scy][scx] = di
                    sym_a = (scx, scy)
            if self._bt(assign):
                return True
            assign[cy][cx] = -1
            if sym_a:
                assign[sym_a[1]][sym_a[0]] = -1
            self.backtracks += 1
        return False

    def solve(self):
        N = self.N
        assign = [[-1]*N for _ in range(N)]
        for cy in range(N):
            for cx in range(N):
                for di in range(len(self.dots)):
                    if self._touches(cx, cy, di) and assign[cy][cx] == -1:
                        assign[cy][cx] = di
        self.backtracks = 0
        self.computations = 0
        self.start_time = time.time()
        result = self._bt(assign)
        self.end_time = time.time()
        
        elapsed = self.end_time - self.start_time
        print(f"\n{'='*60}")
        print(f"Backtracking Solver Statistics")
        print(f"{'='*60}")
        print(f"Grid Size: {N}×{N}")
        print(f"Number of Dots: {len(self.dots)}")
        print(f"Computations: {self.computations}")
        print(f"Backtracks: {self.backtracks}")
        print(f"Time Taken: {elapsed:.6f} seconds")
        print(f"{'='*60}\n")
        
        return assign if result else None


# ══════════════════════════════════════════════════════════════════════════════
# GAME STATE
# ══════════════════════════════════════════════════════════════════════════════

def border_edges(N):
    edges = set()
    for x in range(N):
        edges.add(('h', x, 0)); edges.add(('h', x, N))
    for y in range(N):
        edges.add(('v', 0, y)); edges.add(('v', N, y))
    return edges

def assign_to_edges(assign, N):
    edges = set()
    for cy in range(N):
        for cx in range(N):
            o = assign[cy][cx]
            if cx+1 < N and assign[cy][cx+1] != o:
                edges.add(('v', cx+1, cy))
            if cy+1 < N and assign[cy+1][cx] != o:
                edges.add(('h', cx, cy+1))
    return edges


class GameState:
    def __init__(self, N, seed=None):
        self.N = N
        self.rng = random.Random(seed)
        self._new()

    def _new(self):
        gen = PuzzleGenerator(self.N, self.rng)
        gen.generate()
        self.dots = gen.dots
        self.owner = gen.owner
        self.solution_edges = gen.solution_edges
        self.fixed = border_edges(self.N)
        self.edges = set(self.fixed)
        self.history = []
        self.redo_stack = []
        self.solution_assign = None

    def new_puzzle(self): self._new()

    def reset(self):
        self.edges = set(self.fixed)
        self.history = []
        self.redo_stack = []

    def toggle_edge(self, edge):
        if edge in self.fixed:
            return False
        if edge in self.edges:
            self.edges.remove(edge)
            self.history.append((edge, False))
        else:
            self.edges.add(edge)
            self.history.append((edge, True))
        self.redo_stack.clear()
        return True

    def undo(self):
        if not self.history: return False
        edge, added = self.history.pop()
        (self.edges.discard if added else self.edges.add)(edge)
        self.redo_stack.append((edge, added))
        return True

    def redo(self):
        if not self.redo_stack: return False
        edge, added = self.redo_stack.pop()
        (self.edges.add if added else self.edges.discard)(edge)
        self.history.append((edge, added))
        return True

    def get_regions(self):
        N = self.N
        visited = [[False]*N for _ in range(N)]
        regions = []
        def bfs(sx, sy):
            comp, q = [], deque([(sx, sy)])
            visited[sy][sx] = True
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for dcx, dcy, wfn in [
                    ( 1, 0, lambda x,y:('v',x+1,y)),
                    (-1, 0, lambda x,y:('v',x,  y)),
                    ( 0, 1, lambda x,y:('h',x,  y+1)),
                    ( 0,-1, lambda x,y:('h',x,  y)),
                ]:
                    nx, ny = cx+dcx, cy+dcy
                    if 0<=nx<N and 0<=ny<N and not visited[ny][nx]:
                        if wfn(cx,cy) not in self.edges:
                            visited[ny][nx] = True
                            q.append((nx, ny))
            return frozenset(comp)
        for cy in range(N):
            for cx in range(N):
                if not visited[cy][cx]:
                    regions.append(bfs(cx, cy))
        return regions

    def _dot_in(self, region):
        for di, (dx, dy) in enumerate(self.dots):
            for cx, cy in region:
                if cx <= dx <= cx+1 and cy <= dy <= cy+1:
                    return di, dx, dy
        return None

    def _symmetric(self, region, dx, dy):
        for cx, cy in region:
            scx_f = 2*dx - cx - 1
            scy_f = 2*dy - cy - 1
            if abs(scx_f-round(scx_f)) > 1e-9 or abs(scy_f-round(scy_f)) > 1e-9:
                return False
            if (int(round(scx_f)), int(round(scy_f))) not in region:
                return False
        return True

    def valid_cells(self):
        valid = set()
        for region in self.get_regions():
            info = self._dot_in(region)
            if info and self._symmetric(region, info[1], info[2]):
                valid.update(region)
        return valid

    def is_solved(self):
        return len(self.valid_cells()) == self.N * self.N


# ══════════════════════════════════════════════════════════════════════════════
# UI — matches reference screenshots exactly
# ══════════════════════════════════════════════════════════════════════════════

class GalaxiesUI(tk.Tk):

    SIZES  = [5, 7, 9, 11]
    LABELS = ["5×5  (Easy)", "7×7  (Normal)", "9×9  (Hard)", "11×11  (Expert)"]

    def __init__(self):
        super().__init__()
        self.title("Galaxies Puzzle")
        self.resizable(False, False)
        self.configure(bg=BG_OUTER)

        self.N    = 7
        self.cell = CELL_FOR_SIZE[self.N]
        self.game = GameState(self.N)

        self._build_toolbar()
        self._build_canvas()
        self._build_statusbar()
        self.redraw()

    # ── toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        tb = tk.Frame(self, bg="#e0e0e0", relief="raised", bd=1)
        tb.pack(fill="x")

        B = dict(font=("Arial", 10, "bold"), relief="groove", bd=2,
                 bg="#efefef", activebackground="#d4d4d4",
                 padx=12, pady=5, cursor="hand2")

        tk.Button(tb, text="New game",      command=self._new_game,  **B).pack(side="left", padx=(6,2), pady=5)
        tk.Button(tb, text="Restart game",  command=self._restart,   **B).pack(side="left", padx=2, pady=5)

        self.undo_btn = tk.Button(tb, text="Undo move", command=self._undo, **B)
        self.undo_btn.pack(side="left", padx=2, pady=5)

        self.redo_btn = tk.Button(tb, text="Redo move", command=self._redo, **B)
        self.redo_btn.pack(side="left", padx=2, pady=5)

        # difficulty
        self.diff_var = tk.StringVar(value=self.LABELS[1])
        om = tk.OptionMenu(tb, self.diff_var, *self.LABELS, command=self._change_diff)
        om.config(font=("Arial", 10, "bold"), relief="groove", bd=2,
                  bg="#efefef", activebackground="#d4d4d4",
                  padx=6, pady=3, cursor="hand2", width=14)
        om["menu"].config(font=("Arial", 10))
        om.pack(side="left", padx=2, pady=5)

        tk.Button(tb, text="Solve game", command=self._solve, **B).pack(side="left", padx=(2,6), pady=5)

    # ── canvas ────────────────────────────────────────────────────────────────

    def _canvas_wh(self):
        return OUTER_PAD*2 + BORDER_W*2 + self.N * self.cell + 2

    def _build_canvas(self):
        s = self._canvas_wh()
        self.canvas = tk.Canvas(self, width=s, height=s,
                                bg=BG_OUTER, highlightthickness=0)
        self.canvas.pack(padx=0, pady=0)
        self.canvas.bind("<Button-1>", self._on_click)

    def _build_statusbar(self):
        self.sv = tk.StringVar(value="Click on a grid edge to draw a wall.")
        tk.Label(self, textvariable=self.sv,
                 font=("Arial", 9), bg="#b8b8b8", fg="#222222",
                 anchor="w", padx=10, pady=3, relief="sunken", bd=1
                 ).pack(fill="x", side="bottom")

    # ── coords ────────────────────────────────────────────────────────────────

    def _ox(self): return OUTER_PAD + BORDER_W
    def _oy(self): return OUTER_PAD + BORDER_W

    def _gx(self, x): return self._ox() + x * self.cell
    def _gy(self, y): return self._oy() + y * self.cell

    def _pixel_to_edge(self, px, py):
        N = self.N
        gx = (px - self._ox()) / self.cell
        gy = (py - self._oy()) / self.cell
        if gx < -0.15 or gy < -0.15 or gx > N+0.15 or gy > N+0.15:
            return None
        rx, ry = round(gx), round(gy)
        dx, dy = abs(gx - rx), abs(gy - ry)
        TOL = 0.22
        if min(dx, dy) > TOL:
            return None
        if dx < dy:
            xi, yi = int(rx), int(gy)
            if 0 <= xi <= N and 0 <= yi < N:
                return ('v', xi, yi)
        else:
            xi, yi = int(gx), int(ry)
            if 0 <= xi < N and 0 <= yi <= N:
                return ('h', xi, yi)
        return None

    # ── draw ──────────────────────────────────────────────────────────────────

    def redraw(self):
        c = self.canvas
        N = self.N
        c.delete("all")

        vcells = self.game.valid_cells()

        # cell fills (white, or light blue if valid)
        for cy in range(N):
            for cx in range(N):
                x0, y0 = self._gx(cx),   self._gy(cy)
                x1, y1 = self._gx(cx+1), self._gy(cy+1)
                fill = VALID_COL if (cx, cy) in vcells else BG_INNER
                c.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")

        # faint grid
        for i in range(N+1):
            c.create_line(self._gx(i), self._gy(0), self._gx(i), self._gy(N),
                          fill=GRID_COL, width=1)
            c.create_line(self._gx(0), self._gy(i), self._gx(N), self._gy(i),
                          fill=GRID_COL, width=1)

        # player walls — thick black, projecting caps so corners join cleanly
        for edge in self.game.edges:
            t, ex, ey = edge
            if edge in self.game.fixed:
                continue
            W = 4
            if t == 'v':
                x = self._gx(ex)
                c.create_line(x, self._gy(ey), x, self._gy(ey+1),
                              width=W, fill=WALL_COL, capstyle="projecting")
            else:
                y = self._gy(ey)
                c.create_line(self._gx(ex), y, self._gx(ex+1), y,
                              width=W, fill=WALL_COL, capstyle="projecting")

        # dots — hollow circles exactly like reference
        for di, (dx, dy) in enumerate(self.game.dots):
            px, py = self._gx(dx), self._gy(dy)
            r = DOT_R
            c.create_oval(px-r, py-r, px+r, py+r,
                          outline=WALL_COL, fill=BG_INNER, width=DOT_W)

        # thick inner border rectangle
        bx0 = self._gx(0)
        by0 = self._gy(0)
        bx1 = self._gx(N)
        by1 = self._gy(N)
        c.create_rectangle(bx0, by0, bx1, by1,
                           outline=WALL_COL, width=BORDER_W+2, fill="")

        # undo/redo button states
        self.undo_btn.config(state="normal" if self.game.history    else "disabled",
                             fg="black"     if self.game.history    else "#aaaaaa")
        self.redo_btn.config(state="normal" if self.game.redo_stack else "disabled",
                             fg="black"     if self.game.redo_stack else "#aaaaaa")

        # status
        regions = self.game.get_regions()
        vcnt = sum(1 for r in regions
                   if (info := self.game._dot_in(r)) and
                   self.game._symmetric(r, info[1], info[2]))
        nd   = len(self.game.dots)
        nw   = len(self.game.edges - self.game.fixed)
        self.sv.set(f"Grid: {N}×{N}  |  Galaxies: {nd}  |  "
                    f"Valid: {vcnt}/{nd}  |  Walls: {nw}")

        if self.game.is_solved():
            self.sv.set(f"✓  Solved! All {nd} galaxies are valid.")
            messagebox.showinfo("Galaxies", "🎉  Puzzle Solved!\nAll galaxies are valid.")

    # ── events ────────────────────────────────────────────────────────────────

    def _on_click(self, event):
        edge = self._pixel_to_edge(event.x, event.y)
        if edge:
            self.game.toggle_edge(edge)
            self.redraw()

    def _new_game(self):
        self.game.new_puzzle(); self.redraw()

    def _restart(self):
        self.game.reset(); self.redraw()

    def _undo(self):
        self.game.undo(); self.redraw()

    def _redo(self):
        self.game.redo(); self.redraw()

    def _change_diff(self, label):
        idx = self.LABELS.index(label)
        self.N    = self.SIZES[idx]
        self.cell = CELL_FOR_SIZE[self.N]
        self.game = GameState(self.N)
        s = self._canvas_wh()
        self.canvas.config(width=s, height=s)
        self.redraw()

    def _solve(self):
        if self.game.solution_assign is None:
            # Compute solution on demand
            solver = BacktrackSolver(self.game.N, self.game.dots)
            self.game.solution_assign = solver.solve()
        
        sa = self.game.solution_assign
        if sa is None:
            messagebox.showwarning("Galaxies", "No solution found."); return
        self.game.edges = set(self.game.fixed) | assign_to_edges(sa, self.N)
        self.game.history.clear()
        self.game.redo_stack.clear()
        self.redraw()


if __name__ == "__main__":
    GalaxiesUI().mainloop()