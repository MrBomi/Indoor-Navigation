import xml.etree.ElementTree as ET
from xml.dom import minidom
from shapely.geometry import Point
import math
from collections import deque

from core.Utils import Utils
from core.GeometryExtractor import GeometryExtractor



class GraphBuilder:
    def __init__(self, output_file: str, node_size: float, offset_cm: float, scale: float ,roof_area: float):
        self.output_file = output_file
        self.node_size = node_size
        self.offset_px = offset_cm * scale
        self.graph, self.graphml = self._init_graphml()
        self.all_positions = set()
        self.queue = deque()
        self.roof_area = roof_area

    def _init_graphml(self):
        ET.register_namespace("", "http://graphml.graphdrawing.org/xmlns")
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace("y", "http://www.yworks.com/xml/graphml")

        graphml = ET.Element("{http://graphml.graphdrawing.org/xmlns}graphml", {
            "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation":
                "http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd"
        })

        keys = [
            ("d0", "graph", "Description", "string", None),
            ("d1", "port", None, None, "portgraphics"),
            ("d2", "port", None, None, "portgeometry"),
            ("d3", "port", None, None, "portuserdata"),
            ("d4", "node", "url", "string", None),
            ("d5", "node", "description", "string", None),
            ("d6", "node", None, None, "nodegraphics"),
            ("d7", "graphml", None, None, "resources"),
            ("d8", "edge", "url", "string", None),
            ("d9", "edge", "description", "string", None),
            ("d10", "edge", None, None, "edgegraphics"),
        ]
        for k_id, k_for, attr_name, attr_type, y_type in keys:
            attr = {"id": k_id, "for": k_for}
            if attr_name: attr["attr.name"] = attr_name
            if attr_type: attr["attr.type"] = attr_type
            if y_type: attr["yfiles.type"] = y_type
            ET.SubElement(graphml, "key", attr)

        graph = ET.SubElement(graphml, "graph", edgedefault="directed", id="G")
        ET.SubElement(graph, "data", key="d0").text = ""
        return graph, graphml

    def create_node(self, node_id, x, y, color, label_text):
        node = ET.SubElement(self.graph, "node", id=node_id)
        data = ET.SubElement(node, "data", key="d6")
        shape = ET.SubElement(data, "{http://www.yworks.com/xml/graphml}ShapeNode")

        ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}Geometry",
                      x=str(x), y=str(y), width=str(self.node_size), height=str(self.node_size))
        ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}Fill",
                      color=color, transparent="false")
        ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}BorderStyle",
                      color="#000000", type="line", width="1.0")
        ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}NodeLabel",
                      fontFamily="Dialog", fontSize="12", textColor="#000000").text = label_text
        ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}Shape", type="ellipse")

    def add_seed_nodes(self, norm_positions,color):
        for i, (x, y) in enumerate(norm_positions):
            self.create_node(f"n{i}", x, y, color, str(i))
            self.queue.append((i, x, y))
            self.all_positions.add((x, y))

    def add_lobby_nodes(self, norm_positions,color):
        for i, (x, y) in enumerate(norm_positions):
            self.create_node(f"n{i}_lobby", x, y, color, str(i))
            self.queue.append((i, x, y))
            self.all_positions.add((x, y))

    def expand_nodes(self,utils: Utils, geometry_extractor: GeometryExtractor):
        directions = {
            "right": (self.offset_px, 0),
            "left": (-self.offset_px, 0),
            "up": (0, -self.offset_px),
            "down": (0, self.offset_px)
        }

        i = 1
        for bx in range(math.floor(utils.norm_x(utils.x_min_raw)), math.ceil(utils.norm_x(utils.x_max_raw))):
            for by in range(math.floor(utils.norm_y(utils.y_min_raw)), math.ceil(utils.norm_y(utils.y_max_raw))):
                if self._is_far_enough(bx, by)\
                        and geometry_extractor.is_point_inside_geometry(self.roof_area,Point(utils.unscale(bx,by))):
                    node_id = f"b{i}_lobby"
                    self.create_node(node_id, bx, by, "#3399FF", node_id)
                    i = i + 1

    def _is_far_enough(self, x, y):
        return all(math.hypot(x - px, y - py) >= self.offset_px for (px, py) in self.all_positions)

    def export(self):
        rough_string = ET.tostring(self.graphml, 'utf-8')
        pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(pretty)

    def add_named_nodes(self, positions):
        for i, (x, y) in enumerate(positions):
            default_name = f"Node_{i+1}"
            user_input = input(f"Enter name for node at ({x:.2f}, {y:.2f}) [default: {default_name}]: ").strip()
            node_name = user_input if user_input else default_name
            self.create_node(node_name, x, y, "#FF6600", node_name)
            self.all_positions.add((x, y))
