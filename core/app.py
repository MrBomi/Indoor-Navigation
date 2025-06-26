
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
        self.utils = None
        self.unit_scale = None
        self.spacing = None
        self.wall_lines = None


    
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
        self.svg_file = SvgManager.createSvgDrawing(WIDTH, HEIGHT, all_lines_to_svg, door_points_to_svg)
        return self.svg_file
    
    def continueAddBuilding(self, point1, point2, distance_cm):
        self.calculateScale(point1, point2, distance_cm)
        return self.createFloor()


    def calculateScale(self, point1, point2, distance_cm):
        point1_unscaled = self.utils.unscale(point1[0], point1[1])
        point2_unscaled = self.utils.unscale(point2[0], point2[1])
        distance_raw = math.sqrt((point2_unscaled[0] - point1_unscaled[0]) ** 2 + (point2_unscaled[1] - point1_unscaled[1]) ** 2)
        self.unit_scale = distance_cm / distance_raw
        self.spacing = math.floor(40 / self.unit_scale)
        print(f"scale: {self.scale} spacing: {self.spacing}")
    
    def createFloor(self):
        
        # output_dir = os.path.join("static", "output")
        # svg_path = os.path.join(output_dir, self.svg_output_file)
        # json_path = os.path.join(output_dir, self.json_output_file)

        # os.makedirs(output_dir, exist_ok=True)

        # extractor = GeometryExtractor(self.doc, self.offset_cm, self.scale)
        # wall_lines = extractor.load_layer_lines(self.wall_layer)
        # roof_lines = extractor.load_layer_lines(self.roof_layer)
        # roof_area = extractor.create_combined_polygon_from_lines(extractor.load_layer_lines(self.roof_layer))
        # all_lines = wall_lines + roof_lines

        # door_coords = extractor.door_positions(self.door_layer)
        # door_points = [Point(round(x, 5), round(y, 5)) for x, y in door_coords]

        grid = self.extractor.generate_quantized_grid(self.roof_area, self.spacing)
        graph = bm.build_graph_with_bitmap(grid,self.door_points,self.wall_lines,self.spacing)

        # min_x , max_x , min_y, max_y = self.extractor.extract_bounding_box(self.all_lines,self.door_points)
        # utils = Utils(min_x, max_x, min_y, max_y)
        norm_positions = [self.utils.scale(x, y) for x, y in self.door_coords]

        roof_area = self.extractor.create_combined_polygon_from_lines(self.extractor.load_layer_lines(self.roof_layer))
        builder = GraphBuilder(self.output_file, self.node_size, self.offset_cm, self.scale, roof_area)
        builder.add_seed_nodes(norm_positions,"#FFCC00")
        builder.export()
        print(f"✅ graph written")

        #svg = svgwrite.Drawing(self.svg_output_file, size=(f"{WIDTH}px", f"{HEIGHT}px"))
        doors_json = []

        # for line in all_lines:
        #     coords = [utils.scale(x, y) for x, y in line.coords]
        #     svg.add(svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))

        for i, pt in enumerate(self.door_points):
            x, y = self.utils.scale(pt.x, pt.y)
            #svg.add(svg.circle(center=(x, y), r=4, fill='black', stroke='none', id=f"door-{i}"))
            #svg.add(svg.text(str(i), insert=(x + 6, y - 6), font_size="8px", fill="blue"))
            doors_json.append({"id": i, "x": x, "y": y})

        # svg.save()
        building = ManagerFloor(graph, self.door_points, self.svg_file, self.utils)
        return building
    
    
   