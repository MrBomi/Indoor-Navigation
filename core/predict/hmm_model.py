
import math
from core.ManagerFloor import find_path
import time


class HMMModel:
    def __init__(self, graph: dict[int, list[int]], grid: dict[int, set[int]], coords_to_cells: dict[tuple[float, float], set[int]], startCoord: tuple[float, float], endCoord: tuple[float, float]):
        self.grid = grid
        self.find_grid_cells_path(coords_to_cells, graph, startCoord, endCoord)
        self.endCoord = endCoord
        self.startCoord = startCoord
        self.dynamic_cells_prob = None
        self.weight_transmition = 1
        self.weight_emission = 1
        self.visited_counter = {}
        self.history_penalty = 0.5
        self.time_stamp = None


    def find_grid_cells_path(self, coords_to_cells, graph ,start, end ):
        path = find_path(graph, start, end)
        self.grid_path = set(cells for coord in path for cells in coords_to_cells.get(coord, []))
        

    def set_dynamic_cells_prob(self, prev_cell: int):
        self.dynamic_cells_prob = {}
        self.total_weight_in_dynamic_prob = 0.0
        self.epsilon = 0.01
        weights = {
            "on_path": 20.0,
            "neighbor_of_path": 10.0,
            "neighbor": 5.0,
            "neighbor_of_neighbor_path": 2.5,
            "neighbor_of_neighbor": 1.0
        }
        cell_neighbors = self.grid.get(prev_cell, [])
        cell_neighbors = self.grid.get(prev_cell, [])
        for cell in cell_neighbors:
            if cell in self.grid_path:
                weight = weights["on_path"]
            elif any(n in self.grid_path for n in self.grid.get(cell, [])):
                weight = weights["neighbor_of_path"]
            else:
                weight = weights["neighbor"]

            self.dynamic_cells_prob[cell] = weight
            self.total_weight_in_dynamic_prob += weight

        for cell in cell_neighbors:
            for neighbor in self.grid.get(cell, []):
                if neighbor == prev_cell or neighbor in cell_neighbors:
                    continue  
                if neighbor in self.dynamic_cells_prob:
                    continue  

                if neighbor in self.grid_path:
                    weight = weights["neighbor_of_neighbor_path"]
                else:
                    weight = weights["neighbor_of_neighbor"]

                self.dynamic_cells_prob[neighbor] = weight
                self.total_weight_in_dynamic_prob += weight
           
        self.total_weight_in_dynamic_prob += self.epsilon * (len(self.grid) - len(self.dynamic_cells_prob)) 

    def viterbi(self, observations: dict[int, float]):
        max_prob = -math.inf
        best_cell = None
        for cell, emission_prob in observations.items():
            if self.dynamic_cells_prob is None:
                raise ValueError("Dynamic cells probabilities not set. Call set_dynamic_cells_prob first.")
            count = self.visited_counter.get(cell, 0)
            penalty = self.history_penalty ** count
            transition_prob = self.dynamic_cells_prob.get(cell, self.epsilon) / self.total_weight_in_dynamic_prob
            combined_score = (
                self.weight_emission * math.log(max(emission_prob, self.epsilon)) +
                self.weight_transmition * math.log(max(transition_prob, self.epsilon)) +
                math.log(penalty)
            )

            if combined_score > max_prob:
                max_prob = combined_score
                best_cell = cell

        self.visited_counter[best_cell] = self.visited_counter.get(best_cell, 0) + 1
        self.time_stamp = time.time()
        if best_cell not in self.dynamic_cells_prob.keys():
            return max(self.dynamic_cells_prob, key=self.dynamic_cells_prob.get) 
        return best_cell,  math.exp(max_prob)

    def step(self, observations: dict[int, float], prev_cell: int):
        self.set_dynamic_cells_prob(prev_cell)
        return self.viterbi(observations)
    

    def closest_point_to_path(self, pred_x: float, pred_y: float):
        path_points = self.grid_path
        if not path_points:
            raise ValueError("self.grid_path is empty.")
        if len(path_points) == 1:
            return path_points[0]

        closest_point = None
        smallest_distance_sq = float("inf")

        for i in range(len(path_points) - 1):
            start_x, start_y = path_points[i]
            end_x, end_y = path_points[i + 1]

            seg_dx = end_x - start_x
            seg_dy = end_y - start_y
            seg_length_sq = seg_dx * seg_dx + seg_dy * seg_dy

            if seg_length_sq == 0.0:
                proj_x, proj_y = start_x, start_y
            else:
                t = ((pred_x - start_x) * seg_dx + (pred_y - start_y) * seg_dy) / seg_length_sq
                t = max(0.0, min(1.0, t))
                proj_x = start_x + t * seg_dx
                proj_y = start_y + t * seg_dy

            diff_x = pred_x - proj_x
            diff_y = pred_y - proj_y
            distance_sq = diff_x * diff_x + diff_y * diff_y

            if distance_sq < smallest_distance_sq:
                smallest_distance_sq = distance_sq
                closest_point = (proj_x, proj_y)

        return closest_point
