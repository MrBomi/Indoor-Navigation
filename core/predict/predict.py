from collections import defaultdict
from core.ManagerFloor import find_path
import numpy as np
from scipy.spatial import KDTree


class Predict:
    def __init__(self, graph : dict, coords_to_cell: dict, cell_to_coords: dict, grid_graph: dict, scan_data: dict, start: tuple, goal: tuple):
        self.graph = graph
        self.coords_to_cell = coords_to_cell
        self.cell_to_coords = cell_to_coords
        self.grid_graph = grid_graph
        self.scan_data = scan_data
        self.start = start
        self.goal = goal
        self.gamma = 0.5
        self.epsilon = 0.05
        self.sigma = 0.1
        # Pit escape controls
        self.escape_k = 4          # number of nearest cells to consider when escaping a pit
        self.escape_radius = None   # optional max radius for escape candidates (e.g., 250.0); None disables
        self.escape_tau = 150.0     # distance decay length-scale for escape weighting (smaller => shorter hops)
        self.K = 3.0               # observation (emission) mixing weight
        self.delta_stay = 0.05     # slower forgetting for the emission winner
        self.delta_move = 0.25     # faster forgetting elsewhere
        self.min_prob = 1e-12      # numerical floor for stability
        self.transition_weight = 0.6
        self.emission_weight = 0.3
        self.locality_weight = 0.1
        self.distance_tau = 300.0
        self.memory_momentum = 0.1
        # self.scan_data = {
        #     self._to_coord(k): v
        #     for k, v in scan_data.items()
        # }
        #self.coarse_points = list(coarse_to_fine.keys())
        self._kd_coarse = KDTree(self.coarse_points)

        #self.scan_data = self.fix_scan(scan_data)
        self.cells = list(self.scan_data.keys())
        self.cell_to_idx = {
            coord: idx
            for idx, coord in enumerate(self.cells)
        }
        self.M = len(self.cells)

        self.fine_points = list(self.graph.keys())
        self._kd_fine = KDTree(self.fine_points)
        self._kd_cells = KDTree(self.cells)
        
        start_p = self._find_closest_fine(start)
        self.path = find_path(graph, start_p, goal)        
        
        #self._build_neighbors()

        self._init_fingerprints()
        
        self._build_Ppath()

        self._init_memory(start_p)

        self._estimate_sigma_median_nn()

        self._gauss_coeff = 1 / ((2 * np.pi)**(self.n/2) * self.sigma**self.n)
        
        self.use_emission_normalization = True

        self.stay_penalty = 0.25      # <1.0 discourages staying; try 0.25–0.5
        self.path_local_tau = 300.0    # locality length-scale; try 150–500

    @staticmethod
    def _to_coord(key):
        """Convert key 'x,y' or tuple to (float(x), float(y))."""
        if isinstance(key, tuple):
            return key
        x_str, y_str = key.split(',')
        return (float(x_str), float(y_str))

    def fix_scan(self, scan_data: dict) -> dict:
        """Fix scan data to match coarse points."""
        fixed_scan = {}
        for name, features in scan_data.items():
            coord = self._to_coord(name)
            if coord in self.coarse_points:
                fixed_scan[coord] = features
            else:
                # Find the closest coarse point
                closest_coarse = self._find_closest_coarse(coord)
                fixed_scan[closest_coarse] = features
        return fixed_scan
        
    def _find_closest_fine(self, point: tuple) -> tuple:
        loc = self._to_coord(point)
        dist, idx = self._kd_fine.query(loc)
        return self.fine_points[idx]

    def _find_closest_coarse_index(self, point: tuple) -> int:
        loc = self._to_coord(point)
        _, idx = self._kd_cells.query(loc)
        return int(idx)

    def _find_closest_coarse(self, point: tuple) -> tuple:
        dist, idx = self._kd_coarse.query(self._to_coord(point))
        return self.coarse_points[idx]

    def _build_neighbors(self):
        self.fine_to_coarse = defaultdict(set)
        for coarse_coord, fine_list in self.coarse_to_fine.items():
            for f in fine_list:
                self.fine_to_coarse[f].add(coarse_coord)

        #coarse_neighbors = {c: set() for c in self.coarse_to_fine}
        coarse_neighbors = {c: set() for c in self.cells}

        treshold = 75**2 + 75**2

        for f1, nbrs in self.graph.items():
            for f2 in nbrs:
                for c1 in self.fine_to_coarse.get(f1, []):
                    for c2 in self.fine_to_coarse.get(f2, []):
                        if c1 in coarse_neighbors and c2 in coarse_neighbors:
                             coarse_neighbors[c1].add(c2)
                             coarse_neighbors[c2].add(c1)
                        # idx1 = self._find_closest_coarse_index(c1)
                        # idx2 = self._find_closest_coarse_index(c2)
                        # c1_snap = self.cells[idx1]
                        # c2_snap = self.cells[idx2]
                        # dx1 = c1[0] - c1_snap[0]
                        # dy1 = c1[1] - c1_snap[1]
                        # dx2 = c2[0] - c2_snap[0]
                        # dy2 = c2[1] - c2_snap[1]
                        # ok1 = (dx1*dx1 + dy1*dy1) <= treshold
                        # ok2 = (dx2*dx2 + dy2*dy2) <= treshold
                        #if ok1 and ok2:
                        #

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
            for coarse_coord in self.coords_to_cell.get(coord, set()):
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
        self.feature_keys = [k for k in next(iter(self.scan_data.values())) if k != 'name']
        self.n = len(self.feature_keys)
        self.fingerprints = np.zeros((self.M, self.n), dtype=float)
        for coord, features in self.scan_data.items():
            idx = self.cell_to_idx[coord]
            self.fingerprints[idx, :] = [features[k] for k in self.feature_keys]

        # z-score normalization
        self.feat_mean = self.fingerprints.mean(axis=0)
        self.feat_std  = self.fingerprints.std(axis=0) + 1e-12
        self.fingerprints = (self.fingerprints - self.feat_mean) / self.feat_std

    def _init_memory(self, start):
        self.memory = np.zeros(self.M, dtype=float)
        #start_fine = self._to_coord(start)
        coarse_list = self.coords_to_cell.get(start)
        if not coarse_list:
            raise ValueError(f"Start point {start} not found in coarse grid.")

        start_coarse = next(iter(coarse_list))
        if start_coarse in self.cells:
            start_idx = self.cell_to_idx[start_coarse]
            #find the nearst coarse cell
        else: 
            start_idx = self._find_closest_coarse_index(start)
        self.memory[start_idx] = 1.0

    def _estimate_sigma_median_nn(self) -> float:
        F = self.fingerprints
        M = F.shape[0]

        dists = np.full(M, np.inf)
        for i in range(M):
            diffs = F - F[i]
            dist2 = np.sum(diffs*diffs, axis=1)
            dist2[i] = np.inf           
            dists[i] = np.sqrt(dist2.min())

        self.sigma = float(np.median(dists))

    def _input_layer(self, x):
        x_t = np.asarray(x, dtype=float)
        if x_t.shape != (self.n,):
            raise ValueError(f"Expected input shape ({self.n},), got {x_t.shape}")
        # apply same z-score
        x_t = (x_t - self.feat_mean) / self.feat_std
        return x_t
    
    def _gaussian_layer(self, x_t: np.ndarray) -> np.ndarray:
        diff = self.fingerprints - x_t            # shape (M, n)
        dist2 = np.sum(diff**2, axis=1)           # shape (M,)
        return self._gauss_coeff * np.exp(-dist2 / (2 * self.sigma ** 2))

    def _summation_layer(self, p: np.ndarray) -> np.ndarray:
        return p.copy()
    
    def step_emission(self, x) -> np.ndarray:
        # 1. Input
        x_t = self._input_layer(x)
        # 2. Gaussian
        p = self._gaussian_layer(x_t)
        # 3. Summation
        G_t = self._summation_layer(p)
        return G_t
    
    def _mix_baseline_with_weights(self, eps: float, size: int, weights: np.ndarray) -> np.ndarray:
        """
        Create a probability vector that mixes exploration and exploitation:
        - baseline: eps / size (uniform over all targets)
        - preference: (1 - eps) distributed proportionally to `weights`
        (falls back to uniform if all weights are zero)
        Returns a length-`size` vector that sums to 1.
        """
        out = np.full(size, eps / size, dtype=float)
        w = np.asarray(weights, dtype=float)
        if np.any(w > 0):
            out += (1.0 - eps) * (w / w.sum())
        else:
            out += (1.0 - eps) / size
        return out

    def _pit_candidates(self, j: int) -> tuple[np.ndarray, np.ndarray]:
        """
        For a 'pit' cell j (neighbor set == {j}), produce short-hop escape candidates:
        - take k nearest cells by KDTree (excluding j),
        - optionally filter by radius if self.escape_radius is set,
        - fallback to 'all other cells' if filtering leaves no candidates.
        Returns:
        idxs: candidate indices (shape: (E,))
        dists: Euclidean distances from j to each candidate (shape: (E,))
        """
        pos_j = np.asarray(self.cells[j], dtype=float)
        k = min(self.escape_k + 1, self.M)  # +1 because j itself will be returned and excluded
        dists, idxs = self._kd_cells.query(pos_j, k=k)
        dists = np.atleast_1d(dists)
        idxs = np.atleast_1d(idxs)

        # exclude self
        mask = (idxs != j)
        idxs = idxs[mask]
        dists = dists[mask]

        # optional radius cap
        R = self.escape_radius
        if R is not None:
            mR = (dists <= R)
            if mR.any():
                idxs = idxs[mR]
                dists = dists[mR]

        # fallback: all others if no candidate remains
        if idxs.size == 0:
            others = np.arange(self.M)
            idxs = others[others != j]
            all_cells = np.asarray(self.cells, dtype=float)
            dvec = all_cells[idxs] - pos_j
            dists = np.linalg.norm(dvec, axis=1)

        return idxs, dists

    def _pit_weights(self, idxs: np.ndarray, dists: np.ndarray) -> np.ndarray:
        """
        Build pit-escape preference weights for the candidate set:
        - path preference via Ppath[idxs]
        - locality via exp(-(d/tau)^2)
        - combined multiplicatively: w = Ppath * locality
        - if combined weights are all zero, fall back to locality-only
        """
        P_cand = self.Ppath[idxs]
        if self.escape_tau and self.escape_tau > 0:
            locality = np.exp(- (dists / float(self.escape_tau)) ** 2)
        else:
            locality = np.ones_like(dists)
        w = P_cand * locality
        if not np.any(w > 0):
            w = locality
        return w

    def _regular_weights(self, j: int, nbrs: list[int]) -> np.ndarray:
        """
        Path preference with local weighting around the current cell j,
        plus a penalty on self-loop.
        """
        w = self.Ppath[nbrs].astype(float).copy()

        # locality around current cell j
        pos_j = np.asarray(self.cells[j], dtype=float)
        pos_n = np.asarray([self.cells[i] for i in nbrs], dtype=float)
        d = np.linalg.norm(pos_n - pos_j, axis=1)
        if self.path_local_tau and self.path_local_tau > 0:
            locality = np.exp(- (d / float(self.path_local_tau)) ** 2)
            w *= locality

        # penalize self-loop if present
        try:
            jj = nbrs.index(j)
            w[jj] *= float(self.stay_penalty)
        except ValueError:
            pass

        return w
    
    def _transition_predict(self) -> np.ndarray:
        M_prev = self.memory
        M_pred = np.zeros(self.M, dtype=float)
        eps = float(self.epsilon)

        for j, nbrs in enumerate(self.neighbors):
            deg = len(nbrs)

            # pit case unchanged...
            if deg == 1 and nbrs[0] == j:
                idxs, dists = self._pit_candidates(j)
                w = self._pit_weights(idxs, dists)
                out = self._mix_baseline_with_weights(eps, len(idxs), w)
                M_pred[idxs] += M_prev[j] * out
                continue

            # regular case with self-loop penalty
            weights = self._regular_weights(j, nbrs)
            out = self._mix_baseline_with_weights(eps, deg, weights)
            M_pred[nbrs] += M_prev[j] * out

        return M_pred

    def _normalize_dist(self, v: np.ndarray) -> np.ndarray:
        """
        L1-normalize a nonnegative vector into a probability distribution.
        If the sum is non-positive or non-finite, fall back to a uniform distribution.
        """
        v = np.asarray(v, dtype=float)
        v[~np.isfinite(v)] = 0.0
        v = np.maximum(v, 0.0)
        s = v.sum()
        if not np.isfinite(s) or s <= 0:
            return np.full(self.M, 1.0 / self.M, dtype=float)
        return v / s

    def _emission_argmax_index(self, G_t: np.ndarray) -> int:
        """
        Return the index of the strongest emission G_t (ties -> first max).
        Robust to NaNs by treating them as -inf.
        """
        G = np.asarray(G_t, dtype=float)
        G = np.where(np.isfinite(G), G, -np.inf)
        return int(np.argmax(G))

    # def _memory_update(self, M_pred: np.ndarray, G_t: np.ndarray) -> np.ndarray:
    #     """
    #     HMM-style multiplicative update to prevent non-neighbor jumps:
    #         M(t) ∝ M_pred ⊙ L(x_t)
    #     where L(x_t) is an emission likelihood vector derived from G_t.

    #     We stabilize numerics by rescaling G_t by its max (scale cancels on normalization).
    #     Optionally keep winner-based delta as a mild inertia via exponent alpha.
    #     """
    #     # emission likelihood (rescaled to [0,1])
    #     G = np.asarray(G_t, dtype=float)
    #     gmax = float(np.max(G))
    #     if not np.isfinite(gmax) or gmax <= 0.0:
    #         # fallback: uniform likelihood if emission is degenerate
    #         L = np.ones_like(G)
    #     else:
    #         L = G / gmax

    #     # optional inertia via exponents (keep defaults = 1.0 for pure HMM update)
    #     alpha_stay = 1.0
    #     alpha_move = 1.0

    #     # winner index (by raw emission)
    #     i_star = self._emission_argmax_index(G_t)

    #     # per-cell exponent to mimic your delta_stay/move idea, but multiplicatively
    #     alpha = np.full(self.M, alpha_move, dtype=float)
    #     alpha[i_star] = alpha_stay

    #     # multiplicative Bayes-style update
    #     M_raw = np.asarray(M_pred, dtype=float) * (L ** alpha)

    #     # numerical floor + normalize
    #     M_raw = np.maximum(M_raw, self.min_prob)
    #     M_t = self._normalize_dist(M_raw)

    #     self.memory = M_t
    #     return M_t

    def _memory_update(self, M_pred: np.ndarray, G_t: np.ndarray) -> np.ndarray:
        """
        Strict HMM update:
            M(t) ∝ M_pred ⊙ L(x_t)
        Cells with M_pred == 0 stay unreachable (no teleport).
        """
        # 1) Keep transition zeros as zeros (no global floor)
        M_pred_clean = np.asarray(M_pred, dtype=float)
        M_pred_clean[~np.isfinite(M_pred_clean)] = 0.0
        M_pred_clean = np.maximum(M_pred_clean, 0.0)

        # 2) Emission likelihood rescaled by its max (scale cancels on normalization)
        G = np.asarray(G_t, dtype=float)
        G[~np.isfinite(G)] = 0.0
        gmax = float(G.max())
        L = np.ones_like(G) if gmax <= 0.0 else (G / gmax)

        # 3) Hard mask: unreachable cells get zero likelihood
        reachable = (M_pred_clean > 0.0)
        L_masked = np.zeros_like(L)
        L_masked[reachable] = L[reachable]

        # 4) Multiplicative Bayes update + normalize
        M_raw = M_pred_clean * L_masked
        if not np.any(M_raw > 0):
            M_raw = M_pred_clean.copy()  # fallback if everything underflowed

        # IMPORTANT: do NOT apply a global floor here
        M_t = self._normalize_dist(M_raw)

        # Optional sparsification: keep only strong support to prevent future diffusion
        tau = 1e-4  # keep entries >= tau * max
        mmax = float(M_t.max())
        if mmax > 0:
            mask = M_t >= (tau * mmax)
            if mask.sum() > 0:
                M_t = self._normalize_dist(M_t * mask)

        self.memory = M_t
        return M_t
            
    def current_estimate(self) -> tuple[int, tuple]:
        """Return (best_index, best_coord) from the current memory."""
        idx = int(np.argmax(self.memory))
        return idx, self.cells[idx]

    def step(self, x) -> tuple[tuple, np.ndarray, np.ndarray]:
        """
        One full RPNN step:
        1) compute emission G_t from features x
        2) apply transition to get M_pred
        3) update memory with G_t and M_pred
        4) return (predicted_coord, M_t, G_t)
        """
        G_t = self.step_emission(x)
        M_pred = self._transition_predict()
        M_t = self._memory_update(M_pred, G_t)
        _, coord = self.current_estimate()
        return coord, M_t, G_t

    def _vector_from_dict(self, sample: dict) -> np.ndarray:
        """
        Convert a feature dict into a 1D vector in the exact order of self.feature_keys.
        Raises a clear error if a required key is missing.
        """
        try:
            vec = np.array([sample[k] for k in self.feature_keys], dtype=float)
        except KeyError as e:
            raise ValueError(f"Missing required feature: {e.args[0]} (expected keys: {self.feature_keys})")
        if vec.shape != (self.n,):
            raise ValueError(f"Expected input shape ({self.n},), got {vec.shape}")
        return vec
    
    def predict_coord(self, x: dict | np.ndarray) -> tuple:
        """
        Predict a single step from either a feature dict or a ready-made vector.
        Returns the predicted coordinate (coarse cell) for the current step.
        """
        x_vec = self._vector_from_dict(x) if isinstance(x, dict) else self._input_layer(x)
        coord, _, _ = self.step(x_vec)
        return coord

    def debug_transition_info(self, start_p):
        start_idx = self._find_closest_coarse_index(start_p)
        print("start:", self.cells[start_idx])
        print("neighbors:", [self.cells[i] for i in self.neighbors[start_idx]])

    def test(self, X: list):
        prev_idx = None
        prev_coord = None
        for t, x in enumerate(X, 1):
            coord, M_t, G_t = self.step(self._vector_from_dict(x))
            idx = int(np.argmax(self.memory))
            if prev_coord is not None:
                jump = np.linalg.norm(np.array(coord) - np.array(prev_coord))
                print(f"[t={t:02d}] pred={coord}  jump={jump:.1f}")
                if jump > 400 + 1e-6:
                    print("prev neighbors:", [self.cells[i] for i in self.neighbors[prev_idx]])
            else:
                print(f"[t={t:02d}] pred={coord}")
            prev_coord = coord
            prev_idx = idx
      
    def debug_step(self, x, topk: int = 5):
        x_vec = self._vector_from_dict(x) if isinstance(x, dict) else self._input_layer(x)
        G = self.step_emission(x_vec)
        print(f"sigma={self.sigma:.6f}, G[min,max]=({float(G.min()):.3e}, {float(G.max()):.3e}), sum(G)={float(G.sum()):.3e}")
        top_idx = np.argsort(G)[-topk:][::-1]
        print("top emission cells:", [self.cells[i] for i in top_idx])
        print("top emission vals :", [float(G[i]) for i in top_idx])