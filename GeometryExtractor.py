# geometry_extractor.py
import math
import heapq
import ezdxf
from shapely.ops import polygonize, unary_union
from shapely.geometry.base import BaseGeometry
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, MultiPolygon
from shapely.strtree import STRtree
from collections import defaultdict
from shapely.prepared import prep
from rtree import index



class GeometryExtractor:
    def __init__(self, dxf_file, offset_cm, scale):
        self.doc = dxf_file
        self.modelspace = self.doc.modelspace()
        self.allNodes = []
        self.offset_cm = offset_cm
        self.scale = scale


    def load_layer_lines(self, layer_name):
        lines = []

        for e in self.modelspace.query("LINE"):
            if e.dxf.layer in layer_name:
                start = (e.dxf.start.x, e.dxf.start.y)
                end = (e.dxf.end.x,e.dxf.end.y)
                lines.append(LineString([start, end]))

        for e in self.modelspace.query("LWPOLYLINE"):
            if e.dxf.layer in layer_name:
                points = [(pt[0], pt[1]) for pt in e.get_points()]
                if not e.closed:
                    lines.append(LineString(points))
                else:
                    points.append(points[0])  # close the shape
                    lines.append(LineString(points))

        return lines

    def door_positions(self, layer_name):
        doors = []
        geometry_types = set()

        for entity in self.modelspace.query(f'*[layer=="{layer_name}"]'):
            geometry_types.add(entity.dxftype())


        handler_map = {
            "LWPOLYLINE": self._get_lwpolyline_center,
            "LINE": self._get_line_center,
            "CIRCLE": self._get_circle_center,
            "ARC": self._get_arc_center,
            "POLYLINE": self._get_polyline_center,
            "INSERT": self._get_insert_point,
            # Add more types and handlers here if needed
        }

        for entity in self.modelspace.query(f'*[layer=="{layer_name}"]'):
            dtype = entity.dxftype()
            handler = handler_map.get(dtype)
            if handler:
                result = handler(entity)
                if result:
                    doors.append(result)
                    self.allNodes.append(result)

        if not doors:
            raise ValueError(f"No door positions found on layer: {layer_name}")
        return doors

    def create_combined_polygon_from_lines(self, lines):
        merged = unary_union(lines)
        polygons = list(polygonize(merged))
        if not polygons:
            raise ValueError("Failed to find any polygons in the merged lines")
        return MultiPolygon(polygons)

    def is_point_inside_geometry(self, geometry, point: Point):
        return geometry.contains(point)

    def extract_bounding_box(self, layer_name):
        x_min, y_min = float('inf'), float('inf')
        x_max, y_max = float('-inf'), float('-inf')

        # Include LWPOLYLINE walls
        for polyline in self.modelspace.query("LWPOLYLINE"):
            if polyline.dxf.layer == layer_name:
                for point in polyline.get_points():
                    x, y = point[0], point[1]
                    x_min = min(x_min, x)
                    x_max = max(x_max, x)
                    y_min = min(y_min, y)
                    y_max = max(y_max, y)

        # Include LINE walls
        for line in self.modelspace.query("LINE"):
            if line.dxf.layer == layer_name:
                start = line.dxf.start
                end = line.dxf.end
                for x, y in [(start.x, start.y), (end.x, end.y)]:
                    x_min = min(x_min, x)
                    x_max = max(x_max, x)
                    y_min = min(y_min, y)
                    y_max = max(y_max, y)

        return x_min, x_max, y_min, y_max

    def print_all_line_layers(self):
        """Prints all layers that contain LINE or LWPOLYLINE entities."""
        line_layers = set()

        for e in self.modelspace:
            if e.dxftype() in {"LINE", "LWPOLYLINE"}:
                line_layers.add(e.dxf.layer)

        print("📋 Layers containing LINE or LWPOLYLINE entities:")
        for layer in sorted(line_layers):
            print(f"  - {layer}")

    def plot_geometry_and_point(self, geometry, point=None, title=""):
        fig, ax = plt.subplots()

        if geometry.geom_type == "MultiPolygon":
            for poly in geometry.geoms:
                x, y = poly.exterior.xy
                ax.plot(x, y, color='green')
        elif geometry.geom_type == "Polygon":
            x, y = geometry.exterior.xy
            ax.plot(x, y, color='green')

        if point:
            ax.plot(point.x, point.y, 'ro')
        ax.set_aspect('equal')
        plt.title(title)
        plt.grid(True)
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show()

    def _is_far_enough(self, x, y):
        offset_px = self.offset_cm * self.scale
        return all(math.hypot(x - px, y - py) >= offset_px for (px, py) in self.allNodes)

    # --- Handlers for entity types ---

    def _get_lwpolyline_center(self, entity):
        points = list(entity.get_points())
        if not points:
            return None
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return (x, y)

    def _get_line_center(self, entity):
        start = entity.dxf.start
        end = entity.dxf.end
        x = (start[0] + end[0]) / 2
        y = (start[1] + end[1]) / 2
        return (x, y)

    def _get_circle_center(self, entity):
        center = entity.dxf.center
        return (center[0], center[1])

    def _get_arc_center(self, entity):
        center = entity.dxf.center
        return (center[0], center[1])

    def _get_polyline_center(self, entity):
        points = [v.dxf.location for v in entity.vertices]
        if not points:
            return None
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return (x, y)

    def _get_insert_point(self, entity):
        insert = entity.dxf.insert
        return (insert[0], insert[1])


    def generate_quantized_grid(self,geometry, spacing):
        minx, miny, maxx, maxy = geometry.bounds
        result = []
        x = round(minx // spacing) * spacing
        while x <= maxx:
            y = round(miny // spacing) * spacing
            while y <= maxy:
                pt = Point(x, y)
                if geometry.contains(pt):
                    result.append(pt)
                y += spacing
            x += spacing
        return result

    def build_grid_graph_fast(self, grid_points, wall_lines,door_points, spacing):
        graph = defaultdict(list)
        points_set = set((p.x, p.y) for p in grid_points)

        # ודא שכולם חוקיים
        wall_lines = [w for w in wall_lines if isinstance(w, LineString) and w.is_valid]

        # הכנה של הקירות מראש עם bounding boxes ו־prepared geometry
        wall_data = []
        for wall in wall_lines:
            bounds = wall.bounds  # (minx, miny, maxx, maxy)
            prepared = prep(wall)
            wall_data.append((bounds, prepared))

        directions = [
            (spacing, 0), (-spacing, 0),
            (0, spacing), (0, -spacing)
        ]

        for pt in grid_points:
            for dx, dy in directions:
                neighbor = (pt.x + dx, pt.y + dy)
                if neighbor in points_set:
                    line = LineString([(pt.x, pt.y), neighbor])
                    if not line.is_valid or line.is_empty:
                        continue

                    lxmin, lymin, lxmax, lymax = line.bounds
                    blocked = False

                    for (wxmin, wymin, wxmax, wymax), wall in wall_data:
                        # סינון לפי bbox
                        if (
                                lxmax < wxmin or lxmin > wxmax or
                                lymax < wymin or lymin > wymax
                        ):
                            continue  # אין סיכוי לחפיפה

                        if wall.crosses(line):  # רק אם יש סיכוי
                            blocked = True
                            break

                    if not blocked:
                        graph[(pt.x, pt.y)].append(neighbor)

        for door in door_points:
            graph[(door.x, door.y)] = []

            # חבר את הדלת לנקודות גריד קרובות (בטווח סביר)
            for pt in grid_points:
                if Point(pt).distance(door) <= spacing * 1.5:  # טווח חיבור
                    line = LineString([pt, (door.x, door.y)])
                    if all(not line.crosses(w) for w in wall_lines):
                        graph[(door.x, door.y)].append(pt)
                        graph[pt].append((door.x,door.y))
        return graph



    # def build_graph_with_doors(self,grid_points, door_points, wall_lines, spacing):
    #     graph = defaultdict(list)
    #     epsilon = 10
    #     points_set = set((p.x, p.y) for p in grid_points)
    #
    #     # סינון קירות חוקיים
    #     wall_lines = [wall.buffer(12.5) for wall in wall_lines]
    #     combined_wall = unary_union(wall_lines)
    #     wall_lines = [w for w in wall_lines if isinstance(w, LineString) and w.is_valid]
    #
    #     # בניית אינדקס מרחבי לקירות
    #     rtree_idx = index.Index()
    #     wall_geoms = []
    #
    #     for i, wall in enumerate(wall_lines):
    #         wall_geoms.append(wall)
    #         rtree_idx.insert(i, wall.bounds)
    #
    #     directions = [(spacing, 0), (-spacing, 0), (0, spacing), (0, -spacing)]
    #
    #     # שלב 1: יצירת גרף מנקודות הגריד
    #     for pt in grid_points:
    #         for dx, dy in directions:
    #             neighbor = (pt.x + dx, pt.y + dy)
    #             if neighbor in points_set:
    #                 line = LineString([(pt.x, pt.y), neighbor])
    #                 if not line.is_valid or line.is_empty:
    #                     continue
    #
    #                 possible_hits = list(rtree_idx.intersection(line.bounds))
    #
    #                 if not any(line.buffer(epsilon).intersects(wall_geoms[i]) for i in possible_hits):
    #                     graph[(pt.x, pt.y)].append(neighbor)
    #
    #     # שלב 2: הוספת נקודות דלתות וחיבורן לנקודות קרובות
    #     for door in door_points:
    #         door_key = (door.x, door.y)
    #         graph[door_key] = []
    #
    #         for pt in grid_points:
    #             grid_key = (pt.x, pt.y)
    #             if Point(pt).distance(door) <= spacing * 1.5:
    #                 line = LineString([pt, door])
    #                 if not line.is_valid or line.is_empty:
    #                     continue
    #
    #                 possible_hits = list(rtree_idx.intersection(line.bounds))
    #                 if not any(line.buffer(epsilon).intersects(wall_geoms[i]) for i in possible_hits):
    #                     graph[door_key].append(grid_key)
    #                     graph[grid_key].append(door_key)
    #
    #     return graph

    def build_graph_with_doors(self,grid_points, door_points, wall_lines, spacing, path_width=40, wall_thickness_ratio=0.5):
        graph = defaultdict(list)
        points_set = set((p.x, p.y) for p in grid_points)

        # סינון קירות תקינים
        wall_lines = [w for w in wall_lines if isinstance(w, LineString) and w.is_valid]

        # הפיכת קירות לפוליגונים עם עובי
        wall_thickness = spacing * wall_thickness_ratio
        wall_polygons = [wall.buffer(wall_thickness,resolution=1) for wall in wall_lines]
        combined_walls = unary_union(wall_polygons)

        directions = [(spacing, 0), (-spacing, 0), (0, spacing), (0, -spacing)]

        # שלב 1: יצירת גרף מהגריד
        for pt in grid_points:
            for dx, dy in directions:
                neighbor = (pt.x + dx, pt.y + dy)
                if neighbor in points_set:
                    line = LineString([(pt.x, pt.y), neighbor])
                    path_shape = line.buffer(path_width / 2)
                    if not path_shape.intersects(combined_walls):
                        graph[(pt.x, pt.y)].append(neighbor)

        # שלב 2: חיבור דלתות לגריד
        for door in door_points:
            door_key = (door.x, door.y)
            graph[door_key] = []

            for pt in grid_points:
                grid_key = (pt.x, pt.y)
                if Point(pt).distance(door) <= spacing * 1.5:
                    line = LineString([pt, door])
                    path_shape = line.buffer(path_width / 2)
                    if not path_shape.intersects(combined_walls):
                        graph[door_key].append(grid_key)
                        graph[grid_key].append(door_key)

        return graph

    def astar(self, graph, start, goal):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0

        def heuristic(a, b):
            return math.hypot(a[0] - b[0], a[1] - b[1])

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for neighbor in graph[current]:
                tentative_g = g_score[current] + heuristic(current, neighbor)
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))
        return None

    def lobby_nodes(self, roof_area,roof_layer_name):
        lobby = []
        x_min, x_max, y_min, y_max = self.extract_bounding_box(roof_layer_name)
        for bx in range(math.floor(x_min), math.ceil(x_max)):
            for by in range(math.floor(y_min), math.ceil(y_max)):
                if self._is_far_enough(bx, by) and self.is_point_inside_geometry(roof_area,Point(bx,by)):
                    lobby.append((bx,by))
                    self.allNodes.append((bx,by))
        if not lobby:
            print(f"No lobby positions found on layer")
        return lobby

    def compute_visibility_map(self, grid_points, door_points, wall_lines, max_distance=500):
        from shapely.geometry.base import BaseGeometry
        from shapely.strtree import STRtree
        from collections import defaultdict

        wall_lines = [w for w in wall_lines if isinstance(w, LineString)]
        wall_tree = STRtree(wall_lines)
        visibility = defaultdict(set)

        for i, pt in enumerate(grid_points):
            for j, door in enumerate(door_points):
                if pt.distance(door) > max_distance:
                    continue

                line = LineString([pt, door])
                obstacles = wall_tree.query(line)

                if all(w is not None and isinstance(w, BaseGeometry) and not line.crosses(w) and not line.within(w) for
                       w in obstacles):
                    visibility[(pt.x, pt.y)].add(j)

        return visibility

    def greedy_cover(self,visibility_map, total_doors):
        uncovered = set(range(total_doors))
        selected = []

        while uncovered:
            best_pt = None
            best_cover = set()

            for pt, covers in visibility_map.items():
                new_covers = covers & uncovered
                if len(new_covers) > len(best_cover):
                    best_pt = pt
                    best_cover = new_covers

            if not best_pt:
                break
            selected.append(best_pt)
            uncovered -= best_cover

        return selected

    def invert_visibility_map(self, visibility_map, total_doors):
        door_visibility_map = defaultdict(list)

        for grid_pt, doors in visibility_map.items():
            for door_id in doors:
                door_visibility_map[door_id].append(grid_pt)

        for door_id in range(total_doors):
            points = door_visibility_map.get(door_id, [])
            print(f"Door {door_id} sees {len(points)} grid points:")
            for pt in points:
                print(f"  ↳ Grid Point: {pt}")
            if not points:
                print("  ⚠ Door does not see any point!")

        return door_visibility_map

    def find_covering_nodes(self, wall_lines, roof_lines, door_coords, spacing):
        roof_area = self.create_combined_polygon_from_lines(roof_lines)
        door_points = [Point(x, y) for x, y in door_coords]

        grid_points = self.generate_quantized_grid(roof_area, spacing)
        visibility_map = self.compute_visibility_map(grid_points, door_points, wall_lines)
        door_visibility_map = self.invert_visibility_map(visibility_map, len(door_coords))
        selected_nodes = self.greedy_cover(visibility_map, total_doors=len(door_points))

        return selected_nodes