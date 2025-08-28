from collections import defaultdict
from core.predict.hmm_model import HMMModel
import time
import threading


class PredictManager:
    def __init__(self):
        self.predicts = defaultdict()
        self.lock = threading.Lock()


    def get_new_id(self):
        with self.lock:
            find = False
            new_id = None
            for id, model in self.predicts.items():
                if model is None or model.time_stamp is None or (time.time() - model.time_stamp) > 300:
                    if not find:
                        find = True
                        new_id = id
                        del self.predicts[id]
            if not find:
                new_id = len(self.predicts) + 1
            return new_id

    def add_new_id(self):
        id = self.get_new_id()
        self.predicts[id] = None
        return id

    def add_new_model(self,graph, grid, coords_to_cells, startCoord, endCoord, id=None):
        if id is None:
            id = self.get_new_id()
        self.predicts[id] = HMMModel(graph, grid, coords_to_cells, startCoord, endCoord)
        return self.predicts[id]

    def do_step(self, id, observations: dict[int, float], prev_cell: int):
        if id not in self.predicts:
            raise ValueError(f"Predict model with ID {id} not found.")
        model = self.predicts[id]
        cell, prob = model.step(observations, prev_cell)
        return cell, prob
    
    def step1(self, id, prev_cell: int):
        if id not in self.predicts:
            raise ValueError(f"Predict model with ID {id} not found.")
        model = self.predicts[id]
        model.set_dynamic_cells_prob(prev_cell)
        return model.dynamic_cells_prob, model.total_weight_in_dynamic_prob
    
    def step2(self, id, observations: dict[int, float], prev_cell: int):
        if id not in self.predicts:
            raise ValueError(f"Predict model with ID {id} not found.")
        model = self.predicts[id]
        cell, prob = model.viterbi(observations)
        return cell, prob
    
    def get_model(self, id):
        return self.predicts.get(id, None)
    