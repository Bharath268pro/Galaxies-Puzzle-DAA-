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
    return val // 1

def my_round(val):
    r = val // 1
    if val - r >= 0.5: r += 1
    return r

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
    lst = []
    for x in iterable: lst.append(x)
    n = my_len(lst)
    i = 0
    while i < n:
        j = 0
        while j < n - i - 1:
            val1 = lst[j] if key is None else key(lst[j])
            val2 = lst[j+1] if key is None else key(lst[j+1])
            swap = False
            if reverse:
                if val1 < val2: swap = True
            else:
                if val1 > val2: swap = True
            if swap:
                temp = lst[j]
                lst[j] = lst[j+1]
                lst[j+1] = temp
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

    def generate(self, target_rects=None):
        n = self.N
        if target_rects is None:
            target_rects = self.rng.randint(9, 14)

        rects = [(0, 0, n, n)]

        def can_split(r):
            _, _, w, h = r
            return w >= 2 or h >= 2

        tries = 0
        while my_len(rects) < target_rects and tries < 5000:
            tries += 1
            candidates = [r for r in rects if can_split(r)]
            if not candidates:
                break
            r = self.rng.choice(candidates)
            rects.remove(r)
            x, y, w, h = r

            if w >= 2 and h >= 2:
                vertical = (w >= h and self.rng.random() < 0.65) or (self.rng.random() < 0.35)
            elif w >= 2:
                vertical = True
            else:
                vertical = False

            if vertical:
                k = self.rng.randint(1, w - 1)
                r1 = (x, y, k, h)
                r2 = (x + k, y, w - k, h)
            else:
                k = self.rng.randint(1, h - 1)
                r1 = (x, y, w, k)
                r2 = (x, y + k, w, h - k)

            rects.append(r1)
            rects.append(r2)

        self.rects = rects

        self.owner = [-1] * (n * n)
        for idx, (x, y, w, h) in my_enumerate(self.rects):
            for yy in my_range(y, y + h):
                for xx in my_range(x, x + w):
                    self.owner[self.cell_id(xx, yy)] = idx

        self.dots = []
        for (x, y, w, h) in self.rects:
            self.dots.append((x + w / 2.0, y + h / 2.0))

        self.solution_edges = self.compute_solution_edges()

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
        if (my_int(sym_x), my_int(sym_y)) not in region_cells:
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

    if not (my_int(dot_x) in [x for x, y in region_cells] and my_int(dot_y) in [y for x, y in region_cells]):
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
            if (my_int(sym_x), my_int(sym_y)) not in region_cells:
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
        
        if not (my_int(dot_x) in [x for x, y in region_cells] and my_int(dot_y) in [y for x, y in region_cells]):
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

    def computer_move(self):
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
        super().__init__()
        self.title("Galaxies Puzzle")

        self.grid_size = 4
        self.menu_result = None

        self.after(100, self.init_game_with_difficulty)

    def init_game_with_difficulty(self):
        self.show_difficulty_menu()

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
        self.snap_tol = 0.18
        self.arrow_len = 12

        n = self.game.N
        w = self.margin * 2 + self.cell * n
        h = self.margin * 2 + self.cell * n

        self.canvas = tk.Canvas(self, width=w, height=h, bg="#d8d8d8", highlightthickness=0)
        self.canvas.grid(row=0, column=0, columnspan=7, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<B3-Motion>", self.on_arrow_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_arrow_release)

        self.dragging_arrow = None

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
        menu_window.geometry("300x320")
        menu_window.grab_set()

        selected = tk.IntVar(value=4)

        tk.Label(menu_window, text="Select Puzzle Difficulty:").pack(pady=10)

        tk.Radiobutton(menu_window, text="4x4 (Pure D&C safe)", variable=selected, value=4).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="7x7 Normal", variable=selected, value=7).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="7x7 Unreasonable", variable=selected, value=7).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="10x10 Normal", variable=selected, value=10).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="10x10 Unreasonable", variable=selected, value=10).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="15x15 Normal", variable=selected, value=15).pack(anchor="w", padx=40)

        self.menu_result = None

        def start_game():
            self.menu_result = selected.get()
            menu_window.destroy()

        tk.Button(menu_window, text="Start Game", command=start_game, bg="green", fg="white").pack(pady=20)

        menu_window.wait_window()
        return self.menu_result

    def on_change_difficulty(self):
        new_size = self.show_difficulty_menu()
        if new_size is not None and new_size != self.grid_size:
            self.grid_size = new_size
            self.game = GalaxiesGame(n=self.grid_size)
            self.cell = 40 if self.grid_size >= 15 else (50 if self.grid_size >= 10 else 60)
            self.dot_r = 7 if self.grid_size >= 15 else 9
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
            self.canvas.create_oval(cx - self.dot_r, cy - self.dot_r, cx + self.dot_r, cy + self.dot_r,
                                    outline="black", width=2, fill="white", tags=f"dot_{dot_idx}")

        for arrow_idx, arrow in my_enumerate(self.game.arrows):
            cell_cx = self.gx(arrow.cell_x + 0.5)
            cell_cy = self.gy(arrow.cell_y + 0.5)
            dot_x, dot_y = self.game.puzzle.dots[arrow.dot_idx]
            dot_cx = self.gx(dot_x)
            dot_cy = self.gy(dot_y)

            dx = dot_cx - cell_cx
            dy = dot_cy - cell_cy
            dist = (dx**2 + dy**2) ** 0.5
            if dist > 0:
                dx /= dist
                dy /= dist
                end_x = cell_cx + dx * self.arrow_len
                end_y = cell_cy + dy * self.arrow_len
                self.canvas.create_line(cell_cx, cell_cy, end_x, end_y, width=2, fill="green", arrow="last", tags=f"arrow_{arrow_idx}")

        for (t, x, y) in my_sorted(self.game.edges):
            if t == 'h':
                x0, y0 = self.gx(x), self.gy(y)
                x1, y1 = self.gx(x + 1), self.gy(y)
            else:
                x0, y0 = self.gx(x), self.gy(y)
                x1, y1 = self.gx(x), self.gy(y + 1)
            self.canvas.create_line(x0, y0, x1, y1, width=self.wall_w, fill="black", capstyle=tk.ROUND)

        self.canvas.create_rectangle(self.gx(0), self.gy(0), self.gx(n), self.gy(n),
                                     outline="black", width=8)

        adj = self.game.cell_adj_graph()
        comps = bfs_components(adj, n * n)
        valid_count = my_len(self.game.get_valid_regions())

        msg = f"Lines placed: {my_len(self.game.edges - self.game.fixed)} | Regions: {my_len(comps)} | Valid regions: {valid_count}/{my_len(self.game.puzzle.rects)}"
        self.status.set(msg)

    def edge_from_click(self, px, py):
        n = self.game.N
        gx = (px - self.margin) / self.cell
        gy = (py - self.margin) / self.cell
        if gx < -0.2 or gy < -0.2 or gx > n + 0.2 or gy > n + 0.2:
            return None

        rx, ry = my_round(gx), my_round(gy)
        dx, dy = my_abs(gx - rx), my_abs(gy - ry)
        if my_min([dx, dy]) > self.snap_tol:
            return None

        if dx < dy:
            x = my_int(rx)
            y = my_int(gy)
            if 0 <= x <= n and 0 <= y < n:
                return ('v', x, y)
        else:
            x = my_int(gx)
            y = my_int(ry)
            if 0 <= x < n and 0 <= y <= n:
                return ('h', x, y)
        return None

    def on_click(self, event):
        edge = self.edge_from_click(event.x, event.y)
        if edge is None:
            return

        self.game.toggle_edge(edge, who="player")
        self.redraw()

        if not self.game.is_solved():
            self.after(500, self.auto_computer_move)

    def auto_computer_move(self):
        if self.game.is_solved():
            return

        self.game.computer_move()
        self.redraw()

        if self.game.is_solved():
            pass

    def on_right_click(self, event):
        n = self.game.N
        px, py = event.x, event.y

        gx = (px - self.margin) / self.cell
        gy = (py - self.margin) / self.cell

        nearest_dot = None
        nearest_dist = self.snap_tol * self.cell
        for dot_idx, (dx, dy) in my_enumerate(self.game.puzzle.dots):
            cx = self.gx(dx)
            cy = self.gy(dy)
            dist = ((px - cx)**2 + (py - cy)**2) ** 0.5
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_dot = dot_idx

        if nearest_dot is None:
            return

        cell_x = my_int(my_round(gx))
        cell_y = my_int(my_round(gy))
        if not (0 <= cell_x < n and 0 <= cell_y < n):
            return

        for i, arrow in my_enumerate(self.game.arrows):
            if arrow.cell_x == cell_x and arrow.cell_y == cell_y:
                self.game.arrows[i] = Arrow(cell_x, cell_y, nearest_dot)
                self.redraw()
                return

        self.game.arrows.append(Arrow(cell_x, cell_y, nearest_dot))
        self.redraw()

    def on_arrow_drag(self, event):
        pass

    def on_arrow_release(self, event):
        px, py = event.x, event.y
        gx = (px - self.margin) / self.cell
        gy = (py - self.margin) / self.cell
        n = self.game.N

        if gx < -0.5 or gy < -0.5 or gx > n - 0.5 or gy > n - 0.5:
            cell_x = my_int(my_round(gx))
            cell_y = my_int(my_round(gy))
            new_arrows = []
            for a in self.game.arrows:
                if not (a.cell_x == cell_x and a.cell_y == cell_y):
                    new_arrows.append(a)
            self.game.arrows = new_arrows
            self.redraw()

    def do_computer_turn(self):
        if not self.game.is_solved():
            self.game.computer_move()
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
            self.game.computer_move()
            self.redraw()

    def on_undo(self):
        if self.game.undo():
            self.redraw()

    def on_redo(self):
        if self.game.redo():
            self.redraw()

if __name__ == "__main__":
    GalaxiesUI().mainloop()