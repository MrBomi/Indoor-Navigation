from collections import defaultdict
from core.ManagerFloor import find_path
import numpy as np
from scipy.spatial import KDTree


class Predict:
    def __init__(self, graph : dict, coarse_to_fine : dict, scan_data: dict, start: tuple, goal: tuple):
        self.graph = graph
        self.coarse_to_fine = coarse_to_fine
        self.gamma = 0.5
        self.epsilon = 0.05
        #self.feature_keys = ["declination", "inclination", "magnitude", "nx", "ny", "nz"]
        # self.graph = {
        #     self._to_coord(k): [self._to_coord(v) for v in vs]
        #     for k, vs in graph.items()
        # }

        #print(f"[DEBUG] graph mapped: {len(self.graph)} nodes")

        # self.coarse_to_fine = {
        #     self._to_coord(k): [self._to_coord(v) for v in vs]
        #     for k, vs in coarse_to_fine.items()
        # }

        #print(f"[DEBUG] coarse_to_fine mapped: {len(self.coarse_to_fine)} nodes")

        self.scan_data = {
            self._to_coord(k): v
            for k, v in scan_data.items()
        }

        print(f"[DEBUG] scan_data mapped: {len(self.scan_data)} nodes")
                
        self.cells = list(self.scan_data.keys())
        self.cell_to_idx = {
            coord: idx
            for idx, coord in enumerate(self.cells)
        }
        self.M = len(self.cells)

        print(f"[DEBUG] cells mapped: {self.M} cells")
        self.fine_points = list(self.graph.keys())
        self._kd_fine = KDTree(self.fine_points)


        start_p = self._find_closest_fine(start)
        self.path = find_path(graph, start_p, goal)        
        
        self._build_neighbors()

        print(f"[DEBUG] neighbors built: {len(self.neighbors)} neighbors")

        self._init_fingerprints()

        print(f"[DEBUG] fingerprints initialized: {self.fingerprints.shape}")
        
        self._build_Ppath()

        print(f"[DEBUG] Ppath initialized: {self.Ppath.shape}")

        self._init_memory(start_p)

        print(f"[DEBUG] memory initialized: {self.memory.shape}")

    @staticmethod
    def _to_coord(key):
        """Convert key 'x,y' or tuple to (float(x), float(y))."""
        if isinstance(key, tuple):
            return key
        x_str, y_str = key.split(',')
        return (float(x_str), float(y_str))

    def _find_closest_fine(self, point: tuple) -> tuple:
        loc = self._to_coord(point)
        dist, idx = self._kd_fine.query(loc)
        return self.fine_points[idx]

    def _build_neighbors(self):
        self.fine_to_coarse = defaultdict(set)
        for coarse_coord, fine_list in self.coarse_to_fine.items():
            for f in fine_list:
                self.fine_to_coarse[f].add(coarse_coord)

        coarse_neighbors = {c: set() for c in self.coarse_to_fine}

        for f1, nbrs in self.graph.items():
            for f2 in nbrs:
                for c1 in self.fine_to_coarse.get(f1, []):
                    for c2 in self.fine_to_coarse.get(f2, []):
                        coarse_neighbors[c1].add(c2)
                        coarse_neighbors[c2].add(c1)

        self.neighbors = []
        for coarse_coord in self.cells:         
            nbr_set = coarse_neighbors[coarse_coord] | {coarse_coord}
            
            nbr_idxs = [
                self.cell_to_idx[c]
                for c in nbr_set
                if c in self.cell_to_idx
            ]
            self.neighbors.append(nbr_idxs)

    def _build_Ppath(self):
        self.Ppath = np.zeros(self.M, dtype=float)
        path_coarse = set()
        for fine_coord in self.path:
            coord = self._to_coord(fine_coord)
            for coarse_coord in self.fine_to_coarse.get(coord, []):
                path_coarse.add(coarse_coord)

        path_idxs = []
        for c in path_coarse:
            if c in self.cell_to_idx:
                idx = self.cell_to_idx[c]
                self.Ppath[idx] = 1.0
                path_idxs.append(idx)

        for i in range(self.M):
            if self.Ppath[i] == 0 and any(p in self.neighbors[i] for p in path_idxs):
                self.Ppath[i] = self.gamma

    def _init_fingerprints(self):
        self.feature_keys = [
            k
            for k in next(iter(self.scan_data.values()))
            if k != 'name'
        ]
        self.n = len(self.feature_keys)

        self.fingerprints = np.zeros((self.M, self.n), dtype=float)

        for coord, features in self.scan_data.items():
            idx = self.cell_to_idx[coord]             
            self.fingerprints[idx, :] = [features[k] for k in self.feature_keys]

    def _init_memory(self, start):
        self.memory = np.zeros(self.M, dtype=float)
        #start_fine = self._to_coord(start)
        coarse_list = self.fine_to_coarse.get(start)
        if not coarse_list:
            raise ValueError(f"Start point {start} not found in coarse grid.")

        start_coarse = next(iter(coarse_list))
        start_idx = self.cell_to_idx[start_coarse]
        self.memory[start_idx] = 1.0