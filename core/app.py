
import ezdxf
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

        grid = extractor.generate_quantized_grid(roof_area, 40)
        graph = bm.build_graph_with_bitmap(grid,door_points,wall_lines,40)

        min_x , max_x , min_y, max_y = extractor.extract_bounding_box(all_lines,door_points)
        utils = Utils(min_x, max_x, min_y, max_y)
        norm_positions = [utils.scale(x, y) for x, y in door_coords]

        roof_area = extractor.create_combined_polygon_from_lines(extractor.load_layer_lines(self.roof_layer))
        builder = GraphBuilder(self.output_file, self.node_size, self.offset_cm, self.scale, roof_area)
        builder.add_seed_nodes(norm_positions,"#FFCC00")
        builder.export()
        print(f"✅ graph written")

        svg = svgwrite.Drawing(self.svg_output_file, size=(f"{WIDTH}px", f"{HEIGHT}px"))
        doors_json = []

        for line in all_lines:
            coords = [utils.scale(x, y) for x, y in line.coords]
            svg.add(svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))

        for i, pt in enumerate(door_points):
            x, y = utils.scale(pt.x, pt.y)
            #svg.add(svg.circle(center=(x, y), r=4, fill='black', stroke='none', id=f"door-{i}"))
            #svg.add(svg.text(str(i), insert=(x + 6, y - 6), font_size="8px", fill="blue"))
            doors_json.append({"id": i, "x": x, "y": y})

        svg.save()
        return ManagerFloor(graph, door_points, svg, self.svg_output_file, utils)