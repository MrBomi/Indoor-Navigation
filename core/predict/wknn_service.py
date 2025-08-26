from __future__ import annotations
import time
import numpy as np
import pandas as pd

from core.predict.wknn_positioning import (
    LABEL_COL, MISSING,
    USE_WKNN, WKNN_K, WKNN_P, WKNN_EPS, PER_LABEL_CAP,
    USE_MASKED_DISTANCE, CONNECTION_AP_TOPN, STRONG_RSSI_THRESHOLD, CONNECTION_BETA,
    connection_aware_score, _label_vote_scores
)

from server.DataBaseManger.floorManager import download_floor_scan_table

_FPCACHE: dict[tuple[int,int], dict] = {}
_CACHE_TTL = 300  # seconds

def _get_fp_df(building_id: int, floor_id: int) -> pd.DataFrame:
    key = (int(building_id), int(floor_id))
    now = time.time()
    hit = _FPCACHE.get(key)
    if hit and (now - hit["ts"] < _CACHE_TTL):
        return hit["df"]

    df = download_floor_scan_table(int(building_id), int(floor_id))
    if df is None or df.empty:
        raise ValueError("Fingerprint table not found or empty for the requested floor.")
    if LABEL_COL not in df.columns:
        raise ValueError(f"Fingerprint table missing label column '{LABEL_COL}'.")

    df = df.copy()
    df[LABEL_COL] = df[LABEL_COL].astype(str)
    ap_cols = [c for c in df.columns if c != LABEL_COL]
    df[ap_cols] = df[ap_cols].astype(float)

    _FPCACHE[key] = {"df": df, "ts": now}
    return df

def _scan_to_vec(scan_dict: dict, ap_cols: list[str]) -> np.ndarray:
    """Align {bssid:rssi} to fingerprint schema; fill missing with MISSING (-100)."""
    vec = np.full(len(ap_cols), MISSING, dtype=float)
    if scan_dict:
        for i, ap in enumerate(ap_cols):
            if ap in scan_dict:
                try:
                    vec[i] = float(scan_dict[ap])
                except Exception:
                    vec[i] = MISSING
    return vec

def predict_top1(building_id: int, floor_id: int, scan_dict: dict) -> tuple[str, float]:
    """
    Returns (label, confidence). Confidence is the wKNN vote weight.
    """
    fp_df = _get_fp_df(building_id, floor_id)
    ap_cols = [c for c in fp_df.columns if c != LABEL_COL]
    scan_vec = _scan_to_vec(scan_dict, ap_cols)

    if USE_WKNN:
        votes = _label_vote_scores(
            scan_vec, fp_df, ap_cols,
            k=WKNN_K, p=WKNN_P, eps=WKNN_EPS, per_label_cap=PER_LABEL_CAP
        )
        if votes:
            lab, w = sorted(votes.items(), key=lambda x: x[1], reverse=True)[0]
            return str(lab), float(w)

    # fallback: nearest neighbor by score
    fp_vals = fp_df[ap_cols].values
    scores = np.array([
        connection_aware_score(
            scan_vec, fp_vals[i], ap_cols, ap_cols,
            use_masked=USE_MASKED_DISTANCE,
            conn_topn=CONNECTION_AP_TOPN if STRONG_RSSI_THRESHOLD is None else 0,
            conn_thr=STRONG_RSSI_THRESHOLD,
            beta=CONNECTION_BETA
        )
        for i in range(fp_vals.shape[0])
    ])
    i = int(np.argmin(scores))
    return str(fp_df.iloc[i][LABEL_COL]), 0.0
