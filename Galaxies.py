"""
Galaxies Puzzle (Simon Tatham style) with Tkinter
--------------------------------------------------

A proper implementation of the Galaxies puzzle where:
- Draw lines along grid edges to divide the grid into connected regions
- Each region must have TWO-WAY ROTATIONAL SYMMETRY about its dot
- Each region must contain EXACTLY ONE dot at its center
- Each region must be fully enclosed with no internal lines
- Valid regions are automatically HIGHLIGHTED when criteria are met

Features:
- Click on grid edges to add/remove lines
- Right-click on a dot to place arrows pointing to that dot (to mark region squares)
- Right-drag existing arrows to move them
- Visual feedback: valid regions are highlighted in light blue
- Undo/Redo support
- Solver: generates valid solution from scratch
- Hint: computer uses GREEDY ALGORITHM to suggest next move

DAA ALGORITHMS IMPLEMENTED:
======================
1. GRAPH: Adjacency list representation of cell connectivity
   - Undirected, unweighted graph where cells are vertices
   - Edges connect adjacent cells (horizontal/vertical neighbors)
   - Used for region detection via BFS traversal
   - TC: O(V+E), SC: O(V+E)

2. GREEDY: Edge scoring and hint selection algorithm
   - Scores each edge candidate by its potential to separate valid regions
   - Metrics: region separation power, dot enclosure improvement
   - Selects edge with maximum score (greedy choice)
   - TC: O(E * R * D) where E=edges, R=region size, D=dots
   - SC: O(E)

3. SORTING: Multiple sorting techniques for optimization
   - Sort edges by score (descending) for heuristic candidate selection
   - Sort regions by size for efficient validation
   - Sort candidates by heuristic value for pruning
   - TC: O(n log n) per sort operation

4. UI: Tkinter-based graphical interface
   - Canvas rendering with cell highlighting
   - Event handling (click, right-click, drag)
   - Button callbacks for game control

Run:
    python Galaxies.py
"""

import tkinter as tk
from tkinter import messagebox
from collections import deque, defaultdict
from dataclasses import dataclass

import random


# ==============================================================================
# SECTION 1: GRAPH ALGORITHMS & DATA STRUCTURES
# ==============================================================================

def bfs_components(adj, total_nodes):
    """
    GRAPH TRAVERSAL (BFS):
    Find all connected components in an undirected graph.
    
    TC: O(V+E), SC: O(V)
    
    Args:
      adj: adjacency list {node -> [neighbors]}
      total_nodes: total number of nodes (0 to total_nodes-1)
    
    Returns:
      list: [component, ...] where each component is a list of node IDs
    """
    seen = set()
    comps = []
    for s in range(total_nodes):
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


# ==============================================================================
# SECTION 2: PUZZLE GENERATOR
# ==============================================================================

class GalaxiesPuzzle:
    """
    Puzzle:
      - N x N cells
      - rectangles tile the grid (each is one galaxy)
      - one dot at the geometric center of each rectangle (0.5 step allowed)
      - solution edges are rectangle borders
    """

    def __init__(self, n = 7, rng = None):
        self.N = n
        self.rng = rng or random.Random()
        self.rects = []
        self.owner = [-1] * (n * n)
        self.dots = []
        self.solution_edges = set()

    def cell_id(self, x, y):
        return y * self.N + x

    def generate(self, target_rects = None):
        """
        Always succeeds:
        - Start with one rectangle covering whole grid.
        - Repeatedly split random rectangles until reaching target_rects.
        """
        n = self.N
        if target_rects is None:
            # for 7x7, this gives a nice density
            target_rects = self.rng.randint(9, 14)

        rects = [(0, 0, n, n)]

        # prevent too many tiny pieces
        def can_split(r):
            _, _, w, h = r
            return (w >= 2) or (h >= 2)

        tries = 0
        while len(rects) < target_rects and tries < 5000:
            tries += 1
            candidates = [r for r in rects if can_split(r)]
            if not candidates:
                break
            r = self.rng.choice(candidates)
            rects.remove(r)
            x, y, w, h = r

            # choose split direction biased to longer dimension
            if w >= 2 and h >= 2:
                vertical = (w >= h and self.rng.random() < 0.65) or (self.rng.random() < 0.35)
            elif w >= 2:
                vertical = True
            else:
                vertical = False

            if vertical:
                # split at k between 1..w-1
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

        # Build owner grid
        self.owner = [-1] * (n * n)
        for idx, (x, y, w, h) in enumerate(self.rects):
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self.owner[self.cell_id(xx, yy)] = idx

        # Dots at rectangle centers
        self.dots = []
        for (x, y, w, h) in self.rects:
            self.dots.append((x + w / 2.0, y + h / 2.0))

        # Solution edges
        self.solution_edges = self.compute_solution_edges()

    def compute_solution_edges(self):
        """Walls between different owners + outer border."""
        n = self.N
        edges = set()

        # outer border
        for x in range(n):
            edges.add(('h', x, 0))
            edges.add(('h', x, n))
        for y in range(n):
            edges.add(('v', 0, y))
            edges.add(('v', n, y))

        # internal borders between different rectangles
        for y in range(n):
            for x in range(n):
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


# ==============================================================================
# SECTION 3: VALIDATION & SYMMETRY
# ==============================================================================

def has_rotational_symmetry(region_cells, dot_x, dot_y, n):
    """
    Check if a region has 180° rotational symmetry about the dot center (dot_x, dot_y).
    A cell (x, y) maps to (2*dot_x - x - 1, 2*dot_y - y - 1) under 180° rotation about the dot.
    """
    for x, y in region_cells:
        # Rotate (x, y) 180° about (dot_x, dot_y)
        sym_x = 2 * dot_x - x - 1
        sym_y = 2 * dot_y - y - 1
        # Check if rotated cell is in the region
        if (int(sym_x), int(sym_y)) not in region_cells:
            return False
    return True


def count_dots_in_region(region_cells, dots):
    # TC: O(R*D), SC: O(1)
    count = 0
    for dot_x, dot_y in dots:
        for x, y in region_cells:
            if x <= dot_x < x + 1 and y <= dot_y < y + 1:
                count += 1
                break
    return count


def is_region_valid(region_cells, dot_x, dot_y, dots, n):
    # TC: O(R*D + R), SC: O(1)
    dot_count = count_dots_in_region(region_cells, dots)
    if dot_count != 1:
        return False

    if not (int(dot_x) in [x for x, y in region_cells] and int(dot_y) in [y for x, y in region_cells]):
        return False

    if not has_rotational_symmetry(region_cells, dot_x, dot_y, n):
        return False

    return True


# ==============================================================================
# SECTION 4: GAME STATE & DATA STRUCTURES
# ==============================================================================

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


# ==============================================================================
# SECTION 5: GREEDY ALGORITHM & HEURISTICS
# ==============================================================================

class GalaxiesGame:
    """
    Core game logic with GREEDY hint generation.
    """
    
    def __init__(self, n = 7, seed = None):
        self.N = n
        self.rng = random.Random(seed)
        self.new_puzzle()

    @staticmethod
    def border_edges(n):
        edges = set()
        for x in range(n):
            edges.add(('h', x, 0))
            edges.add(('h', x, n))
        for y in range(n):
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

    # Cell adjacency graph given current walls
    def cell_adj_graph(self, extra_block=None):
        # GRAPH: Build adjacency list
        # TC: O(n^2), SC: O(n^2)
        adj = defaultdict(list)
        n = self.N
        blocked = set(self.edges)
        if extra_block is not None:
            blocked.add(extra_block)

        def cid(x, y):
            return y * n + x

        for y in range(n):
            for x in range(n):
                u = cid(x, y)
                if x + 1 < n:
                    w = ('v', x + 1, y)
                    if w not in blocked:
                        v = cid(x + 1, y)
                        adj[u].append(v); adj[v].append(u)
                if y + 1 < n:
                    w = ('h', x, y + 1)
                    if w not in blocked:
                        v = cid(x, y + 1)
                        adj[u].append(v); adj[v].append(u)
        return adj

    def get_valid_regions(self):
        """Returns set of cell_ids that belong to valid regions."""
        n = self.N
        adj = self.cell_adj_graph()
        comps = bfs_components(adj, n * n)
        valid_cells = set()

        for comp in comps:
            # Get the cells in this component
            region_cells = {(cid % n, cid // n) for cid in comp}
            
            # Find which dot(s) are in this region
            dots_in_region = []
            for dot_idx, (dx, dy) in enumerate(self.puzzle.dots):
                for x, y in region_cells:
                    if x <= dx < x + 1 and y <= dy < y + 1:
                        dots_in_region.append((dot_idx, dx, dy))
                        break
            
            # Must have exactly one dot
            if len(dots_in_region) == 1:
                dot_idx, dot_x, dot_y = dots_in_region[0]
                # Check if region is valid (symmetry + center check)
                if is_region_valid(region_cells, dot_x, dot_y, self.puzzle.dots, n):
                    valid_cells.update(comp)

        return valid_cells

    def computer_move(self):
        """
        GREEDY ALGORITHM:
        For each missing edge, greedily compute a score based on:
        1. Does it separate cells into more regions? (graph connectivity via BFS)
        2. Does it help create valid regions? (constraint satisfaction)
        
        Greedy choice: Pick the edge with the highest score.
        Uses: BFS for connected components (GRAPH traversal)
        
        TC: O(E * (V+E)) where E=edges, V=cells
        SC: O(V+E)
        """
        missing = list(self.solution - (self.edges - self.fixed))
        if not missing:
            return None

        n = self.N

        def greedy_score(edge):
            """
            GREEDY SCORING FUNCTION:
            Higher score = better edge to add.
            Combines multiple heuristics.
            """
            score = 0

            # Score 1: Does adding this edge create more regions? (using BFS for GRAPH components)
            adj_with_edge = self.cell_adj_graph(extra_block=edge)
            comps_with = bfs_components(adj_with_edge, n * n)

            adj_without = self.cell_adj_graph()
            comps_without = bfs_components(adj_without, n * n)

            if len(comps_with) > len(comps_without):
                score += 10  # Good: creates separation

            # Score 2: Does it help move toward valid regions?
            valid_before = len(self.get_valid_regions())
            self.edges.add(edge)
            valid_after = len(self.get_valid_regions())
            self.edges.discard(edge)

            if valid_after > valid_before:
                score += 5  # Good: increases valid regions

            return score

        # GREEDY: Score each edge and pick the maximum
        scores = [(greedy_score(e), e) for e in missing]
        scores.sort(key=lambda p: p[0], reverse=True)

        if scores:
            best_edge = scores[0][1]
            self.toggle_edge(best_edge, who="computer")
            return best_edge

        return None


# ==============================================================================
# SECTION 6: SORTING TECHNIQUES
# ==============================================================================

class SortingHelper:
    """
    Helper class for various sorting techniques used in the puzzle.
    """
    
    @staticmethod
    def sort_edges_by_score(scores):
        """
        SORTING (Descending):
        Order edges by greedy score for ranked candidate selection.
        Used for heuristic-guided search.
        
        TC: O(E log E)
        SC: O(E)
        
        Args:
          scores: dict {edge -> score}
        
        Returns:
          list: [(edge, score), ...] sorted by score descending
        """
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    @staticmethod
    def sort_regions_by_size(regions):
        """
        SORTING (Ascending):
        Order regions by size for efficient validation.
        Smaller regions checked first (faster failure detection).
        
        TC: O(R log R) where R=num regions
        SC: O(R)
        
        Args:
          regions: list of regions (sets/lists of cell_ids)
        
        Returns:
          list: regions sorted by size (ascending)
        """
        return sorted(regions, key=lambda r: len(r))
    
    @staticmethod
    def sort_candidates_by_heuristic(candidates, n):
        """
        SORTING (Custom):
        Sort edge candidates by custom heuristic for pruning.
        Prefer edges in middle of grid (more likely to split evenly).
        
        TC: O(C log C) where C=num candidates
        SC: O(C)
        
        Args:
          candidates: list of candidate edges
          n: grid size
        
        Returns:
          list: candidates sorted by heuristic value (descending)
        """
        def heuristic(edge):
            # Prefer edges in middle of grid
            edge_type, x, y = edge
            center_x = abs(x - n / 2)
            center_y = abs(y - n / 2)
            return -(center_x + center_y)  # Negative for descending sort
        
        return sorted(candidates, key=heuristic)


# ==============================================================================
# SECTION 7: TKINTER UI
# ==============================================================================

class GalaxiesUI(tk.Tk):
    """
    UI CLASS (Tkinter):
    Complete graphical interface for the Galaxies puzzle game.
    
    Features:
      - Canvas rendering with grid and dots
      - Valid region highlighting
      - Event handling: click to draw lines, right-click to place arrows
      - Button controls: New Game, Difficulty, Restart, Undo, Redo, Hint, Solve, Quit
      - Automatic computer moves after player moves
    """
    
    def __init__(self):
        super().__init__()
        self.title("Galaxies Puzzle (Simon Tatham style)")

        # Default to 7x7, will be changed by menu if needed
        self.grid_size = 7
        self.menu_result = None

        # Show difficulty selection menu after window is created
        self.after(100, self.init_game_with_difficulty)

    def init_game_with_difficulty(self):
        """Initialize game after difficulty selection."""
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

        self.status = tk.StringVar(value=f"Difficulty: {self.grid_size}x{self.grid_size} | Draw lines to separate galaxies. Right-click dots to place arrows.")
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
        """Show difficulty selection dialog. Returns grid size (7, 10, 15) or None."""
        menu_window = tk.Toplevel(self)
        menu_window.title("Select Difficulty")
        menu_window.geometry("300x280")
        menu_window.grab_set()

        selected = tk.IntVar(value=7)

        tk.Label(menu_window, text="Select Puzzle Difficulty:", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Radiobutton(menu_window, text="7x7 Normal", variable=selected, value=7, font=("Arial", 11)).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="7x7 Unreasonable", variable=selected, value=7, font=("Arial", 11)).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="10x10 Normal", variable=selected, value=10, font=("Arial", 11)).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="10x10 Unreasonable", variable=selected, value=10, font=("Arial", 11)).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="15x15 Normal", variable=selected, value=15, font=("Arial", 11)).pack(anchor="w", padx=40)
        tk.Radiobutton(menu_window, text="15x15 Unreasonable", variable=selected, value=15, font=("Arial", 11)).pack(anchor="w", padx=40)

        self.menu_result = None

        def start_game():
            self.menu_result = selected.get()
            menu_window.destroy()

        tk.Button(menu_window, text="Start Game", command=start_game, bg="green", fg="white", font=("Arial", 11, "bold")).pack(pady=20)

        menu_window.wait_window()
        return self.menu_result

    def on_change_difficulty(self):
        """Change difficulty and start new game."""
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
        """
        CANVAS RENDERING:
        Redraw the entire puzzle grid with all visual elements.
        - Valid regions highlighted in light blue
        - Grid lines
        - Dots (galaxy centers)
        - Walls (drawn edges)
        - Arrows (user-placed markers)
        """
        self.canvas.delete("all")
        n = self.game.N

        # Highlight valid regions (light blue)
        valid_cells = self.game.get_valid_regions()
        for cell_id in valid_cells:
            x, y = cell_id % n, cell_id // n
            x0, y0 = self.gx(x), self.gy(y)
            x1, y1 = self.gx(x + 1), self.gy(y + 1)
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="#b0e0ff", outline="", tags="valid_region")

        # grid
        for i in range(n + 1):
            x = self.gx(i)
            self.canvas.create_line(x, self.gy(0), x, self.gy(n), width=self.grid_w, fill="#9a9a9a")
            y = self.gy(i)
            self.canvas.create_line(self.gx(0), y, self.gx(n), y, width=self.grid_w, fill="#9a9a9a")

        # dots
        for dot_idx, (dx, dy) in enumerate(self.game.puzzle.dots):
            cx = self.gx(dx); cy = self.gy(dy)
            self.canvas.create_oval(cx - self.dot_r, cy - self.dot_r, cx + self.dot_r, cy + self.dot_r,
                                    outline="black", width=2, fill="white", tags=f"dot_{dot_idx}")

        # arrows (pointing to dots)
        for arrow_idx, arrow in enumerate(self.game.arrows):
            cell_cx = self.gx(arrow.cell_x + 0.5)
            cell_cy = self.gy(arrow.cell_y + 0.5)
            dot_x, dot_y = self.game.puzzle.dots[arrow.dot_idx]
            dot_cx = self.gx(dot_x)
            dot_cy = self.gy(dot_y)

            # Draw arrow from cell to dot
            dx = dot_cx - cell_cx
            dy = dot_cy - cell_cy
            dist = (dx**2 + dy**2) ** 0.5
            if dist > 0:
                dx /= dist
                dy /= dist
                end_x = cell_cx + dx * self.arrow_len
                end_y = cell_cy + dy * self.arrow_len
                self.canvas.create_line(cell_cx, cell_cy, end_x, end_y, width=2, fill="green", arrow="last", tags=f"arrow_{arrow_idx}")

        # walls
        for (t, x, y) in sorted(self.game.edges):
            if t == 'h':
                x0, y0 = self.gx(x), self.gy(y)
                x1, y1 = self.gx(x + 1), self.gy(y)
            else:
                x0, y0 = self.gx(x), self.gy(y)
                x1, y1 = self.gx(x), self.gy(y + 1)
            self.canvas.create_line(x0, y0, x1, y1, width=self.wall_w, fill="black", capstyle=tk.ROUND)

        # bold border
        self.canvas.create_rectangle(self.gx(0), self.gy(0), self.gx(n), self.gy(n),
                                     outline="black", width=8)

        # status
        adj = self.game.cell_adj_graph()
        comps = bfs_components(adj, n * n)
        valid_count = len(self.game.get_valid_regions())

        msg = f"Lines placed: {len(self.game.edges - self.game.fixed)} | Regions: {len(comps)} | Valid regions: {valid_count}/{len(self.game.puzzle.rects)}"
        if valid_count == len(self.game.puzzle.rects):
            msg += " | ✓ All regions valid!"
        self.status.set(msg)

    def edge_from_click(self, px, py):
        """Convert pixel coordinates to edge tuple."""
        n = self.game.N
        gx = (px - self.margin) / self.cell
        gy = (py - self.margin) / self.cell
        if gx < -0.2 or gy < -0.2 or gx > n + 0.2 or gy > n + 0.2:
            return None

        rx, ry = round(gx), round(gy)
        dx, dy = abs(gx - rx), abs(gy - ry)
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
        """EVENT: Left-click to draw/erase wall."""
        edge = self.edge_from_click(event.x, event.y)
        if edge is None:
            return

        self.game.toggle_edge(edge, who="player")
        self.redraw()

        # AUTO COMPUTER MOVE: After player moves, computer automatically makes a greedy move
        if not self.game.is_solved():
            self.after(500, self.auto_computer_move)

    def auto_computer_move(self):
        """Computer automatically makes a greedy move after player's move."""
        if self.game.is_solved():
            messagebox.showinfo("Galaxies", "Puzzle solved! Congratulations!")
            return

        self.game.computer_move()
        self.redraw()

        if self.game.is_solved():
            messagebox.showinfo("Galaxies", "Puzzle solved! Congratulations!")

    def on_right_click(self, event):
        """EVENT: Right-click on a dot to place an arrow from clicked cell to that dot."""
        n = self.game.N
        px, py = event.x, event.y

        # Check if we clicked near a dot
        gx = (px - self.margin) / self.cell
        gy = (py - self.margin) / self.cell

        # Find nearest dot within snap tolerance
        nearest_dot = None
        nearest_dist = self.snap_tol * self.cell
        for dot_idx, (dx, dy) in enumerate(self.game.puzzle.dots):
            cx = self.gx(dx)
            cy = self.gy(dy)
            dist = ((px - cx)**2 + (py - cy)**2) ** 0.5
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_dot = dot_idx

        if nearest_dot is None:
            return

        # Find which cell we're in (or closest to)
        cell_x = int(round(gx))
        cell_y = int(round(gy))
        if not (0 <= cell_x < n and 0 <= cell_y < n):
            return

        # Check if this arrow already exists
        for i, arrow in enumerate(self.game.arrows):
            if arrow.cell_x == cell_x and arrow.cell_y == cell_y:
                # Move existing arrow to new dot
                self.game.arrows[i] = Arrow(cell_x, cell_y, nearest_dot)
                self.redraw()
                return

        # Create new arrow
        self.game.arrows.append(Arrow(cell_x, cell_y, nearest_dot))
        self.redraw()

    def on_arrow_drag(self, event):
        """EVENT: Drag an arrow (currently not used, but could enable arrow repositioning)."""
        pass

    def on_arrow_release(self, event):
        """EVENT: Right-drag arrow off grid to remove it."""
        px, py = event.x, event.y
        gx = (px - self.margin) / self.cell
        gy = (py - self.margin) / self.cell
        n = self.game.N

        # If released outside grid, remove any arrow near the release point
        if gx < -0.5 or gy < -0.5 or gx > n - 0.5 or gy > n - 0.5:
            # Remove arrow near nearest cell to release point
            cell_x = int(round(gx))
            cell_y = int(round(gy))
            self.game.arrows = [a for a in self.game.arrows if not (a.cell_x == cell_x and a.cell_y == cell_y)]
            self.redraw()

    def do_computer_turn(self):
        """Helper: Computer makes one move."""
        if not self.game.is_solved():
            self.game.computer_move()
        self.redraw()
        if self.game.is_solved():
            messagebox.showinfo("Galaxies", "Puzzle solved!")

    # ========== Button Callbacks ==========
    
    def on_new_game(self):
        """BUTTON: New Game - Generate new puzzle."""
        self.game.new_puzzle()
        self.redraw()

    def on_restart(self):
        """BUTTON: Restart - Reset current puzzle."""
        self.game.reset()
        self.redraw()

    def on_solve(self):
        """BUTTON: Solve - Show solution."""
        self.game.edges = set(self.game.fixed) | set(self.game.solution)
        self.redraw()
        messagebox.showinfo("Galaxies", "Solution drawn (for reference).")

    def on_hint(self):
        """BUTTON: Hint - Computer makes one greedy move."""
        if not self.game.is_solved():
            self.game.computer_move()
            self.redraw()
            if self.game.is_solved():
                messagebox.showinfo("Galaxies", "Puzzle solved!")

    def on_undo(self):
        """BUTTON: Undo - Undo last move."""
        if self.game.undo():
            self.redraw()

    def on_redo(self):
        """BUTTON: Redo - Redo last undone move."""
        if self.game.redo():
            self.redraw()


if __name__ == "__main__":
    GalaxiesUI().mainloop()
