# ---------------------- wknn_positioning.py ----------------------
import pandas as pd
import numpy as np

# -----------------------------------------------------------------
# 0. CONFIG – change here if you use different filenames / columns
FINGERPRINT_CSV = "Postioning/Waston_floor3.csv"   # training fingerprints
TEST_CSV        = "Postioning/WastonFloor3Test.csv"     # test scans (one row = one scan)
LABEL_COL       = "Vertex"                        # the column holding your location label
TOP_GUESSES     = 3                              # how many guesses to output per test row (set 5, etc.)

# --- Connection-aware scoring (toggle & knobs) ---
USE_CONNECTION_HINT   = True      # set False to revert to pure RSSI distance
CONNECTION_AP_TOPN    = 0         # infer "connected" as Top-N strongest APs per row
STRONG_RSSI_THRESHOLD = -80      # or set to a dBm (e.g., -70.0) to use a threshold instead of TopN
CONNECTION_BETA       = 15       # weight of (1 - similarity) term added to distance (higher => more influence)

# --- Distance hygiene (keeps -100 sentinel but safer distances) ---
USE_MASKED_DISTANCE = True
MISSING       = -100.0            # sentinel for "not seen"
MISS_PENALTY  = 15.0              # cost if seen in one vector but not the other
DIFF_CAP      = 60.0              # cap per-AP difference

# --- Weighted kNN label voting ---
USE_WKNN      = True     # turn on weighted voting by label
WKNN_K        = 40     # None => auto from data; or set e.g. 30 or 40
WKNN_P        = 2.0      # weight exponent: w = 1 / (eps + score)**p
WKNN_EPS      = 1e-6     # numerical stability for very small scores
PER_LABEL_CAP = None     # optional: cap neighbors per label within top-K (e.g., 5); None = no cap
# -----------------------------------------------------------------


def load_data(fp_file: str, test_file: str, label_col: str):
    """
    Load fingerprint (training) and test CSVs and align columns so that
    both use the fingerprint schema (AP list) in the same order.
    """
    fp   = pd.read_csv(fp_file)
    test = pd.read_csv(test_file)

    ap_cols = [c for c in fp.columns if c != label_col]

    # Ensure test has all AP columns (fill missing with -100)
    for c in ap_cols:
        if c not in test.columns:
            test[c] = MISSING

    # Keep only label + AP columns in the same order as fingerprint
    test = test[[label_col] + ap_cols]
    return fp, test, ap_cols


# ------------------------ Distance -------------------------------

def masked_distance(scan_vec, fp_vec):
    """
    Robust distance using the -100 sentinel:
      - both MISSING -> ignored
      - one MISSING  -> MISS_PENALTY
      - both present -> |diff| (clipped), L2 over features, normalized.
    """
    # clip real RSSI but leave sentinel untouched
    scan = np.where(scan_vec == MISSING, MISSING, np.clip(scan_vec, -95.0, -30.0))
    fp   = np.where(fp_vec   == MISSING, MISSING, np.clip(fp_vec,   -95.0, -30.0))

    both_missing = (scan == MISSING) & (fp == MISSING)
    one_missing  = ((scan == MISSING) ^ (fp == MISSING))
    both_present = ~both_missing & ~one_missing

    diff = np.zeros_like(scan, dtype=float)
    diff[one_missing]  = MISS_PENALTY
    diff[both_present] = np.abs(scan[both_present] - fp[both_present])
    diff = np.minimum(diff, DIFF_CAP)

    contrib = (~both_missing).astype(float)
    k = np.count_nonzero(contrib)
    if k == 0:
        return 1e6

    # L2 normalized by sqrt(#contrib) to keep scale consistent across rows
    return float(np.linalg.norm(diff) / np.sqrt(k))


def plain_distance(scan_vec, fp_vec):
    """Standard Euclidean distance, treating -100 like any other value."""
    return float(np.linalg.norm(fp_vec - scan_vec))


# ------------------ Connection / Strong-AP overlap ----------------

def strong_ap_set(rssi_row_values, ap_cols, topn=2, thr=None):
    """
    Return a set of AP (BSSID) names considered 'strong' for this row.
    - If `thr` is provided, include all APs with RSSI >= thr (and != MISSING).
    - Else, take the Top-N strongest APs that are != MISSING.
    """
    vals = np.array(rssi_row_values, dtype=float)
    seen_mask = vals != MISSING
    if not np.any(seen_mask):
        return set()

    if thr is not None:
        keep = (vals >= thr) & seen_mask
        return set(np.array(ap_cols)[keep])
    
    if topn == 0:
        return set(np.array(ap_cols)[seen_mask])

    # Top-N by RSSI (higher is stronger; remember RSSI is negative)
    idx = np.argsort(vals[seen_mask])  # ascending; but RSSI higher is less negative => need descending
    sorted_seen_vals = vals[seen_mask][idx]
    sorted_seen_cols = np.array(ap_cols)[seen_mask][idx]

    # Take last 'topn' (strongest)
    strongest = list(sorted_seen_cols[-topn:]) if topn > 0 else []
    return set(strongest)


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


# ---------------------- Scoring & Ranking ------------------------

def connection_aware_score(scan_vec, fp_vec, scan_ap_cols, fp_ap_cols,
                           use_masked=True,
                           conn_topn=2, conn_thr=None, beta=8.0):
    """
    score = distance + beta * (1 - similarity)
    where similarity = Jaccard(strong_APs(scan), strong_APs(fp))
    """
    # Distance part
    dist = masked_distance(scan_vec, fp_vec) if use_masked else plain_distance(scan_vec, fp_vec)

    # Overlap part
    scan_strong = strong_ap_set(scan_vec, scan_ap_cols, topn=conn_topn, thr=conn_thr)
    fp_strong   = strong_ap_set(fp_vec,   fp_ap_cols,   topn=conn_topn, thr=conn_thr)
    sim = jaccard(scan_strong, fp_strong)

    return dist + beta * (1.0 - sim)

def _label_vote_scores(scan_vec, fp_df, ap_cols, k, p, eps, per_label_cap=None):
    # Distances to every fingerprint row
    fp_vals = fp_df[ap_cols].astype(float).values
    scores  = np.array([
        connection_aware_score(
            scan_vec, fp_vals[i], ap_cols, ap_cols,
            use_masked=USE_MASKED_DISTANCE,
            conn_topn=CONNECTION_AP_TOPN if STRONG_RSSI_THRESHOLD is None else 0,
            conn_thr=STRONG_RSSI_THRESHOLD,
            beta=(CONNECTION_BETA if USE_CONNECTION_HINT else 0.0)
        )
        for i in range(fp_vals.shape[0])
    ])

    order = np.argsort(scores)[:k]        # take Top-K neighbors overall
    labs  = fp_df.iloc[order][LABEL_COL].values
    sc    = scores[order]

    # Optional: cap how many neighbors any single label can contribute (helps imbalance)
    if per_label_cap is not None and per_label_cap > 0:
        keep_idx = []
        seen_counts = {}
        for idx in order:
            lab = fp_df.iloc[idx][LABEL_COL]
            c = seen_counts.get(lab, 0)
            if c < per_label_cap:
                keep_idx.append(idx)
                seen_counts[lab] = c + 1
        sc   = scores[keep_idx]
        labs = fp_df.iloc[keep_idx][LABEL_COL].values

    # Convert distances to weights (closer → larger)
    w = 1.0 / np.power(eps + sc, p)

    # Sum weights per label
    votes = {}
    for lab, wt in zip(labs, w):
        votes[lab] = votes.get(lab, 0.0) + wt
    return votes

def top_unique_label_guesses(scan_row, fp_df, ap_cols, top_n=3):
    scan_vec = scan_row[ap_cols].astype(float).values

    if USE_WKNN:
        votes = _label_vote_scores(
            scan_vec, fp_df, ap_cols,
            k=WKNN_K, p=WKNN_P, eps=WKNN_EPS,
            per_label_cap=PER_LABEL_CAP
        )
        ranked = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        guesses = [lab for lab, _ in ranked[:top_n]]
    else:
        # Fallback: your original "first unique labels by score"
        fp_vecs = fp_df[ap_cols].astype(float).values
        scores = np.array([
            connection_aware_score(
                scan_vec, fp_vecs[i], ap_cols, ap_cols,
                use_masked=USE_MASKED_DISTANCE,
                conn_topn=CONNECTION_AP_TOPN if STRONG_RSSI_THRESHOLD is None else 0,
                conn_thr=STRONG_RSSI_THRESHOLD,
                beta=(CONNECTION_BETA if USE_CONNECTION_HINT else 0.0)
            )
            for i in range(fp_vecs.shape[0])
        ])
        order = np.argsort(scores)
        guesses, seen = [], set()
        for i in order:
            lab = fp_df.iloc[i][LABEL_COL]
            if lab not in seen:
                guesses.append(lab); seen.add(lab)
                if len(guesses) == top_n: break

    while len(guesses) < top_n:
        guesses.append("")
    return guesses



def build_guesses_table(test_df, fp_df, ap_cols, top_n=3):
    """
    For every row in test_df, produce:
    Vertex, Guess 1, Guess 2, ..., Guess N
    """
    rows = []
    for _, row in test_df.iterrows():
        guesses = top_unique_label_guesses(row, fp_df, ap_cols, top_n=top_n)
        record = {LABEL_COL: row[LABEL_COL]}
        for j, g in enumerate(guesses, start=1):
            record[f"Guess {j}"] = g
        rows.append(record)
    return pd.DataFrame(rows)

def _auto_k(fp_df):
    # Use 3× the (median) scans per vertex, clipped to [15, 60]
    counts = fp_df[LABEL_COL].value_counts()
    if counts.empty:
        return 30
    scans_per_label = int(counts.median())
    return int(np.clip(3 * max(scans_per_label, 1), 15, 60))

# --------------------------- MAIN --------------------------------
if __name__ == "__main__":
    fp, test, ap_cols = load_data(FINGERPRINT_CSV, TEST_CSV, LABEL_COL)

    AUTO_WKNN_K = _auto_k(fp)
    if WKNN_K is None:
        WKNN_K = AUTO_WKNN_K
    print(f"[wKNN] Using K={WKNN_K} (auto)" if USE_WKNN else "[wKNN] Disabled")

    # Build top-N unique guesses per test row (connection-aware if enabled)
    guesses_df = build_guesses_table(test, fp, ap_cols, top_n=TOP_GUESSES)

    out_path = "nearest_neighbors.csv"
    guesses_df.to_csv(out_path, index=False)
    print(f"\nSaved top-{TOP_GUESSES} guesses per test row to {out_path}\n")
    print(guesses_df.head())
# -----------------------------------------------------------------
