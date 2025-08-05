
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
        return self.svg_file
    
    def continueAddBuilding(self, point1, point2, distance_cm):
        self.calculateScale(point1, point2, distance_cm)
        return self.createFloor()

    def calculateScale(self, point1, point2, distance_cm):
        point1_unscaled = self.utils.unscale(point1[0], point1[1])
        point2_unscaled = self.utils.unscale(point2[0], point2[1])
        distance_raw = math.sqrt((point2_unscaled[0] - point1_unscaled[0]) ** 2 + (point2_unscaled[1] - point1_unscaled[1]) ** 2)
        self.unit_scale = 1 #distance_cm / distance_raw
        self.spacing = math.floor(20 / self.unit_scale)
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

        coarse_to_fine = self.createGreedToSvg(graph)
        one_m_space = math.floor(100 / self.unit_scale)
        grid_svg, cell_id_to_coords = SvgManager.addGridToSvg(self.all_lines, coarse_to_fine, self.utils, one_m_space)
        building = ManagerFloor(graph, self.door_points, self.svg_file, grid_svg, self.utils, cell_id_to_coords, coarse_to_fine)
        return building
        
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
        coarse_spacing = math.floor(100 / self.unit_scale)
        x = round(min_x / coarse_spacing) * coarse_spacing
        count_over = 0
        count_less = 0
        while x <= max_x:
            y = round(min_y / coarse_spacing) * coarse_spacing
            while y <= max_y:
                center = (round(x, 6), round(y, 6))
                indices = tree.query_ball_point(center, threshold)
                if indices:
                    nearby = [graph_points[i] for i in indices]
                    if len(nearby) < 1 or len(nearby) > 4:
                        if len(nearby) > 4:
                            count_over += 1
                        else:
                            count_less += 1
                    coarse_to_fine[center] = nearby
                y += coarse_spacing
            x += coarse_spacing
        print(f"Coarse grid created with {len(coarse_to_fine)} points, {count_over} over 4 points, {count_less} less than 1 point")
        return coarse_to_fine

        
    