
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
        return best_cell,  math.exp(max_prob)

    def step(self, observations: dict[int, float], prev_cell: int):
        self.set_dynamic_cells_prob(prev_cell)
        return self.viterbi(observations)