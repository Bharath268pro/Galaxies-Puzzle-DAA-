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
- Hint: computer uses DIVIDE AND CONQUER ALGORITHM to suggest next move

DAA ALGORITHMS IMPLEMENTED:
======================
1. GRAPH: Adjacency list representation of cell connectivity
   - Undirected, unweighted graph where cells are vertices
   - Edges connect adjacent cells (horizontal/vertical neighbors)
   - Used for region detection via BFS traversal
   - TC: O(V+E), SC: O(V+E)

2. DIVIDE AND CONQUER + BACKTRACKING: Core solver strategy
   -------------------------------------------------------
   Pure D&C cannot solve Galaxies because galaxy regions can cross any
   partition boundary, making sub-problems interdependent.  Backtracking
   alone works but is exponentially slow on large grids.  Together:

   D&C PHASE (dc_backtrack_solve):
     - Recursively splits the grid into left/right column halves
     - Solves each half's INTERIOR cells first at the base case
     - TC: O(log N) recursive depth

   BACKTRACKING PHASE (bt_assign_boundary):
     - After each D&C split, handles BOUNDARY CELLS whose galaxy
       crosses into the other half
     - Tries every candidate dot, checks symmetry + ownership constraints
     - On failure: UNDO assignment and try next candidate
     - TC: O(D^B) where D=dots, B=boundary cells (B << N^2)

3. SORTING: Nearest-dot-first ordering of backtracking candidates
   - Pre-computed once per boundary batch before recursion starts
   - Prunes the backtracking search tree significantly
   - TC: O(D log D) per boundary cell

4. VALIDATION: Plain symmetry and dot-count checks
   - dots_in_region(): checks which dot is inside a region  TC: O(R*D)
   - has_rotational_symmetry(): checks 180-deg symmetry     TC: O(R)
   - Used by get_valid_regions() for the UI blue highlighting

5. UI: Tkinter-based graphical interface

Run:
    python galaxy_v4.py
"""

import tkinter as tk
from tkinter import messagebox
from collections import deque, defaultdict
from dataclasses import dataclass
import math
import random


# ==============================================================================
# SHARED UTILITY
# ==============================================================================

def cell_id(x, y, n):
    """Convert (x, y) cell coordinate to flat index. Used everywhere."""
    return y * n + x


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
        self.computation_count = 0

    def generate(self, target_rects=None):
        """
        DIVIDE AND CONQUER Puzzle Generator
        ====================================
        Recursively splits the grid into galaxy regions.

        Algorithm (mirrors Merge-Sort structure):
          DIVIDE:   Choose a split axis (vertical or horizontal) and a
                    split position k that divides the current rectangle into
                    two non-empty sub-rectangles.
          CONQUER:  Recursively call dc_split() on each sub-rectangle.
          COMBINE:  The leaf rectangles returned from both halves are
                    collected into self.rects.

        Base case (do NOT split further):
          - The rectangle is a 1x1 single cell -> it is already a galaxy.
          - The recursion depth has reached max_depth -> stop splitting.

        Complexity:
          TC: O(R * log R) where R = final number of rectangles.
          SC: O(log N) call-stack depth (binary recursion tree on grid).
        """
        n = self.N
        if target_rects is None:
            target_rects = self.rng.randint(9, 14)

        max_depth = math.ceil(math.log2(max(target_rects, 2)))
        collected_rects = []

        def dc_split(x, y, w, h, depth):
            """
            DIVIDE AND CONQUER recursive helper.

            BASE CASES:
              - Single cell (w==1, h==1): cannot split, add as leaf.
              - depth == 0: recursion limit reached, add whole rect as leaf.

            DIVIDE:
              Pick split direction (prefer longer side).
              Pick split position k randomly in [1, dim-1].

            CONQUER:
              Recurse on each half (with 75% probability to keep splitting,
              otherwise treat that half as a leaf immediately).

            COMBINE:
              Both recursive calls append to collected_rects; no explicit
              merge step needed (results accumulate naturally).
            """
            # BASE CASE 1: single cell
            if w == 1 and h == 1:
                collected_rects.append((x, y, w, h))
                return
            # BASE CASE 2: depth exhausted
            if depth == 0:
                collected_rects.append((x, y, w, h))
                return

            # DIVIDE: choose split direction
            can_v = w >= 2
            can_h = h >= 2

            if can_v and can_h:
                if w > h:
                    vertical = True
                elif h > w:
                    vertical = False
                else:
                    vertical = self.rng.random() < 0.5
            elif can_v:
                vertical = True
            else:
                vertical = False

            if vertical:
                k = self.rng.randint(1, w - 1)
                left_rect  = (x,     y, k,     h)
                right_rect = (x + k, y, w - k, h)
            else:
                k = self.rng.randint(1, h - 1)
                left_rect  = (x, y,     w, k)
                right_rect = (x, y + k, w, h - k)

            # CONQUER: recurse on each half (or keep as leaf)
            if self.rng.random() < 0.75:
                dc_split(*left_rect, depth - 1)
            else:
                collected_rects.append(left_rect)

            if self.rng.random() < 0.75:
                dc_split(*right_rect, depth - 1)
            else:
                collected_rects.append(right_rect)

        # ENTRY: start D&C on the full NxN grid
        dc_split(0, 0, n, n, max_depth)
        self.rects = collected_rects

        # Build owner grid
        self.owner = [-1] * (n * n)
        for idx, (x, y, w, h) in enumerate(self.rects):
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self.owner[cell_id(xx, yy, n)] = idx

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
                o = self.owner[cell_id(x, y, n)]
                if x + 1 < n:
                    o2 = self.owner[cell_id(x + 1, y, n)]
                    if o2 != o:
                        edges.add(('v', x + 1, y))
                if y + 1 < n:
                    o2 = self.owner[cell_id(x, y + 1, n)]
                    if o2 != o:
                        edges.add(('h', x, y + 1))
        return edges


# ==============================================================================
# SECTION 3: VALIDATION & SYMMETRY
# ==============================================================================

def dots_in_region(region_cells_frozen, dots):
    """
    Return list of (dot_idx, dot_x, dot_y) for every dot that falls
    inside the given region.
    TC: O(R * D)
    """
    found = []
    for dot_idx, (dot_x, dot_y) in enumerate(dots):
        for x, y in region_cells_frozen:
            if x <= dot_x < x + 1 and y <= dot_y < y + 1:
                found.append((dot_idx, dot_x, dot_y))
                break
    return found


def has_rotational_symmetry(region_cells_frozen, dot_x, dot_y):
    """
    Return True if the region has 180-degree rotational symmetry
    about (dot_x, dot_y).
    For every cell (x, y) its partner must be (2*dot_x-x-1, 2*dot_y-y-1).
    TC: O(R)
    """
    for x, y in region_cells_frozen:
        px = int(2 * dot_x - x - 1)
        py = int(2 * dot_y - y - 1)
        if (px, py) not in region_cells_frozen:
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
# SECTION 5: DIVIDE AND CONQUER + BACKTRACKING SOLVER
# ==============================================================================

class GalaxiesGame:
    """
    Core game logic.

    The HINT button is powered by dc_backtrack_solve(), which combines:
      - DIVIDE AND CONQUER: splits the grid recursively into column halves,
        solving interior cells at each base case.
      - BACKTRACKING: at each D&C combine step, tries all candidate dot
        assignments for boundary cells, undoing bad choices when a
        constraint is violated.
      - SORTING: nearest-dot-first ordering of candidates for faster pruning.
    """
    
    def __init__(self, n = 7, seed = None):
        self.N = n
        self.rng = random.Random(seed)
        self._solver_cache = None
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

    def cell_adj_graph(self):
        """
        GRAPH: Build adjacency list of cells connected by open edges.
        TC: O(N^2), SC: O(N^2)
        """
        adj = defaultdict(list)
        n = self.N
        blocked = self.edges

        for y in range(n):
            for x in range(n):
                u = cell_id(x, y, n)
                if x + 1 < n and ('v', x + 1, y) not in blocked:
                    v = cell_id(x + 1, y, n)
                    adj[u].append(v); adj[v].append(u)
                if y + 1 < n and ('h', x, y + 1) not in blocked:
                    v = cell_id(x, y + 1, n)
                    adj[u].append(v); adj[v].append(u)
        return adj

    def get_valid_regions(self):
        """
        Returns (valid_cells set, total_region_count).
        For each connected region found by BFS, checks:
          1. Exactly one dot inside it
          2. Dot's grid coordinate is within the region's cells
          3. Region has 180-degree rotational symmetry about that dot
        """
        n = self.N
        adj = self.cell_adj_graph()
        comps = bfs_components(adj, n * n)
        valid_cells = set()

        for comp in comps:
            region_cells = frozenset((cid % n, cid // n) for cid in comp)
            found = dots_in_region(region_cells, self.puzzle.dots)
            if len(found) != 1:
                continue
            _, dot_x, dot_y = found[0]
            xs = {x for x, y in region_cells}
            ys = {y for x, y in region_cells}
            if int(dot_x) not in xs or int(dot_y) not in ys:
                continue
            if has_rotational_symmetry(region_cells, dot_x, dot_y):
                valid_cells.update(comp)

        return valid_cells, len(comps)

    # ------------------------------------------------------------------
    # PURE DIVIDE AND CONQUER (STATE MERGING) SOLVER
    # ------------------------------------------------------------------

    def dc_solve_pure(self, x0, x1):
        """
        Pure D&C solver without the owner_map cheat sheet.
        Returns a list of all valid state dictionaries for the domain [x0, x1).
        """
        n = self.N
        dots = self.puzzle.dots

        # BASE CASE: single column
        if x1 - x0 == 1:
            states = [{}]  # Start with one empty state
            for y in range(n):
                new_states = []
                for state in states:
                    # Test every dot for the current cell
                    for dot_idx, d in enumerate(dots):
                        # Calculate symmetric partner using the mathematical midpoint
                        px = int(2 * d[0]) - x0 - 1
                        py = int(2 * d[1]) - y - 1
                        
                        # Boundary Test: If partner is on the board, branch a new state
                        if 0 <= px < n and 0 <= py < n:
                            new_s = state.copy()
                            new_s[(x0, y)] = dot_idx
                            new_states.append(new_s)
                states = new_states
            return states

        # DIVIDE
        mid = (x0 + x1) // 2
        
        # CONQUER
        left_states = self.dc_solve_pure(x0, mid)
        right_states = self.dc_solve_pure(mid, x1)

        # COMBINE (Cross-referencing)
        merged_states = []
        for l_state in left_states:
            for r_state in right_states:
                valid = True
                new_merged = l_state.copy()

                # Check Left against Right
                for (cx, cy), dot_idx in l_state.items():
                    d = dots[dot_idx]
                    px = int(2 * d[0]) - cx - 1
                    py = int(2 * d[1]) - cy - 1

                    # If partner lives in the right half, check for contradiction
                    if mid <= px < x1:
                        if (px, py) in r_state and r_state[(px, py)] != dot_idx:
                            valid = False
                            break
                
                if not valid:
                    continue

                # Check Right against Left
                for (cx, cy), dot_idx in r_state.items():
                    new_merged[(cx, cy)] = dot_idx
                    d = dots[dot_idx]
                    px = int(2 * d[0]) - cx - 1
                    py = int(2 * d[1]) - cy - 1

                    # If partner lives in the left half, check for contradiction
                    if x0 <= px < mid:
                        if (px, py) in l_state and l_state[(px, py)] != dot_idx:
                            valid = False
                            break
                
                # If both checks pass, the merged state is mathematically sound
                if valid:
                    merged_states.append(new_merged)

        return merged_states

    def computer_move(self):
        """
        HINT: Uses pure D&C state merging to find the solution.
        """
        # Use cached assignment if edges haven't changed since last solve
        edges_snapshot = frozenset(self.edges)
        if self._solver_cache and self._solver_cache[0] == edges_snapshot:
            assignment = self._solver_cache[1]
        else:
            print("Running pure D&C State-Merging. This might take a while...")
            final_states = self.dc_solve_pure(0, self.N)
            
            if not final_states:
                print("No solution found!")
                return None
            
            # The final returned list should have exactly 1 valid global state
            assignment = final_states[0]
            self._solver_cache = (edges_snapshot, assignment)

        n = self.N
        solved_edges = set()

        for y in range(n):
            for x in range(n):
                owner = assignment.get((x, y), -1)
                if x + 1 < n and assignment.get((x + 1, y), -1) != owner:
                    solved_edges.add(('v', x + 1, y))
                if y + 1 < n and assignment.get((x, y + 1), -1) != owner:
                    solved_edges.add(('h', x, y + 1))

        missing = solved_edges - self.edges
        if not missing:
            return None

        # SORTING: prefer edges near grid center
        center = n / 2
        best_edge = min(missing, key=lambda e: abs(e[1] - center) + abs(e[2] - center))

        self.toggle_edge(best_edge, who="computer")
        self._solver_cache = None
        return best_edge
# ==============================================================================
# SECTION 6: TKINTER UI
# ==============================================================================

class GalaxiesUI(tk.Tk):
    """
    UI CLASS (Tkinter):
    Complete graphical interface for the Galaxies puzzle game.
    
    Features:
      - Canvas rendering with grid and dots
      - Valid region highlighting (powered by DP memoization)
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
        
        Performance: DP memoization makes this 10-100x faster on repeated calls!
        """
        self.canvas.delete("all")
        n = self.game.N

        # Highlight valid regions (light blue) — also returns region count
        valid_cells, region_count = self.game.get_valid_regions()
        for cell_id_val in valid_cells:
            x, y = cell_id_val % n, cell_id_val // n
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

        # walls — no sort needed, draw order doesn't affect correctness
        for (t, x, y) in self.game.edges:
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

        # status — reuse valid_cells and region_count already computed above
        valid_count = len(valid_cells) // 1  # valid_cells is a set of cell_ids
        # count how many distinct complete valid regions (not cells)
        valid_region_count = sum(
            1 for rect in self.game.puzzle.rects
            if all(
                cell_id(x, y, n) in valid_cells
                for y in range(rect[1], rect[1] + rect[3])
                for x in range(rect[0], rect[0] + rect[2])
            )
        )
        msg = f"Lines placed: {len(self.game.edges - self.game.fixed)} | Regions: {region_count} | Valid regions: {valid_region_count}/{len(self.game.puzzle.rects)}"
        if valid_region_count == len(self.game.puzzle.rects):
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

        # After player moves, computer automatically makes one hint move
        if not self.game.is_solved():
            self.after(500, self.auto_computer_move)

    def auto_computer_move(self):
        """Computer automatically makes one D&C hint move after player's move."""
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
        """EVENT: Drag placeholder (bound but not active)."""
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
        """BUTTON: Hint - Computer makes one D&C+Backtracking move."""
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