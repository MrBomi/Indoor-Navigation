
import io
import ezdxf
from ezdxf.recover import read

import svgwrite

import math


from shapely.geometry import LineString, Point, MultiPolygon
from core.GraphBuilder import GraphBuilder
from core.Utils import Utils

from core.configLoader import Config
from core.GeometryExtractor import GeometryExtractor
import os
import json
import matplotlib.pyplot as plt
from shapely.geometry import Point
import core.Bitmap as bm
from core.ManagerFloor import ManagerFloor
import core.SvgManager as SvgManager
from scipy.spatial import KDTree

WIDTH, HEIGHT = 800, 800

class App:
    def __init__(self, config, dwg_file = None):
        self.name = config.get('app', 'name')
        self.version = config.get('app', 'version')
        self.dxf_file = config.get('file','input_name')
        self.output_file = config.get('file','output_name')
        self.svg_output_file = config.get('file','svg_output_name')
        self.json_output_file = config.get('file','json_output_name')
        self.wall_layer = config.get('layers', 'wall_layer', 'name')
        self.door_layer = config.get('layers', 'door_layer', 'name')
        self.roof_layer = config.get('layers', 'roof_layer', 'name')
        self.node_size = config.get('graph','node_size')
        self.scale = config.get('graph','scale')
        self.offset_cm = config.get('graph','offset_cm')
        # if dwg_file is None:
        #     dwg_path = config.get('file','input_name')
        dwg_file.seek(0)
        raw = dwg_file.read()
        stream = io.BytesIO(raw)
        self.doc, auditor = read(stream)
        if auditor.has_errors:
            print("Errors found in the DXF file:")
            for error in auditor.errors:
                print("-", error)
        self.extractor = None
        self.roof_area = None
        self.all_lines = None
        self.door_coords = None
        self.door_points = None
        self.svg_file = None
        self.grid_svg = None
        self.utils = None
        self.unit_scale = None
        self.spacing = None
        self.wall_lines = None
        self.height = None
        self.width = None


    
    def startProccesCreateNewBuilding(self):
        self.extractor = GeometryExtractor(self.doc, self.offset_cm, self.scale)
        self.wall_lines = self.extractor.load_layer_lines(self.wall_layer)
        roof_lines = self.extractor.load_layer_lines(self.roof_layer)
        self.roof_area = self.extractor.create_combined_polygon_from_lines(self.extractor.load_layer_lines(self.roof_layer))
        self.all_lines = self.wall_lines + roof_lines

        self.door_coords = self.extractor.door_positions(self.door_layer)
        self.door_points = [Point(round(x, 5), round(y, 5)) for x, y in self.door_coords]
        min_x , max_x , min_y, max_y = self.extractor.extract_bounding_box(self.all_lines,self.door_points)
        self.utils = Utils(min_x, max_x, min_y, max_y)
        all_lines_to_svg = [[self.utils.scale(x, y) for x, y in line.coords] for line in self.all_lines]
        door_points_to_svg = [self.utils.scale(pt.x, pt.y) for pt in self.door_points]
        self.svg_file = SvgManager.createSvgDrawing(self.utils.width, self.utils.height, all_lines_to_svg, door_points_to_svg)
        self.svg_grid = SvgManager.createSvgDrawing(self.utils.width, self.utils.height, all_lines_to_svg, door_points_to_svg)
        return self.svg_file
    
    def continueAddBuilding(self, point1, point2, distance_cm):
        self.calculateScale(point1, point2, distance_cm)
        return self.createFloor()

    def calculateScale(self, point1, point2, distance_cm):
        point1_unscaled = self.utils.unscale(point1[0], point1[1])
        point2_unscaled = self.utils.unscale(point2[0], point2[1])
        distance_raw = math.sqrt((point2_unscaled[0] - point1_unscaled[0]) ** 2 + (point2_unscaled[1] - point1_unscaled[1]) ** 2)
        self.unit_scale = 1 #distance_cm / distance_raw
        self.spacing = 50 / self.unit_scale #math.floor(35 / self.unit_sce)al
        print(f"scale: {self.unit_scale} spacing: {self.spacing}")
    
    def createFloor(self):
        grid = self.extractor.generate_quantized_grid(self.roof_area, self.spacing)
        graph = bm.build_graph_with_bitmap(grid,self.door_points,self.wall_lines,self.spacing)
        norm_positions = [self.utils.scale(x, y) for x, y in self.door_coords]
        roof_area = self.extractor.create_combined_polygon_from_lines(self.extractor.load_layer_lines(self.roof_layer))
        builder = GraphBuilder(self.output_file, self.node_size, self.offset_cm, self.scale, roof_area)
        builder.add_seed_nodes(norm_positions,"#FFCC00")
        builder.export()
        print(f"✅ graph written")
        doors_json = []
        for i, pt in enumerate(self.door_points):
            x, y = self.utils.scale(pt.x, pt.y)
            doors_json.append({"id": i, "x": x, "y": y})

        #coarse_to_fine = self.createGreedToSvg(graph)
        one_m_space = math.floor(100 / self.unit_scale)
        #grid_svg, cell_id_to_coords = SvgManager.addGridToSvg(self.all_lines, coarse_to_fine, self.utils, one_m_space)
        #grid_svg, cell_id_to_coords = SvgManager.draw_grid(self.svg_grid, graph, self.utils, self.spacing)
        grid_svg, cell_id_to_coords = SvgManager.draw_grid_flutter(self.svg_grid, graph, self.utils, self.spacing)
        node_to_cell, cell_to_nodes = memberships_from_drawing(
        graph,
        cell_id_to_coords,
        spacing_units=50,   # 0.5 m in model units
        eps_ratio=1e-9      # tiny tolerance for boundary sharing
        )
        adj = build_bigcell_adjacency(
        cell_id_to_coords,
        spacing_units=50,     # your 0.5 m in model units
        eps_ratio=1e-9,       # tiny tolerance for FP
        include_diagonals=True  # 8-neighborhood; set False for 4-neighborhood
    )

        # Example: print neighbors for cell 88 (if it exists)
        
        for cid in [88, 79, 107, 330, 480, 1323]:
            if cid in adj:
                print(cid, "->", sorted(adj[cid]))

        one_cm_svg = (1 / self.unit_scale) * self.utils.get_unit_size() 
        print(f"one cm in svg units: {one_cm_svg}")
        building = ManagerFloor(graph, self.door_points, self.svg_file, grid_svg, self.utils, cell_id_to_coords, cell_to_nodes, node_to_cell, adj, one_cm_svg)
        return building
        
    # def createGreedToSvg(self, graph):
    #     threshold = self.spacing * math.sqrt(2) * 1.1
    #     # Get graph nodes as Point objects
    #     graph_points = list(graph.keys())
    #     if not graph_points:
    #         return {}

    #     xs = [p[0] for p in graph_points]
    #     ys = [p[1] for p in graph_points]

    #     min_x, max_x = min(xs), max(xs)
    #     min_y, max_y = min(ys), max(ys)

    #     # Build KDTree for efficient search
    #     tree = KDTree(graph_points)

    #     coarse_to_fine = {}

    #     # Step 1: Build coarse grid (2*spacing)
    #     coarse_spacing = math.floor(100 / self.unit_scale)
    #     x = round(min_x / coarse_spacing) * coarse_spacing
    #     count_over = 0
    #     count_less = 0
    #     while x <= max_x:
    #         y = round(min_y / coarse_spacing) * coarse_spacing
    #         while y <= max_y:
    #             center = (round(x, 6), round(y, 6))
    #             indices = tree.query_ball_point(center, threshold)
    #             if indices:
    #                 nearby = [graph_points[i] for i in indices]
    #                 if len(nearby) < 1 or len(nearby) > 25:
    #                     if len(nearby) > 25:
    #                         count_over += 1
    #                     else:
    #                         count_less += 1
    #                 coarse_to_fine[center] = nearby
    #             y += coarse_spacing
    #         x += coarse_spacing
    #     print(f"Coarse grid created with {len(coarse_to_fine)} points, {count_over} over 25 points, {count_less} less than 1 point")
    
    #     # 1. Gather all fine-level points from the original graph
    #     fine_points = list(graph.keys())

    #     # 2. Collect every fine point that appears in any coarse_to_fine entry
    #     mapped_points = {p for fine_list in coarse_to_fine.values() for p in fine_list}

    #     # 3. Find which fine points weren’t mapped to any coarse cell
    #     unmapped = set(fine_points) - mapped_points

    #     # 4. Report the results
    #     if unmapped:
    #         print(f"[WARNING] {len(unmapped)} fine points are not assigned to any coarse cell:")
    #     else:
    #         print("All fine points are assigned to at least one coarse cell.")

    #     return coarse_to_fine

    def createGreedToSvg(self, graph):
        fine_points = list(graph.keys())
        if not fine_points:
            return {}

        # Extract min and max coordinates from fine points
        xs = [p[0] for p in fine_points]
        ys = [p[1] for p in fine_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Calculate coarse spacing based on unit scale
        meter_size = 1.0
        coarse_spacing_raw = meter_size * 100

        # coarse_spacing ב־raw יחידות מחולק ל־unit_scale
        coarse_spacing = max(
            1,
            math.floor(coarse_spacing_raw / self.unit_scale)
        )

        
        nx = math.ceil((max_x - min_x) / coarse_spacing)
        ny = math.ceil((max_y - min_y) / coarse_spacing)

        coarse_to_fine = {}
        
        for ix in range(nx):
            for iy in range(ny):
                cx = min_x + (ix + 0.5) * coarse_spacing
                cy = min_y + (iy + 0.5) * coarse_spacing
                center = (round(cx, 6), round(cy, 6))
                coarse_to_fine[center] = []

        # Assign fine points to coarse cells
        for fp in fine_points:
            ix = int((fp[0] - min_x) // coarse_spacing)
            iy = int((fp[1] - min_y) // coarse_spacing)
            ix = min(max(ix, 0), nx - 1)
            iy = min(max(iy, 0), ny - 1)
            cx = min_x + (ix + 0.5) * coarse_spacing
            cy = min_y + (iy + 0.5) * coarse_spacing
            center = (round(cx, 6), round(cy, 6))
            coarse_to_fine[center].append(fp)

        coarse_to_fine = {
            center: fines
            for center, fines in coarse_to_fine.items()
            if len(fines) > 1
        }

        max_fines = max(len(fines) for fines in coarse_to_fine.values())

        for i in range(1, max_fines + 1):
            count_i = sum(1 for fines in coarse_to_fine.values() if len(fines) == i)
            print(f"{i}: {count_i} coarse cells have exactly {i} fine points")

        return coarse_to_fine


# =========================
# Big-cell membership (drawing-based)
# =========================
import math
from collections import defaultdict
from typing import Dict, Tuple, Set, Iterable

Coord = Tuple[float, float]
CellID = int
Bounds = Tuple[float, float, float, float]  # (minx, miny, maxx, maxy)

def build_cell_bounds_from_centers(
    cell_id_to_coords: Dict[CellID, Coord],
    spacing_units: float = 50.0,  # 0.5 m in model units -> 1.0 m = 2*spacing_units
) -> Dict[CellID, Bounds]:
    """
    Reconstruct per-cell bounds from the DRAWN cell centers (model units).
    This makes NO assumptions about origin or index layout.
      BIG = 2 * spacing_units (1 m in your model units).
      For center (cx, cy): bounds = [cx - BIG/2, cx + BIG/2] x [cy - BIG/2, cy + BIG/2].
    """
    BIG = 2.0 * spacing_units
    half = BIG / 2.0
    bounds: Dict[CellID, Bounds] = {}
    for cid, (cx, cy) in cell_id_to_coords.items():
        minx = cx - half
        maxx = cx + half
        miny = cy - half
        maxy = cy + half
        bounds[cid] = (minx, miny, maxx, maxy)
    return bounds

def _point_hits_bounds_with_boundary(b: Bounds, x: float, y: float, eps: float) -> bool:
    """
    Inclusive rectangle hit test with small tolerance:
    - Interior counts as inside.
    - Points on edges/vertices count as inside (with eps tolerance).
    """
    minx, miny, maxx, maxy = b
    # early reject with expanded bounds (eps) to avoid tiny FP misses
    if x < (minx - eps) or x > (maxx + eps) or y < (miny - eps) or y > (maxy + eps):
        return False

    # treat edges as inclusive with a small tolerance
    inside_x = (minx + eps) < x < (maxx - eps)
    inside_y = (miny + eps) < y < (maxy - eps)
    if inside_x and inside_y:
        return True

    # On edge or vertex: still counts
    return (minx - eps) <= x <= (maxx + eps) and (miny - eps) <= y <= (maxy + eps)

def memberships_from_drawing(
    graph: Dict[Coord, Iterable[Coord]],   # unweighted graph: (x,y) -> list[(x,y)]
    cell_id_to_coords: Dict[CellID, Coord],# returned by your existing draw function
    spacing_units: float = 50.0,           # 0.5 m in model units -> 1.0 m cell size = 2*spacing_units
    eps_ratio: float = 1e-9,               # boundary tolerance as a fraction of 1 m cell size
) -> Tuple[Dict[Coord, Set[CellID]], Dict[CellID, Set[Coord]]]:
    """
    Assign each original graph node to the DRAWN big cells, using boundary-sharing rules:
      - interior -> belongs to exactly 1 drawn cell
      - on an edge -> belongs to both adjacent drawn cells
      - on a vertex -> belongs to all touching drawn cells (2..4)
    NO assumptions about origin or index math. Everything is derived from the SVG output.

    Returns:
      node_to_cell_ids: (x,y) -> set of drawn cell IDs containing that point
      cell_id_to_nodes: cell_id -> set of (x,y) nodes contained in that drawn cell
    """
    BIG = 2.0 * spacing_units
    eps = max(1e-12, eps_ratio * BIG)

    # 1) Bounds from the actual drawing (centers)
    bounds_by_cid = build_cell_bounds_from_centers(cell_id_to_coords, spacing_units)

    # 2) Collect unique nodes from the graph (unweighted)
    nodes: Set[Coord] = set()
    for u, nbrs in graph.items():
        nodes.add(u)
        for v in nbrs:
            nodes.add(v)

    # 3) Test each node against the DRAWN rectangles (boundary-inclusive)
    node_to_cell_ids: Dict[Coord, Set[CellID]] = {}
    cell_id_to_nodes: Dict[CellID, Set[Coord]] = defaultdict(set)

    # NOTE: O(|V| * |C|). If |C| is large, add a spatial index (grid buckets / R-tree) later.
    for (x, y) in nodes:
        hits: Set[CellID] = set()
        for cid, b in bounds_by_cid.items():
            if _point_hits_bounds_with_boundary(b, x, y, eps):
                hits.add(cid)
        node_to_cell_ids[(x, y)] = hits
        for cid in hits:
            cell_id_to_nodes[cid].add((x, y))

    return node_to_cell_ids, cell_id_to_nodes


def build_cell_bounds_from_centers(
    cell_id_to_coords: Dict[CellID, Coord],
    spacing_units: float = 50.0,  # 0.5 m model units -> 1.0 m = 2*spacing_units
) -> Dict[CellID, Bounds]:
    """Reconstruct each drawn 1 m cell's rectangle bounds from its center (model units)."""
    BIG  = 2.0 * spacing_units
    half = BIG / 2.0
    out: Dict[CellID, Bounds] = {}
    for cid, (cx, cy) in cell_id_to_coords.items():
        out[cid] = (cx - half, cy - half, cx + half, cy + half)
    return out

def _intervals_overlap_inclusive(a1: float, a2: float, b1: float, b2: float, eps: float) -> bool:
    """True if [a1,a2] and [b1,b2] overlap or just touch, within eps."""
    left  = max(a1, b1)
    right = min(a2, b2)
    return right >= left - eps  # allow touching

def _are_edge_neighbors(b1: Bounds, b2: Bounds, eps: float) -> bool:
    """Share a full edge (left/right or top/bottom) with nonzero overlap along the other axis."""
    minx1, miny1, maxx1, maxy1 = b1
    minx2, miny2, maxx2, maxy2 = b2
    # left/right adjacency
    if abs(maxx1 - minx2) <= eps or abs(maxx2 - minx1) <= eps:
        return _intervals_overlap_inclusive(miny1, maxy1, miny2, maxy2, eps)
    # top/bottom adjacency
    if abs(maxy1 - miny2) <= eps or abs(maxy2 - miny1) <= eps:
        return _intervals_overlap_inclusive(minx1, maxx1, minx2, maxx2, eps)
    return False

def _are_corner_neighbors(b1: Bounds, b2: Bounds, eps: float) -> bool:
    """Touch at exactly one corner (no edge overlap)."""
    minx1, miny1, maxx1, maxy1 = b1
    minx2, miny2, maxx2, maxy2 = b2

    x_touch = abs(maxx1 - minx2) <= eps or abs(maxx2 - minx1) <= eps
    y_touch = abs(maxy1 - miny2) <= eps or abs(maxy2 - miny1) <= eps
    if not (x_touch and y_touch):
        return False

    # ensure it's a corner (overlap along each axis is ~0)
    x_overlap = min(maxx1, maxx2) - max(minx1, minx2)
    y_overlap = min(maxy1, maxy2) - max(miny1, miny2)
    return x_overlap <= eps and y_overlap <= eps

def build_bigcell_adjacency(
    cell_id_to_coords: Dict[CellID, Coord],
    spacing_units: float = 50.0,
    eps_ratio: float = 1e-9,
    include_diagonals: bool = True,
) -> Dict[CellID, Set[CellID]]:
    """
    Build adjacency between actually drawn 1 m cells.
    - Two cells are neighbors if their rectangles touch (share edge), and if
      include_diagonals=True, also if they touch at a corner.
    - Real gaps mean 'not neighbors' (even if they look near).

    Returns: dict[cell_id] -> set(neighbor_cell_ids)
    """
    BIG = 2.0 * spacing_units
    eps = max(1e-12, eps_ratio * BIG)

    bounds_by_cid = build_cell_bounds_from_centers(cell_id_to_coords, spacing_units)
    cids = list(bounds_by_cid.keys())

    neighbors: Dict[CellID, Set[CellID]] = {cid: {cid} for cid in cids}

    # O(|C|^2). For very large C, add a spatial index / grid bucketing later.
    for i, ca in enumerate(cids):
        ba = bounds_by_cid[ca]
        for cb in cids[i+1:]:
            bb = bounds_by_cid[cb]
            edge_adj   = _are_edge_neighbors(ba, bb, eps)
            corner_adj = include_diagonals and _are_corner_neighbors(ba, bb, eps)
            if edge_adj or corner_adj:
                neighbors[ca].add(cb)
                neighbors[cb].add(ca)

    return neighbors
