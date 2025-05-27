import ezdxf
import svgwrite

import math


from shapely.geometry import LineString, Point, MultiPolygon
from GraphBuilder import GraphBuilder
from Utils import Utils

from configLoader import Config
from GeometryExtractor import GeometryExtractor
import os
import json
import matplotlib.pyplot as plt
from shapely.geometry import Point
import Bitmap as bm
from ManageBuilding import ManageBuilding

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

    # def test(self):
    #     output_dir = "static/output"
    #     svg_input_path = os.path.join(output_dir, "output.svg")
    #     json_path = os.path.join(output_dir, "doors.json")
    #     svg_output_path = os.path.join(output_dir, "output_with_doors.svg")
    #
    #     # Load door coordinates from JSON
    #     with open(json_path, "r", encoding="utf-8") as f:
    #         data = json.load(f)
    #
    #     doors = data["doors"]
    #
    #     # Load existing SVG content
    #     tree = ET.parse(svg_input_path)
    #     root = tree.getroot()
    #
    #     # SVG namespace
    #     ns = {'svg': 'http://www.w3.org/2000/svg'}
    #     ET.register_namespace('', ns['svg'])  # Register default namespace
    #
    #     # Add new <circle> elements for each door
    #     for door in doors:
    #         x = door["x"]
    #         y = door["y"]
    #
    #         circle = ET.Element('circle', {
    #             'cx': str(x),
    #             'cy': str(y),
    #             'r': '4',
    #             'fill': 'red',
    #             #'stroke': 'black',
    #             #'stroke-width': '0.5'
    #         })
    #         root.append(circle)
    #
    #     # Save updated SVG
    #     tree.write(svg_output_path, encoding="utf-8", xml_declaration=True)
    #
    #     print(f"✅ Updated SVG with red door circles saved to: {svg_output_path}")
    #
    #     plt.show()

    def run(self):
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

        grid = extractor.generate_quantized_grid(roof_area, 30)
        graph = bm.build_graph_with_bitmap(grid,door_points,wall_lines,30)

        #pathFind = ManageBuilding(graph, door_points, wall_lines)

        #start = (-388.1676171169763,2238.452643791598) # 13
        #end =(6230.032944379447,810.1576336265814) # 6

        start = (69221951.48698045, 27675262.802139413) #14
        end = (69221357.78242427, 27677144.81186621) #4

        #start =(4351.4499912220235,868.0000274175329)# 17
        #start = (3094.999236916683,1622.061945066984)#22
        #end = (4240.0036833095455,1622.061587634103) #21
        #end = (2680.002006415428,1622.062082592983) # 23
        # path = pathFind.astar(graph, start, end)
        # path = extractor.astar(graph, start, end)
        #
        # if path:
        #     for p in path:
        #         print(f"Path step: {p}")
        # else:
        #     print("No path found")

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

        # if path:
        #     scaled_path = [utils.scale(x, y) for x, y in path]
        #     dwg.add(dwg.polyline(points=scaled_path, stroke='red', stroke_width=2, id="astar-path"))

        for line in all_lines:
            coords = [utils.scale(x, y) for x, y in line.coords]
            svg.add(svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))

        for i, pt in enumerate(door_points):
            x, y = utils.scale(pt.x, pt.y)
            svg.add(svg.circle(center=(x, y), r=4, fill='black', stroke='none', id=f"door-{i}"))
            svg.add(svg.text(str(i), insert=(x + 6, y - 6), font_size="8px", fill="blue"))
            doors_json.append({"id": i, "x": x, "y": y})

        svg.save()
        #return ManageBuilding(graph, door_points, wall_lines, svg, utils, self.svg_output_file)
        return ManageBuilding(graph, door_points, svg, self.svg_output_file, utils)


        # with open(json_path, "w", encoding="utf-8") as f:
        #     json.dump({
        #         "image_url": f"/static/output/{self.svg_output_file}",
        #         "doors": doors_json
        #     }, f, indent=2)
        #
        # print(f"✅ SVG written to {svg_path}")
        # print(f"✅ JSON written to{json_path}")
