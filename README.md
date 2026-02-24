# Galaxies Puzzle: Divide & Conquer State-Merging Solver

A complete Python and Tkinter implementation of the classic "Galaxies" logic puzzle (popularized by Simon Tatham's Portable Puzzle Collection). This project features a fully interactive graphical interface and a mathematically rigorous, custom-built solver utilizing a pure **Divide and Conquer** state-merging architecture.

## Project Overview

The objective of Galaxies is to draw edges along the grid lines to divide the board into enclosed regions.
Every valid region must follow strict constraints:

1. It must contain exactly **one dot**.
2. The dot must be the exact geometric center of the region.
3. The region must possess **two-way (180-degree) rotational symmetry** around its dot.

## Technical Highlights & Algorithm Analysis

This implementation was built with a strict adherence to fundamental algorithm design principles, avoiding high-level Python built-in functions (like `len()`, `sum()`, `max()`, `min()`, `sorted()`) in favor of custom, low-level implementations.

### 1. Pure Divide & Conquer (State-Merging) Solver

The core of the hint system is a "cheat-free" solver that deduces the solution strictly through mathematical constraints and state-space merging.

* **Divide:** The $N \times N$ grid is recursively bisected vertically until it reaches single base-case columns.
* **Conquer (Base Case):** For a single column, the algorithm generates all mathematically viable state branches using coordinate geometry and midpoint rotation formulas to prune impossible dot assignments.
* **Combine:** Left and Right state spaces are cross-referenced. Symmetric partner cells are interrogated to eliminate contradictions. Only globally valid state dictionaries survive the merge and bubble up the recursion tree.
* **Complexity:** Showcases the classic DAA trade-off. It heavily reduces Time Complexity by pruning bad branches early, but requires significant Space Complexity to hold intermediate state dictionaries during the merge steps.

### 2. Graph Traversal (BFS)

* **Application:** Used dynamically to detect enclosed regions and walls.
* **Implementation:** An undirected, unweighted adjacency list is generated from the current board state. A custom Breadth-First Search (BFS) traverses the graph to map out connected components and validate isolation constraints.
* **Complexity:** $O(V + E)$ Time and Space.

### 3. Computation Tracking

* The solver includes an internal diagnostic counter that tracks the exact number of state generations and cross-reference checks performed during a run, allowing for empirical analysis of the combinatorial explosion.

## Features

* **Interactive Canvas:** Click grid lines to draw/erase walls.
* **Visual Feedback:** Valid regions (symmetrical with exactly one dot) are automatically highlighted in blue.
* **Arrow Markers:** Right-click dots to place directional arrows to map out complex galaxy shapes visually.
* **Hint System:** Watch the pure D&C algorithm calculate and place the next strictly logical edge.
* **Undo/Redo Stack:** Full history traversal.
* **Dynamic Sizing:** Supports $4 \times 4$ up to $15 \times 15$ grids (Note: Pure D&C solver is computationally heavy on grids larger than $4 \times 4$).

## Installation & Usage

### Prerequisites

* Python 3.x
* Tkinter (usually bundled with standard Python installations)

### Running the Game

1. Clone this repository to your local machine.
2. Navigate to the project directory.
3. Run the script:

```bash
python galaxies.py

```

### Controls

* **Left Click (Edge):** Place or remove a wall.
* **Right Click (Cell -> Dot):** Draw a marker arrow from the cell to the nearest dot.
* **Right Drag (Off-Grid):** Remove an existing marker arrow.

---
