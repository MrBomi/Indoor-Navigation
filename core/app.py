import ezdxf
import svgwrite
import math
from shapely.geometry import LineString, Point, MultiPolygon
from core.GraphBuilder import GraphBuilder
from core.Utils import Utils
from scipy.spatial import KDTree
from core.configLoader import Config
from core.GeometryExtractor import GeometryExtractor
import os
import json
import matplotlib.pyplot as plt
from shapely.geometry import Point
import core.Bitmap as bm
from core.ManagerFloor import ManagerFloor

class App:
    def __init__(self, config, dwg_path = None):
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
        if dwg_path is None:
            dwg_path = config.get('file','input_name')
        self.doc = ezdxf.readfile(dwg_path)
        self.scale = self.calcukateScale(config)
        if self.scale < 0:
            self.spacing = 40
        else:
            self.spacing = math.floor(0.5 / self.scale) 
        print(f"scale: {self.scale} spacing: {self.spacing}")

    def calcukateScale(self, config):
        distance = config.get('distance')
        if distance:
            point1 = distance.get('point1')
            point2 = distance.get('point2')
            real_distance_m = distance.get('real_distance')
            dx = point2[0] - point1[0]
            dy = point2[1] - point1[1]
            dxf_distance = math.hypot(dx, dy)
            scale_factor = real_distance_m / dxf_distance
            return scale_factor
        return -1


    def createFloor(self):
        WIDTH, HEIGHT = 800, 800
        output_dir = os.path.join("static", "output")
        svg_path = os.path.join(output_dir, self.svg_output_file)
        json_path = os.path.join(output_dir, self.json_output_file)

        os.makedirs(output_dir, exist_ok=True)

        extractor = GeometryExtractor(self.doc, self.offset_cm, self.scale)
        wall_lines = extractor.load_layer_lines(self.wall_layer)
        roof_lines = extractor.load_layer_lines(self.roof_layer)
        roof_area = extractor.create_combined_polygon_from_lines(extractor.load_layer_lines(self.roof_layer))
        all_lines = wall_lines + roof_lines

        door_coords = extractor.door_positions(self.door_layer)
        door_points = [Point(x, y) for x, y in door_coords]

        grid = extractor.generate_quantized_grid(roof_area, 30) #self.spacing)
        graph = bm.build_graph_with_bitmap(grid,door_points,wall_lines, 30) #self.spacing)

        min_x , max_x , min_y, max_y = extractor.extract_bounding_box(all_lines,door_points)
        utils = Utils(min_x, max_x, min_y, max_y)
        norm_positions = [utils.scale(x, y) for x, y in door_coords]

        roof_area = extractor.create_combined_polygon_from_lines(extractor.load_layer_lines(self.roof_layer))
        builder = GraphBuilder(self.output_file, self.node_size, self.offset_cm, self.scale, roof_area)
        builder.add_seed_nodes(norm_positions,"#FFCC00")
        builder.export()
        print(f"✅ graph written")

        svg = svgwrite.Drawing(self.svg_output_file, size=(f"{WIDTH}px", f"{HEIGHT}px"))
        #grid_svg = svgwrite.Drawing("static/output/grid_with_building.svg", size=(f"{WIDTH}px", f"{HEIGHT}px"))
        doors_json = []

        for line in all_lines:
            coords = [utils.scale(x, y) for x, y in line.coords]
            svg.add(svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))
            #grid_svg.add(grid_svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))

        #svg_greed = self.createGreedToSvg(graph)
        #self.addGridToSvg(grid_svg, svg_greed, utils, min_x, max_x)

        for i, pt in enumerate(door_points):
            x, y = utils.scale(pt.x, pt.y)
            #svg.add(svg.circle(center=(x, y), r=4, fill='black', stroke='none', id=f"door-{i}"))
            #svg.add(svg.text(str(i), insert=(x + 6, y - 6), font_size="8px", fill="blue"))
            doors_json.append({"id": i, "x": x, "y": y})

        svg.save()
        #grid_svg.save()
        return ManagerFloor(graph, door_points, svg, self.svg_output_file, utils)
    
    def addGridToSvg(self, grid_svg, coarse_to_fine, utils, min_x, max_x):
        cell_spacing = self.spacing * 2 
        cell_size_px = cell_spacing * (800 / (max_x - min_x)) 

        print("🟦 Drawing grid rectangles...")
        updated_coarse_to_fine = {}
        count = 0

        for coarse_pt, fine_pts in coarse_to_fine.items():
            x_svg, y_svg = utils.scale(coarse_pt[0], coarse_pt[1])

            grid_svg.add(grid_svg.rect(
                insert=(x_svg - cell_size_px / 2, y_svg - cell_size_px / 2),
                size=(cell_size_px, cell_size_px),
                fill='blue',
                fill_opacity=0.1,
                stroke='black',
                stroke_width=0.1,
                id=f"cell-{round(x_svg, 2)}-{round(y_svg, 2)}"
            ))

            updated_coarse_to_fine[(round(x_svg, 2), round(y_svg, 2))] = fine_pts
            count += 1

        print(f"🟦 Done drawing {count} grid squares.")
        return updated_coarse_to_fine

    
    def createGreedToSvg(self, graph):
        threshold = self.spacing * math.sqrt(2) * 0.9
        # Get graph nodes as Point objects
        graph_points = list(graph.keys())
        if not graph_points:
            return {}

        xs = [p[0] for p in graph_points]
        ys = [p[1] for p in graph_points]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Build KDTree for efficient search
        tree = KDTree(graph_points)

        coarse_to_fine = {}

        # Step 1: Build coarse grid (2*spacing)
        coarse_spacing = 2 * self.spacing
        x = round(min_x / coarse_spacing) * coarse_spacing
        while x <= max_x:
            y = round(min_y / coarse_spacing) * coarse_spacing
            while y <= max_y:
                center = (round(x, 6), round(y, 6))
                indices = tree.query_ball_point(center, threshold)
                if indices:
                    nearby = [graph_points[i] for i in indices]
                    if len(nearby) < 1 or len(nearby) > 4:
                        print(f"⚠️  Cell {center} has {len(nearby)}")
                    coarse_to_fine[center] = nearby
                y += coarse_spacing
            x += coarse_spacing

        return coarse_to_fine

