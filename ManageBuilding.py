import math
import heapq
from collections import defaultdict
from doors import Door
import svgwrite
import xml.etree.ElementTree as ET



class ManageBuilding:
    #def __init__(self, graph, door_points, wall_lines, basic_svg, utils, svg_path)
    def __init__(self, graph, door_points, basic_svg, svg_path, utils):
        self.graph = graph
        #self.door_points = door_points
        #self.wall_lines = wall_lines
        self.basic_svg = basic_svg
        #self.utils = utils
        self.x_min_raw = utils.x_min_raw
        self.x_max_raw = utils.x_max_raw
        self.y_min_raw = utils.y_min_raw
        self.y_max_raw = utils.y_max_raw
        self.svg_path = svg_path
        self.doors_data = {}
        self.output_path = "static/output/output_with_path.svg"
        self.createDoorsData(door_points)

    def getSvgString(self):
        if not self.basic_svg:
            raise ValueError("Basic SVG is not initialized.")
        return self.basic_svg.tostring()
    
    def getGraph(self):
        if not self.graph:
            raise ValueError("Graph is not initialized.")
        return self.graph
    
    def getDoorsData(self):
        if not self.doors_data:
            raise ValueError("Doors data is not initialized.")
        return self.doors_data
    
    def getXMinRaw(self):
        if not self.x_min_raw:
            raise ValueError("X min raw value is not initialized.")
        return self.x_min_raw
    
    def getXMaxRaw(self):
        if not self.x_max_raw:
            raise ValueError("X max raw value is not initialized.")
        return self.x_max_raw
    
    def getYMinRaw(self):
        if not self.y_min_raw:
            raise ValueError("Y min raw value is not initialized.")
        return self.y_min_raw
    
    def getYMaxRaw(self):
        if not self.y_max_raw:
            raise ValueError("Y max raw value is not initialized.")
        return self.y_max_raw

    def find_path(self, start, goal):
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

            for neighbor in self.graph[current]:
                tentative_g = g_score[current] + heuristic(current, neighbor)
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))
        return None

    def scale(self,x, y):
        norm_x = (x - self.x_min_raw) / (self.x_max_raw - self.x_min_raw + 1e-6)
        norm_y = (y - self.y_min_raw) / (self.y_max_raw - self.y_min_raw + 1e-6)
        return norm_x * 800, (1 - norm_y) * 800  # flipped Y to match SVG view

    def createDoorsData(self, door_points):
        self.doors_data = {}
        for i, pt in enumerate(door_points):
            self.doors_data[i] = Door(i, pt.x, pt.y)

    # def crete_door_json(self):
    #     doors_json = []
    #     for i, pt in enumerate(self.door_points):
    #         self.doors_data[i] = Door(i, pt.x, pt.y)
    #         #x, y = self.utils.scale(pt.x, pt.y)
    #         x, y = self.scale(pt.x, pt.y)
    #         doors_json.append({"id": i, "x": x, "y": y})
    #     return doors_json

    def crete_door_json(self):
        doors_json = []
        for i, door in self.doors_data.items():
            x, y = self.scale(door.getX(), door.getY())
            doors_json.append({"id": i, "x": x, "y": y})
        return doors_json

    def getSvgPath(self):
        return self.svg_path
    
    def updateDoorsNames(self, doors):
        for door_id, name in doors.items():
            key = int(door_id)
            if  key in self.doors_data:
                self.doors_data[key].setName(name)
            else:
                raise ValueError(f"Door ID {door_id} not found in building data.")
        self.changeKeyToName()
        #self.updateSvgDoorNames(doors)
    
    def updateSvgDoorNames(self, id_to_name):
        if not self.basic_svg:
            raise ValueError("Basic SVG is not initialized.")
        tree = ET.parse(self.svg_path)
        root = tree.getroot()

        ns = {'svg': 'http://www.w3.org/2000/svg'}
        ET.register_namespace('', ns['svg'])

        for element in root.findall(".//{http://www.w3.org/2000/svg}text"):
            original_text = element.text
            if original_text is None:
                continue

            try:
                id_number = original_text.strip()
            except ValueError:
                continue 

            if id_number in id_to_name:
                element.text = id_to_name[id_number]

        tree.write(self.svg_path, encoding="utf-8", xml_declaration=True)

    def changeKeyToName(self):
        new_data = {}
        for door_id, door in self.doors_data.items():
            name = door.getName()
            if not name:
                raise ValueError(f"Door ID {door_id} does not have a name set.")
            if name in new_data:
                raise ValueError(f"Duplicate door name detected: '{name}' already exists.")
            new_data[name] = door
        self.doors_data = new_data 

    def getPath(self, start, goal):
        # startPoint = self.doors_data.get(start).getPoint()
        # goalPoint = self.doors_data.get(goal).getPoint()

        start_p = self.doors_data.get(start).getCoordinates()
        goal_p = self.doors_data.get(goal).getCoordinates()
        path = self.find_path(start_p, goal_p)
        if path is None:
            raise ValueError("No path found between the specified points.")
        return path
    
    def getSvgDrawing(self):
        return self.output_path

    def draw_path(self, path, color='red', stroke_width=2):
        if not self.basic_svg:
            raise ValueError("Basic SVG is not initialized.")
        scaled_path = [self.scale(x, y) for x, y in path]
        drawing = self.copy_svg_drawing(self.basic_svg)
        drawing.add(drawing.polyline(points=scaled_path, stroke=color, stroke_width=stroke_width, fill='none', id="path"))
        drawing.saveas(self.output_path)

    
    def copy_svg_drawing(self, original_svg: svgwrite.Drawing) -> svgwrite.Drawing:
        copied_svg = svgwrite.Drawing(size=original_svg['width'], height=original_svg['height'])
        copied_svg.attribs.update(original_svg.attribs)
        copied_svg.embed_stylesheet = original_svg.embed_stylesheet
        for element in original_svg.elements:
            copied_svg.add(element.copy())
        return copied_svg
    
    def getSvgWithPath(self, start, goal):
        path = self.getPath(start, goal)
        self.draw_path(path)
        return self.getSvgDrawing()

def find_path(graph, start, goal):
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
                if neighbor == (69221200.0, 27675600.0):
                    print(f"Adding neighbor {neighbor} with f_score {f_score}")
                heapq.heappush(open_set, (f_score, neighbor))
    return None

def scale(x, y, x_min_raw, x_max_raw, y_min_raw, y_max_raw):
    norm_x = (x - x_min_raw) / (x_max_raw - x_min_raw + 1e-6)
    norm_y = (y - y_min_raw) / (y_max_raw - y_min_raw + 1e-6)
    return norm_x * 800, (1 - norm_y) * 800  # flipped Y to match SVG view

def draw_path(svg, path, x_min_raw, x_max_raw, y_min_raw, y_max_raw, color='red', stroke_width=2):
    SVG_NS = "http://www.w3.org/2000/svg"
    ET.register_namespace("", SVG_NS)

    scaled_path = [scale(x, y, x_min_raw, x_max_raw, y_min_raw, y_max_raw) for x, y in path]
    svg_root = ET.fromstring(svg)

    points_str = " ".join(f"{x},{y}" for x, y in scaled_path)
    path_element = ET.Element(f"{{{SVG_NS}}}polyline", {
        'points': points_str,
        'stroke': color,
        'stroke-width': str(stroke_width),
        'fill': 'none',
        'id': 'path'
    })

    svg_root.append(path_element)
    return ET.tostring(svg_root, encoding='utf-8', xml_declaration=True).decode('utf-8')


def get_svg_with_path(svg, graph, start, goal, x_min_raw, x_max_raw, y_min_raw, y_max_raw):
    path = find_path(graph, start, goal)
    if path is None:
        raise ValueError("No path found between the specified points.")
    return draw_path(svg, path, x_min_raw, x_max_raw, y_min_raw, y_max_raw)

def update_svg_door_names(svg, doors_data, x_min_raw, x_max_raw, y_min_raw, y_max_raw, radius=4, color='blue'):
    SVG_NS = "http://www.w3.org/2000/svg"
    ET.register_namespace("", SVG_NS)

    svg_root = ET.fromstring(svg)

    for door in doors_data:
        x, y = scale(door["x"], door["y"], x_min_raw, x_max_raw, y_min_raw, y_max_raw)
        name = door.get("name", f"Door {door['id']}")

        circle = ET.SubElement(svg_root, f"{{{SVG_NS}}}circle", {
            'cx': str(x),
            'cy': str(y),
            'r': str(radius),
            'fill': color,
            'stroke': 'black',
            'stroke-width': '1',
            'id': f'door-{door["id"]}'
        })

        text = ET.SubElement(svg_root, f"{{{SVG_NS}}}text", {
            'x': str(x),
            'y': str(y - radius - 2),
            'font-size': "10",
            'fill': "black",
            'text-anchor': "middle"
        })
        text.text = name

    return ET.tostring(svg_root, encoding='utf-8', xml_declaration=True).decode('utf-8')