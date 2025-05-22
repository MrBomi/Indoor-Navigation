# import ezdxf
# import xml.etree.ElementTree as ET
# from xml.dom import minidom
# import math
# from collections import deque
# import GeometryExtractor
# from GeometryExtractor import roof_area
# from shapely.geometry import LineString, Point, MultiPolygon
#
# # --- Configuration ---
# DXF_FILE = "res/building001-0_floor2.dxf"
# DOOR_LAYER_NAME = "A-DOOR"
# WALL_LAYER_NAME = "A-WALL"
# OUTPUT_FILE = "DemoResults/test_graph_1.graphml"
# NODE_SIZE = 30.0  # Ellipse node diameter in pixels
# SCALE = 1
# OFFSET_CM = 200  # Offset in centimeters
#
#
#
#
# # --- Load DXF ---
# doc = ezdxf.readfile(DXF_FILE)
# msp = doc.modelspace()
#
# # --- Bounding Box Extraction ---
# def extract_bounding_box():
#     x_min, y_min = float('inf'), float('inf')
#     x_max, y_max = float('-inf'), float('-inf')
#
#     # Include LWPOLYLINE walls
#     for polyline in msp.query("LWPOLYLINE"):
#         if polyline.dxf.layer == WALL_LAYER_NAME:
#             for point in polyline.get_points():
#                 x, y = point[0], point[1]
#                 x_min = min(x_min, x)
#                 x_max = max(x_max, x)
#                 y_min = min(y_min, y)
#                 y_max = max(y_max, y)
#
#     # Include LINE walls
#     for line in msp.query("LINE"):
#         if line.dxf.layer == WALL_LAYER_NAME:
#             start = line.dxf.start
#             end = line.dxf.end
#             for x, y in [(start.x, start.y), (end.x, end.y)]:
#                 x_min = min(x_min, x)
#                 x_max = max(x_max, x)
#                 y_min = min(y_min, y)
#                 y_max = max(y_max, y)
#
#     return x_min, x_max, y_min, y_max
#
#
# x_min_raw, x_max_raw, y_min_raw, y_max_raw = extract_bounding_box()
#
#
# def normalize_point(x, y):
#     # Flip Y-axis: invert y relative to bounding box height
#     flipped_y = y_max_raw - y
#     return (x - x_min_raw) * SCALE, (flipped_y - y_min_raw) * SCALE
#
#
# def unnormalize_point(x, y):
#     unscaled_x = (x / SCALE) + x_min_raw
#     unflipped_y = y_max_raw - ((y / SCALE) + y_min_raw)
#     return unscaled_x, unflipped_y
#
#
#
# # --- Door Position Extraction ---
# door_positions = []
# for e in msp.query("LWPOLYLINE"):
#     if e.dxf.layer == DOOR_LAYER_NAME:
#         points = list(e.get_points())
#         if points:
#             x = sum(p[0] for p in points) / len(points)
#             y = sum(p[1] for p in points) / len(points)
#             door_positions.append((x, y))
#
# if not door_positions:
#     raise ValueError(f"No door positions found on layer: {DOOR_LAYER_NAME}")
#
# norm_positions = [normalize_point(x, y) for x, y in door_positions]
# x_min, y_min = normalize_point(x_min_raw, y_min_raw)
# x_max, y_max = normalize_point(x_max_raw, y_max_raw)
#
# # --- GraphML Boilerplate ---
# ET.register_namespace("", "http://graphml.graphdrawing.org/xmlns")
# ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
# ET.register_namespace("y", "http://www.yworks.com/xml/graphml")
#
# graphml = ET.Element("{http://graphml.graphdrawing.org/xmlns}graphml", {
#     "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation":
#     "http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd"
# })
#
# keys = [
#     ("d0", "graph", "Description", "string", None),
#     ("d1", "port", None, None, "portgraphics"),
#     ("d2", "port", None, None, "portgeometry"),
#     ("d3", "port", None, None, "portuserdata"),
#     ("d4", "node", "url", "string", None),
#     ("d5", "node", "description", "string", None),
#     ("d6", "node", None, None, "nodegraphics"),
#     ("d7", "graphml", None, None, "resources"),
#     ("d8", "edge", "url", "string", None),
#     ("d9", "edge", "description", "string", None),
#     ("d10", "edge", None, None, "edgegraphics"),
# ]
# for k_id, k_for, attr_name, attr_type, y_type in keys:
#     attr = {"id": k_id, "for": k_for}
#     if attr_name: attr["attr.name"] = attr_name
#     if attr_type: attr["attr.type"] = attr_type
#     if y_type: attr["yfiles.type"] = y_type
#     ET.SubElement(graphml, "key", attr)
#
# graph = ET.SubElement(graphml, "graph", edgedefault="directed", id="G")
# ET.SubElement(graph, "data", key="d0").text = ""
#
# # --- Helpers ---
# def has_node_within_radius(x, y, nodes, r):
#     for nx, ny in nodes:
#         if 0 < math.hypot(nx - x, ny - y) < r:
#             return True
#     return False
#
# def create_node(graph, node_id, x, y, color, label_text):
#     node = ET.SubElement(graph, "node", id=node_id)
#     data = ET.SubElement(node, "data", key="d6")
#     shape = ET.SubElement(data, "{http://www.yworks.com/xml/graphml}ShapeNode")
#
#     ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}Geometry",
#                   x=str(x), y=str(y), width=str(NODE_SIZE), height=str(NODE_SIZE))
#     ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}Fill",
#                   color=color, transparent="false")
#     ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}BorderStyle",
#                   color="#000000", type="line", width="1.0")
#     ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}NodeLabel",
#                   fontFamily="Dialog", fontSize="12", textColor="#000000").text = label_text
#     ET.SubElement(shape, "{http://www.yworks.com/xml/graphml}Shape", type="ellipse")
#
# # --- Node Placement ---
# nodes_queue = deque()
# all_positions = set()
# offset_px = OFFSET_CM * SCALE
#
# # Add yellow (door) nodes
# for i, (x, y) in enumerate(norm_positions):
#     create_node(graph, f"n{i}", x, y, "#FFCC00", str(i))
#     nodes_queue.append((i, x, y))
#     all_positions.add((x, y))
#
# # Expand with blue offset nodes
# directions = {
#     "right": (offset_px, 0),
#     "left": (-offset_px, 0),
#     "up": (0, -offset_px),
#     "down": (0, offset_px)
# }
#
# while nodes_queue:
#     i, x, y = nodes_queue.popleft()
#     for dir_name, (dx, dy) in directions.items():
#         bx, by = x + dx, y + dy
#         if not has_node_within_radius(bx, by, all_positions, offset_px)\
#                 and RoofManager.is_point_inside_geometry(roof_area,Point(unnormalize_point(bx,by))):
#             node_id = f"b{i}_{dir_name}"
#             create_node(graph, node_id, bx, by, "#3399FF", node_id)
#             if (bx, by) not in all_positions:
#                 all_positions.add((bx, by))
#                 nodes_queue.append((i, bx, by))
#
# # --- Export ---
# rough_string = ET.tostring(graphml, 'utf-8')
# pretty = minidom.parseString(rough_string).toprettyxml(indent="  ")
#
# with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#     f.write(pretty)
#
# print(f"✅ Graph exported to {OUTPUT_FILE} with {len(norm_positions)} yellow nodes and {len(all_positions) - len(norm_positions)} blue offset nodes.")
