

import tkinter as tk
from tkinter import messagebox
from collections import deque
import random
import time

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

OUTER_PAD  = 24
BORDER_W   = 5
GRID_COL   = "#c0c0c0"
WALL_COL   = "#111111"
BG_OUTER   = "#2b2b2b"
BG_INNER   = "#ffffff"
VALID_COL  = "#cce8ff"
UNASSIGNED = "#f5f5f5"
BACKTRACK_COL = "#ff6b6b"
CURRENT_COL   = "#ffe066"
DOT_R      = 9
DOT_W      = 2
STEP_MS    = 500          # 0.5 seconds between steps

CELL_FOR_SIZE = {5: 80, 7: 60, 9: 50, 11: 42}

# 20 distinct pastel galaxy colours
GALAXY_COLOURS = [
    "#b3d9ff", "#b3ffb3", "#ffb3b3", "#ffffb3", "#d9b3ff",
    "#b3fff0", "#ffd9b3", "#ffb3e6", "#c6ffb3", "#b3c6ff",
    "#ffc6b3", "#b3ffcc", "#e6b3ff", "#fff0b3", "#b3ffe6",
    "#ffb3cc", "#ccffb3", "#b3e6ff", "#ffd9ff", "#d9ffb3",
]

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def my_len(obj):
    c = 0
    for _ in obj: c += 1
    return c

def my_range(start, stop=None, step=1):
    if stop is None: stop, start = start, 0
    res, curr = [], start
    while curr < stop:
        res.append(curr); curr += step
    return res

def my_enumerate(iterable):
    res, i = [], 0
    for x in iterable:
        res.append((i, x)); i += 1
    return res

# ══════════════════════════════════════════════════════════════════════════════
# PUZZLE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class PuzzleGenerator:
    def __init__(self, n=4, rng=None):
        self.N   = n
        self.rng = rng or random.Random()
        self.rects = []
        self.owner = [-1] * (n * n)
        self.dots  = []
        self.solution_edges = set()

    def cell_id(self, x, y): return y * self.N + x

    def sym_cell(self, cx, cy, dx, dy):
        return int(2*dx - cx - 1), int(2*dy - cy - 1)

    def _cell_neighbors(self, cid, n):
        cx, cy = cid % n, cid // n
        return [ny*n+nx for nx,ny in [(cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)]
                if 0<=nx<n and 0<=ny<n]

    def generate(self, target_rects=None):
        n = self.N
        self.owner = [-1] * (n*n)
        self.dots  = []
        cells_remaining = set(my_range(n*n))
        regions = []
        if target_rects is None:
            target_rects = max(n*n//4, 3)

        potential_dots = [(x2/2.0, y2/2.0)
                          for y2 in my_range(1, 2*n)
                          for x2 in my_range(1, 2*n)]
        self.rng.shuffle(potential_dots)

        for dx, dy in potential_dots:
            if my_len(regions) >= target_rects: break
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

        max_passes, passes = n*n*4, 0
        while cells_remaining and passes < max_passes:
            passes += 1
            made_progress = False
            r_indices = list(my_range(my_len(regions)))
            self.rng.shuffle(r_indices)
            for r_idx in r_indices:
                if not cells_remaining: break
                dx, dy = self.dots[r_idx]
                region = regions[r_idx]
                possible_extensions = []
                for c in list(region):
                    for ncid in self._cell_neighbors(c, n):
                        if ncid not in cells_remaining: continue
                        scx, scy = self.sym_cell(ncid%n, ncid//n, dx, dy)
                        if not (0<=int(scx)<n and 0<=int(scy)<n): continue
                        scid = int(scy)*n + int(scx)
                        if scid == ncid:
                            possible_extensions.append((ncid, ncid))
                        elif scid in cells_remaining:
                            adj_r = any(nb in region for nb in self._cell_neighbors(scid, n))
                            adj_n = scid in self._cell_neighbors(ncid, n)
                            if adj_r or adj_n:
                                possible_extensions.append((ncid, scid))
                if possible_extensions:
                    c1, c2 = self.rng.choice(possible_extensions)
                    for cid in set([c1, c2]):
                        if cid in cells_remaining:
                            self.owner[cid] = r_idx
                            cells_remaining.discard(cid)
                            region.add(cid)
                    made_progress = True
            if not made_progress: break

        max_fallback, fp = n*n*6, 0
        while cells_remaining and fp < max_fallback:
            fp += 1; made_progress = False
            for cid in list(cells_remaining):
                if cid not in cells_remaining: continue
                cx, cy = cid%n, cid//n
                best_r, best_dist = -1, float('inf')
                for r_idx, (dx, dy) in my_enumerate(self.dots):
                    if not any(nb in regions[r_idx] for nb in self._cell_neighbors(cid, n)): continue
                    scx, scy = self.sym_cell(cx, cy, dx, dy)
                    if not (0<=int(scx)<n and 0<=int(scy)<n): continue
                    scid = int(scy)*n + int(scx)
                    if scid == cid:
                        dist = (cx+.5-dx)**2 + (cy+.5-dy)**2
                        if dist < best_dist: best_dist, best_r = dist, r_idx
                    elif scid in cells_remaining or self.owner[scid] == r_idx:
                        adj_r = any(nb in regions[r_idx] for nb in self._cell_neighbors(scid, n))
                        adj_c = scid in self._cell_neighbors(cid, n)
                        if adj_r or adj_c:
                            dist = (cx+.5-dx)**2 + (cy+.5-dy)**2
                            if dist < best_dist: best_dist, best_r = dist, r_idx
                if best_r >= 0:
                    dx, dy = self.dots[best_r]
                    scx, scy = self.sym_cell(cx, cy, dx, dy)
                    scid = int(scy)*n + int(scx)
                    for ac in set([cid, scid]):
                        if ac in cells_remaining:
                            self.owner[ac] = best_r
                            cells_remaining.discard(ac)
                            regions[best_r].add(ac)
                    made_progress = True
            if not made_progress: break

        while cells_remaining:
            cid = next(iter(cells_remaining))
            cx, cy = cid%n, cid//n
            r_idx = my_len(self.dots)
            self.dots.append((cx+.5, cy+.5))
            regions.append({cid})
            self.owner[cid] = r_idx
            cells_remaining.discard(cid)

        self.solution_edges = self.compute_solution_edges()

    def _get_initial_cells_for_dot(self, dx, dy):
        n = self.N
        dx_half = (dx*2)%2 == 1
        dy_half = (dy*2)%2 == 1
        seeds = set()
        if dx_half and dy_half:
            ix, iy = int(dx), int(dy)
            if 0<=ix<n and 0<=iy<n: seeds.add(iy*n+ix)
        elif dx_half and not dy_half:
            ix, iy = int(dx), int(dy)
            for cy in [iy-1, iy]:
                if 0<=ix<n and 0<=cy<n: seeds.add(cy*n+ix)
        elif not dx_half and dy_half:
            ix, iy = int(dx), int(dy)
            for cx in [ix-1, ix]:
                if 0<=cx<n and 0<=iy<n: seeds.add(iy*n+cx)
        else:
            ix, iy = int(dx), int(dy)
            for cy in [iy-1, iy]:
                for cx in [ix-1, ix]:
                    if 0<=cx<n and 0<=cy<n: seeds.add(cy*n+cx)
        if not seeds: return []
        for c in seeds:
            cx, cy = c%n, c//n
            scx, scy = self.sym_cell(cx, cy, dx, dy)
            if int(scx)!=scx or int(scy)!=scy: return []
            if int(scy)*n+int(scx) not in seeds: return []
        return list(seeds)

    def compute_solution_edges(self):
        n = self.N; edges = set()
        for x in my_range(n): edges.add(('h',x,0)); edges.add(('h',x,n))
        for y in my_range(n): edges.add(('v',0,y)); edges.add(('v',n,y))
        for y in my_range(n):
            for x in my_range(n):
                o = self.owner[self.cell_id(x,y)]
                if x+1<n and self.owner[self.cell_id(x+1,y)] != o: edges.add(('v',x+1,y))
                if y+1<n and self.owner[self.cell_id(x,y+1)] != o: edges.add(('h',x,y+1))
        return edges

# ══════════════════════════════════════════════════════════════════════════════
# ANIMATED BACKTRACKING SOLVER
# ══════════════════════════════════════════════════════════════════════════════

class AnimatedBacktrackSolver:
    """
    Runs the full backtracking algorithm synchronously but records every
    meaningful state change as a step dict. Steps are played back via tk.after().
    """

    def __init__(self, N, dots):
        self.N    = N
        self.dots = dots
        self.backtracks   = 0
        self.computations = 0

    def _sym(self, cx, cy, di):
        dx, dy = self.dots[di]
        scx_f = 2*dx - cx - 1
        scy_f = 2*dy - cy - 1
        if abs(scx_f - round(scx_f)) > 1e-9 or abs(scy_f - round(scy_f)) > 1e-9:
            return None
        scx, scy = int(round(scx_f)), int(round(scy_f))
        return (scx, scy) if (0<=scx<self.N and 0<=scy<self.N) else None

    def _touches(self, cx, cy, di):
        dx, dy = self.dots[di]
        return cx <= dx <= cx+1 and cy <= dy <= cy+1

    def _options(self, cx, cy, assign):
        count = 0
        for di in range(len(self.dots)):
            sym = self._sym(cx, cy, di)
            if sym is None:
                dx, dy = self.dots[di]
                if abs(dx-(cx+.5))<1e-9 and abs(dy-(cy+.5))<1e-9: count+=1
            else:
                scx, scy = sym
                if assign[scy][scx] in (-1, di): count+=1
        return count

    def _pick(self, assign):
        best, bval = None, 999
        for cy in range(self.N):
            for cx in range(self.N):
                if assign[cy][cx] != -1: continue
                v = self._options(cx, cy, assign)
                if v == 0: return cx, cy
                if v < bval: bval, best = v, (cx, cy)
        return best

    def _dot_order(self, cx, cy, assign):
        adj = set()
        for dcx, dcy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = cx+dcx, cy+dcy
            if 0<=nx<self.N and 0<=ny<self.N:
                d = assign[ny][nx]
                if d != -1: adj.add(d)
        order = list(adj)
        for di in range(len(self.dots)):
            if di not in adj: order.append(di)
        return order

    def _connected(self, assign):
        N = self.N
        for di in range(len(self.dots)):
            region = [(cx,cy) for cy in range(N) for cx in range(N) if assign[cy][cx]==di]
            if not region: return False
            rs  = set(region)
            vis = {region[0]}
            q   = deque([region[0]])
            while q:
                cx, cy = q.popleft()
                for dcx, dcy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nb = (cx+dcx, cy+dcy)
                    if nb in rs and nb not in vis:
                        vis.add(nb); q.append(nb)
            if len(vis) != len(rs): return False
        return True

    def build_steps(self):
        """Run BT fully, recording each assign/backtrack as a step."""
        N = self.N
        assign = [[-1]*N for _ in range(N)]

        # Phase 1 – seed cells adjacent to dots
        for cy in range(N):
            for cx in range(N):
                for di in range(len(self.dots)):
                    if self._touches(cx, cy, di) and assign[cy][cx] == -1:
                        assign[cy][cx] = di

        steps = []

        def snapshot(kind, highlight=None, backtrack_cells=None):
            steps.append({
                "kind":            kind,
                "grid":            [row[:] for row in assign],
                "highlight":       highlight,
                "backtrack_cells": list(backtrack_cells or []),
            })

        snapshot("seed")

        def _bt(assign):
            cell = self._pick(assign)
            if cell is None:
                ok = self._connected(assign)
                snapshot("done" if ok else "fail")
                return ok

            cx, cy = cell
            tried  = set()

            for di in self._dot_order(cx, cy, assign):
                self.computations += 1
                if di in tried: continue
                tried.add(di)

                sym = self._sym(cx, cy, di)
                if sym is not None:
                    scx, scy = sym
                    if assign[scy][scx] not in (-1, di): continue
                else:
                    dx, dy = self.dots[di]
                    if abs(dx-(cx+.5))>1e-9 or abs(dy-(cy+.5))>1e-9: continue

                # assign
                assign[cy][cx] = di
                sym_a = None
                if sym is not None:
                    scx, scy = sym
                    if assign[scy][scx] == -1:
                        assign[scy][scx] = di
                        sym_a = (scx, scy)

                snapshot("assign", highlight=(cx, cy))

                if _bt(assign):
                    return True

                # undo
                bt_cells = [(cx, cy)]
                assign[cy][cx] = -1
                if sym_a:
                    assign[sym_a[1]][sym_a[0]] = -1
                    bt_cells.append(sym_a)
                self.backtracks += 1
                snapshot("backtrack", highlight=(cx, cy), backtrack_cells=bt_cells)

            return False

        _bt(assign)
        return steps, assign

# ══════════════════════════════════════════════════════════════════════════════
# GAME STATE
# ══════════════════════════════════════════════════════════════════════════════

def border_edges(N):
    e = set()
    for x in range(N): e.add(('h',x,0)); e.add(('h',x,N))
    for y in range(N): e.add(('v',0,y)); e.add(('v',N,y))
    return e

def assign_to_edges(assign, N):
    edges = set()
    for cy in range(N):
        for cx in range(N):
            o = assign[cy][cx]
            if cx+1<N and assign[cy][cx+1]!=o: edges.add(('v',cx+1,cy))
            if cy+1<N and assign[cy+1][cx]!=o: edges.add(('h',cx,cy+1))
    return edges

class GameState:
    def __init__(self, N, seed=None):
        self.N   = N
        self.rng = random.Random(seed)
        self._new()

    def _new(self):
        gen = PuzzleGenerator(self.N, self.rng)
        gen.generate()
        self.dots           = gen.dots
        self.owner          = gen.owner
        self.solution_edges = gen.solution_edges
        self.fixed          = border_edges(self.N)
        self.edges          = set(self.fixed)

    def new_puzzle(self): self._new()

# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════

class GalaxiesUI(tk.Tk):

    SIZES  = [5, 7, 9, 11]
    LABELS = ["5×5  (Easy)", "7×7  (Normal)", "9×9  (Hard)", "11×11  (Expert)"]

    def __init__(self):
        super().__init__()
        self.title("Galaxies — Backtracking Visualizer")
        self.resizable(False, False)
        self.configure(bg=BG_OUTER)

        self.N    = 7
        self.cell = CELL_FOR_SIZE[self.N]
        self.game = GameState(self.N)

        self._steps       = []
        self._step_idx    = 0
        self._playing     = False
        self._after_id    = None
        self._total_bt    = 0
        self._total_comp  = 0

        self._build_toolbar()
        self._build_canvas()
        self._build_legend()
        self._build_statusbar()
        self.redraw_puzzle()

    # ── toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        tb = tk.Frame(self, bg="#3c3c3c", relief="flat", bd=0)
        tb.pack(fill="x")

        B = dict(font=("Courier", 10, "bold"), relief="flat", bd=0,
                 bg="#555555", fg="#ffffff", activebackground="#777777",
                 activeforeground="#ffffff", padx=14, pady=6, cursor="hand2")

        tk.Button(tb, text="New Puzzle", command=self._new_game, **B).pack(side="left", padx=(8,2), pady=6)

        self.diff_var = tk.StringVar(value=self.LABELS[1])
        om = tk.OptionMenu(tb, self.diff_var, *self.LABELS, command=self._change_diff)
        om.config(font=("Courier", 10, "bold"), relief="flat", bd=0,
                  bg="#555555", fg="#ffffff", activebackground="#777777",
                  padx=6, pady=4, cursor="hand2", width=14, highlightthickness=0)
        om["menu"].config(font=("Courier", 10), bg="#444", fg="white")
        om.pack(side="left", padx=4, pady=6)

        tk.Frame(tb, bg="#666", width=1, height=28).pack(side="left", padx=8, pady=6)

        self.viz_btn = tk.Button(tb, text="▶  Visualize Solve",
                                 command=self._start_viz, **B)
        self.viz_btn.config(bg="#2a7a2a")
        self.viz_btn.pack(side="left", padx=2, pady=6)

        self.stop_btn = tk.Button(tb, text="Stop",
                                  command=self._stop_viz, **B)
        self.stop_btn.config(bg="#7a2a2a", state="disabled")
        self.stop_btn.pack(side="left", padx=2, pady=6)

        self.skip_btn = tk.Button(tb, text="Skip to End",
                                  command=self._skip_to_end, **B)
        self.skip_btn.config(bg="#2a4a7a", state="disabled")
        self.skip_btn.pack(side="left", padx=2, pady=6)

        tk.Label(tb, text="  Delay:", bg="#3c3c3c", fg="#ccc",
                 font=("Courier", 9)).pack(side="left")
        self.speed_var = tk.IntVar(value=STEP_MS)
        tk.Scale(tb, from_=50, to=2000, orient="horizontal",
                 variable=self.speed_var, length=130,
                 bg="#3c3c3c", fg="#ccc", troughcolor="#555",
                 highlightthickness=0, bd=0, showvalue=True,
                 label="").pack(side="left", pady=6)
        tk.Label(tb, text="ms", bg="#3c3c3c", fg="#888",
                 font=("Courier", 8)).pack(side="left")

    # ── canvas ────────────────────────────────────────────────────────────────

    def _canvas_wh(self):
        return OUTER_PAD*2 + BORDER_W*2 + self.N * self.cell + 2

    def _build_canvas(self):
        s = self._canvas_wh()
        self.canvas = tk.Canvas(self, width=s, height=s,
                                bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(padx=0, pady=0)

    def _build_legend(self):
        leg = tk.Frame(self, bg="#2b2b2b")
        leg.pack(fill="x", padx=8, pady=3)
        items = [
            (UNASSIGNED,      "Unassigned"),
            (GALAXY_COLOURS[0], "Galaxy (unique colour per dot)"),
            (CURRENT_COL,     "Current cell"),
            (BACKTRACK_COL,   "Backtrack / undo"),
            (VALID_COL,       "Solved"),
        ]
        for colour, label in items:
            tk.Label(leg, bg=colour, width=2, relief="solid", bd=1).pack(side="left", padx=(6,2), pady=2)
            tk.Label(leg, text=label, bg="#2b2b2b", fg="#bbb",
                     font=("Courier", 8)).pack(side="left", padx=(0,10))

    def _build_statusbar(self):
        self.sv = tk.StringVar(value="Press 'Visualize Solve' to watch the backtracking algorithm step by step.")
        tk.Label(self, textvariable=self.sv,
                 font=("Courier", 9), bg="#1e1e1e", fg="#aaaaaa",
                 anchor="w", padx=10, pady=4).pack(fill="x", side="bottom")

    # ── coordinate helpers ────────────────────────────────────────────────────

    def _ox(self): return OUTER_PAD + BORDER_W
    def _oy(self): return OUTER_PAD + BORDER_W
    def _gx(self, x): return self._ox() + x * self.cell
    def _gy(self, y): return self._oy() + y * self.cell

    # ── draw ─────────────────────────────────────────────────────────────────

    def _cell_colour(self, di, is_highlight=False, is_backtrack=False, solved=False):
        if is_backtrack: return BACKTRACK_COL
        if is_highlight: return CURRENT_COL
        if solved and di != -1: return VALID_COL
        if di == -1:     return UNASSIGNED
        return GALAXY_COLOURS[di % len(GALAXY_COLOURS)]

    def redraw_puzzle(self, grid=None, highlight=None, bt_cells=None, solved=False):
        c  = self.canvas
        N  = self.N
        bt = set(bt_cells or [])
        c.delete("all")

        c.create_rectangle(0, 0, self._canvas_wh(), self._canvas_wh(),
                           fill="#1a1a1a", outline="")

        for cy in range(N):
            for cx in range(N):
                x0, y0 = self._gx(cx),   self._gy(cy)
                x1, y1 = self._gx(cx+1), self._gy(cy+1)
                if grid is not None:
                    di     = grid[cy][cx]
                    colour = self._cell_colour(di,
                                               is_highlight=(highlight==(cx,cy)),
                                               is_backtrack=(cx,cy) in bt,
                                               solved=solved)
                else:
                    colour = BG_INNER
                c.create_rectangle(x0, y0, x1, y1, fill=colour, outline="")

        # grid lines
        for i in range(N+1):
            c.create_line(self._gx(i), self._gy(0), self._gx(i), self._gy(N),
                          fill=GRID_COL, width=1)
            c.create_line(self._gx(0), self._gy(i), self._gx(N), self._gy(i),
                          fill=GRID_COL, width=1)

        # walls (only when solved)
        if solved:
            for edge in self.game.edges:
                t, ex, ey = edge
                if edge in self.game.fixed: continue
                if t == 'v':
                    x = self._gx(ex)
                    c.create_line(x, self._gy(ey), x, self._gy(ey+1),
                                  width=3, fill=WALL_COL, capstyle="projecting")
                else:
                    y = self._gy(ey)
                    c.create_line(self._gx(ex), y, self._gx(ex+1), y,
                                  width=3, fill=WALL_COL, capstyle="projecting")

        # dots with number label
        for di, (dx, dy) in enumerate(self.game.dots):
            px, py = self._gx(dx), self._gy(dy)
            dot_fill = (GALAXY_COLOURS[di % len(GALAXY_COLOURS)]
                        if (grid is not None and not solved) else BG_INNER)
            c.create_oval(px-DOT_R, py-DOT_R, px+DOT_R, py+DOT_R,
                          outline=WALL_COL, fill=dot_fill, width=DOT_W)
            c.create_text(px, py, text=str(di+1),
                          font=("Courier", 6, "bold"), fill=WALL_COL)

        # outer border
        c.create_rectangle(self._gx(0), self._gy(0), self._gx(N), self._gy(N),
                           outline=WALL_COL, width=BORDER_W+2, fill="")

        # gold highlight border around active cell
        if highlight and not solved:
            cx, cy = highlight
            c.create_rectangle(self._gx(cx)+2, self._gy(cy)+2,
                                self._gx(cx+1)-2, self._gy(cy+1)-2,
                                outline="#ffcc00", width=3, fill="")

    # ── playback ──────────────────────────────────────────────────────────────

    def _start_viz(self):
        if self._playing: return
        self.sv.set("Building step list…  (may take a moment for large grids)")
        self.update()

        solver = AnimatedBacktrackSolver(self.game.N, self.game.dots)
        self._steps, _ = solver.build_steps()
        self._step_idx   = 0
        self._total_steps = len(self._steps)
        self._total_bt    = solver.backtracks
        self._total_comp  = solver.computations

        self.viz_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.skip_btn.config(state="normal")
        self._playing = True
        self._play_next()

    def _play_next(self):
        if not self._playing: return
        if self._step_idx >= len(self._steps):
            self._finish(); return

        step = self._steps[self._step_idx]
        self._step_idx += 1

        kind = step["kind"]
        grid = step["grid"]
        hl   = step.get("highlight")
        bt   = step.get("backtrack_cells", [])

        self.redraw_puzzle(grid=grid, highlight=hl,
                           bt_cells=bt, solved=(kind=="done"))

        bt_count = sum(1 for s in self._steps[:self._step_idx]
                       if s["kind"] == "backtrack")
        pct = int(self._step_idx / self._total_steps * 100)
        self.sv.set(
            f"Step {self._step_idx}/{self._total_steps}  ({pct}%)  |  "
            f"{kind.upper():<12}  |  "
            f"Backtracks: {bt_count}  |  "
            f"Cell: {hl if hl else '—'}"
        )

        self._after_id = self.after(self.speed_var.get(), self._play_next)

    def _finish(self):
        self._playing = False
        self.viz_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.skip_btn.config(state="disabled")

        last = self._steps[-1] if self._steps else None
        if last and last["kind"] == "done":
            grid = last["grid"]
            self.game.edges = set(self.game.fixed) | assign_to_edges(grid, self.N)
            self.redraw_puzzle(grid=grid, solved=True)
            self.sv.set(
                f"Solved!  |  Steps: {self._total_steps}  |  "
                f"Backtracks: {self._total_bt}  |  Computations: {self._total_comp}"
            )
            messagebox.showinfo("Galaxies — Solved!",
                                f"Backtracking finished!\n\n"
                                f"Steps visualised : {self._total_steps}\n"
                                f"Computations     : {self._total_comp}\n"
                                f"Backtracks       : {self._total_bt}")
        else:
            self.sv.set("No solution found.")

    def _stop_viz(self):
        if self._after_id: self.after_cancel(self._after_id)
        self._after_id = None
        self._playing  = False
        self.viz_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.skip_btn.config(state="disabled")
        self.sv.set("Stopped. Press 'Visualize Solve' to restart.")

    def _skip_to_end(self):
        if self._after_id: self.after_cancel(self._after_id)
        self._after_id = None
        self._playing  = False
        self._step_idx = len(self._steps)
        self._finish()

    # ── game control ──────────────────────────────────────────────────────────

    def _new_game(self):
        self._stop_viz()
        self._steps = []
        self.game.new_puzzle()
        self.redraw_puzzle()
        self.sv.set("New puzzle loaded. Press 'Visualize Solve'.")

    def _change_diff(self, label):
        self._stop_viz()
        idx       = self.LABELS.index(label)
        self.N    = self.SIZES[idx]
        self.cell = CELL_FOR_SIZE[self.N]
        self.game = GameState(self.N)
        s = self._canvas_wh()
        self.canvas.config(width=s, height=s)
        self.redraw_puzzle()
        self.sv.set(f"Difficulty: {label}. Press 'Visualize Solve'.")


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    GalaxiesUI().mainloop()