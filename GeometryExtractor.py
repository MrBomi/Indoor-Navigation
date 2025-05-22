# geometry_extractor.py
from shapely.geometry import LineString, MultiPolygon, Point
from shapely.ops import polygonize, unary_union
import ezdxf
import matplotlib.pyplot as plt

class GeometryExtractor:
    def __init__(self, dxf_file):
        self.doc = dxf_file
        self.modelspace = self.doc.modelspace()

    def load_layer_lines(self, layer_name):
        lines = []

        for e in self.modelspace.query("LINE"):
            if e.dxf.layer == layer_name:
                start = (e.dxf.start.x, e.dxf.start.y)
                end = (e.dxf.end.x,e.dxf.end.y)
                lines.append(LineString([start, end]))

        for e in self.modelspace.query("LWPOLYLINE"):
            if e.dxf.layer == layer_name:
                points = [(pt[0], pt[1]) for pt in e.get_points()]
                if not e.closed:
                    lines.append(LineString(points))
                else:
                    points.append(points[0])  # close the shape
                    lines.append(LineString(points))

        return lines

    def door_positions(self, layer_name):
        doors = []
        for e in self.modelspace.query("LWPOLYLINE"):
            if e.dxf.layer == layer_name:
                points = list(e.get_points())
                if points:
                    x = sum(p[0] for p in points) / len(points)
                    y = sum(p[1] for p in points) / len(points)
                    doors.append((x, y))
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
