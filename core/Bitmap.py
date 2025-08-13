
import math
import numpy as np
from shapely.geometry import Point, LineString
from collections import defaultdict
from shapely.ops import unary_union
import matplotlib.pyplot as plt

def create_bitmap_from_walls(wall_lines, spacing, wall_thickness):

    wall_polygons = [w.buffer(wall_thickness, resolution=1) for w in wall_lines if w.is_valid]
    combined = unary_union(wall_polygons)

    minx, miny, maxx, maxy = combined.bounds
    cols = int((maxx - minx) // spacing) + 1
    rows = int((maxy - miny) // spacing) + 1

    bitmap = np.zeros((rows, cols), dtype=np.uint8)

    for row in range(rows):
        for col in range(cols):
            x = minx + col * spacing + spacing / 2
            y = miny + row * spacing + spacing / 2
            pt = Point(x, y)
            if combined.contains(pt):
                bitmap[row, col] = 1

    return bitmap, minx, miny, rows, cols

def is_blocked(x, y, bitmap, minx, miny, spacing):
    col = int((x - minx) // spacing)
    row = int((y - miny) // spacing)
    if 0 <= row < bitmap.shape[0] and 0 <= col < bitmap.shape[1]:
        return bitmap[row, col] == 1
    return True

# def build_graph_with_bitmap(grid_points, door_points, wall_lines, spacing, wall_thickness_ratio=0.5):
#     graph = defaultdict(list)
#     directions = [
#     ( spacing,  0), (-spacing,  0), (0,  spacing), (0, -spacing)]

#     # Step 1: Create bitmap
#     wall_thickness = spacing * wall_thickness_ratio
#     bitmap, minx, miny, rows, cols = create_bitmap_from_walls(wall_lines, spacing, wall_thickness)

#     # Step 2: Build graph from grid
#     for pt in grid_points:
#         x1, y1 = pt.x, pt.y
#         if is_blocked(x1, y1, bitmap, minx, miny, spacing):
#             continue
#         for dx, dy in directions:
#             x2, y2 = x1 + dx, y1 + dy
#             if not is_blocked(x2, y2, bitmap, minx, miny, spacing):
#                 graph[(x1, y1)].append((x2, y2))
#                 graph[(x2, y2)].append((x1, y1))

#     # Step 3: Connect doors to grid
#     for door in door_points:
#         door_key = (door.x, door.y)
#         graph[door_key] = []
#         for pt in grid_points:
#             x, y = pt.x, pt.y
#             if not is_blocked(x, y, bitmap, minx, miny, spacing) and Point(x, y).distance(door) <= spacing * 1.5:
#                 graph[door_key].append((x, y))
#                 graph[(x, y)].append(door_key)

#     #visualize_bitmap(bitmap)

#     return graph

def build_graph_with_bitmap(grid_points, door_points, wall_lines, spacing, wall_thickness_ratio=0.5, use_weights=False):
    """
    Build an 8-neighborhood grid graph (N, S, E, W + diagonals) over free cells.
    Diagonal steps are allowed but cannot 'cut corners' through walls.
    Optionally assigns weights: spacing for orthogonal steps, spacing*sqrt(2) for diagonals.
    """
    graph = defaultdict(list)

    # 8 directions: orthogonal + diagonals
    directions = [
        ( spacing,  0), (-spacing,  0), (0,  spacing), (0, -spacing),
        ( spacing,  spacing), ( spacing, -spacing), (-spacing,  spacing), (-spacing, -spacing)
    ]

    # Step 1: Create bitmap (occupied=1, free=0)
    wall_thickness = spacing * wall_thickness_ratio
    bitmap, minx, miny, rows, cols = create_bitmap_from_walls(wall_lines, spacing, wall_thickness)

    def can_move(x1, y1, x2, y2):
        """
        Allow diagonal only if both adjacent orthogonal cells are free.
        Prevents 'corner cutting' through a wall buffer.
        """
        if is_blocked(x2, y2, bitmap, minx, miny, spacing):
            return False
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) == spacing and abs(dy) == spacing:
            if is_blocked(x1 + dx, y1, bitmap, minx, miny, spacing):
                return False
            if is_blocked(x1, y1 + dy, bitmap, minx, miny, spacing):
                return False
        return True

    def add_edge(u, v, cost=None):
        """Append edge u->v if it doesn't already exist (handles weighted/unweighted)."""
        if use_weights:
            # avoid duplicates by checking neighbor coordinate
            if not any(nbr == v for (nbr, _) in graph[u]):
                graph[u].append((v, cost))
        else:
            if v not in graph[u]:
                graph[u].append(v)

    # Step 2: Pre-populate ALL free grid nodes so isolated nodes exist in the graph
    free_nodes = []
    for pt in grid_points:
        x, y = pt.x, pt.y
        if not is_blocked(x, y, bitmap, minx, miny, spacing):
            graph[(x, y)]  # ensure key exists with empty neighbor list
            free_nodes.append((x, y))

    # Step 3: Add edges between neighbors (no duplicates)
    for (x1, y1) in free_nodes:
        for dx, dy in directions:
            x2, y2 = x1 + dx, y1 + dy
            if can_move(x1, y1, x2, y2):
                if use_weights:
                    cost = spacing if (dx == 0 or dy == 0) else spacing * math.sqrt(2)
                    add_edge((x1, y1), (x2, y2), cost)
                    add_edge((x2, y2), (x1, y1), cost)
                else:
                    add_edge((x1, y1), (x2, y2))
                    add_edge((x2, y2), (x1, y1))

    # Step 4: Connect doors to nearby free grid nodes
    for door in door_points:
        door_key = (door.x, door.y)
        graph[door_key]  # ensure door exists even if it doesn't connect to anything
        for (x, y) in free_nodes:
            if Point(x, y).distance(door) <= spacing * 1.5:
                if use_weights:
                    cost = Point(x, y).distance(door)
                    add_edge(door_key, (x, y), cost)
                    add_edge((x, y), door_key, cost)
                else:
                    add_edge(door_key, (x, y))
                    add_edge((x, y), door_key)

    return graph
def visualize_bitmap(bitmap, title="Bitmap Visualization"):
    plt.figure(figsize=(10, 10))
    plt.imshow(bitmap, cmap='gray_r', origin='upper')
    plt.title(title)
    plt.xlabel("Columns")
    plt.ylabel("Rows")
    plt.grid(False)
    plt.show()
	