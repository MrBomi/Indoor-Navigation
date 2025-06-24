import xml.etree.ElementTree as ET
import math
import itertools

INPUT_FILE = 'floorplan.graphml'
OUTPUT_FILE = 'aligned_edges.graphml'
SCALE_FACTOR = 1.05875  # meters per pixel

# XML namespaces
NS = {
    'graphml': 'http://graphml.graphdrawing.org/xmlns',
    'y': 'http://www.yworks.com/xml/graphml'
}
ET.register_namespace('', NS['graphml'])
ET.register_namespace('y', NS['y'])

def get_node_positions(root):
    positions = {}
    for node in root.findall('.//graphml:node', NS):
        node_id = node.attrib['id']
        geometry = node.find('.//y:Geometry', NS)
        if geometry is not None:
            x = float(geometry.attrib['x'])
            y = float(geometry.attrib['y'])
            positions[node_id] = (x, y)
    return positions

def calculate_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) * SCALE_FACTOR

def aligned(p1, p2):
    return abs(p1[0] - p2[0]) < 1e-2 or abs(p1[1] - p2[1]) < 1e-2

def find_graph_element(root):
    return root.find('.//graphml:graph', NS)

def get_next_edge_id(graph):
    existing = {
        int(edge.attrib['id'].replace('e', ''))
        for edge in graph.findall('graphml:edge', NS)
        if edge.attrib['id'].startswith('e') and edge.attrib['id'][1:].isdigit()
    }
    return max(existing, default=-1) + 1

def find_edgegraphics_key(root):
    for key in root.findall('.//graphml:key', NS):
        if key.attrib.get('for') == 'edge' and key.attrib.get('yfiles.type') == 'edgegraphics':
            return key.attrib['id']
    raise ValueError("Could not find edgegraphics key.")

def add_aligned_edges(graph, positions, edge_key):
    edge_id_counter = get_next_edge_id(graph)
    node_ids = list(positions.keys())

    for source, target in itertools.combinations(node_ids, 2):
        p1, p2 = positions[source], positions[target]
        if aligned(p1, p2):
            dist = calculate_distance(p1, p2)

            for src, tgt in [(source, target), (target, source)]:
                edge = ET.SubElement(graph, f"{{{NS['graphml']}}}edge", {
                    'id': f'e{edge_id_counter}',
                    'source': src,
                    'target': tgt
                })
                edge_id_counter += 1

                data = ET.SubElement(edge, f"{{{NS['graphml']}}}data", key=edge_key)
                polyline = ET.SubElement(data, f"{{{NS['y']}}}PolyLineEdge")

                ET.SubElement(polyline, f"{{{NS['y']}}}Path")
                ET.SubElement(polyline, f"{{{NS['y']}}}LineStyle", type="line", width="1.0", color="#000000")
                ET.SubElement(polyline, f"{{{NS['y']}}}Arrows", source="none", target="none")

                label = ET.SubElement(polyline, f"{{{NS['y']}}}EdgeLabel")
                label.text = f"{dist:.2f} cm"

                ET.SubElement(polyline, f"{{{NS['y']}}}BendStyle", smoothed="false")

def main():
    tree = ET.parse(INPUT_FILE)
    root = tree.getroot()
    graph = find_graph_element(root)

    positions = get_node_positions(root)
    edge_key = find_edgegraphics_key(root)

    add_aligned_edges(graph, positions, edge_key)

    tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
    print(f"Saved aligned-edge graph with visible labels to '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    main()
