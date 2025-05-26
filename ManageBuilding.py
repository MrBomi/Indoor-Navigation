import math
import heapq
from collections import defaultdict


class ManageBuilding:
    def __init__(self, graph, door_points, wall_lines, basic_svg, utils, svg_path):
        self.graph = graph
        self.door_points = door_points
        self.wall_lines = wall_lines
        self.basic_svg = basic_svg
        self.utils = utils
        self.svg_path = svg_path


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

    def crete_door_json(self):
        doors_json = []
        for i, pt in enumerate(self.door_points):
            x, y = self.utils.scale(pt.x, pt.y)
            doors_json.append({"id": i, "x": x, "y": y})
        return doors_json

    def getSvgPath(self):
        return self.svg_path