"""
Diagnostic Question Selection and Calibration Evaluation Service.
Part of KT-RL Phase 8: Advanced Policy Audit & RL Improvement Plan.

Implements:
1. Uncertainty-Aware Diagnostic Item Selection:
   - Evaluates expected information gain (entropy reduction) across all required KCs.
   - Inverse-observation weighting to resolve unassessed and high-uncertainty skills.
2. Probabilistic Calibration Evaluation:
   - Expected Calibration Error (ECE) across M reliability bins.
   - Brier Score BS = 1/N * sum((p_hat_i - y_i)^2).
   - Maximum Calibration Error (MCE).
   - Reliability diagram bin statistics.
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from resources import get_all_questions
from services.bkt_service import bkt_step, BKTParameters, DEFAULT_PARAMS


def compute_expected_information_gain(
    p_prior: float,
    bkt_params: BKTParameters = DEFAULT_PARAMS,
) -> float:
    """
    Computes expected entropy reduction E[Delta H] for a given KC prior:
      P(Correct) = P(G) + (1 - P(G) - P(S)) * P(L)
      E[H_post] = P(Correct) * H(P(L | Correct)) + (1 - P(Correct)) * H(P(L | Incorrect))
      E[Delta H] = H(P(L_prior)) - E[H_post]
    """
    p_prior = max(0.001, min(0.999, p_prior))
    h_prior = -(p_prior * math.log2(p_prior) + (1.0 - p_prior) * math.log2(1.0 - p_prior))

    # Predicted probability of correct response
    p_correct = bkt_params.p_g + (1.0 - bkt_params.p_g - bkt_params.p_s) * p_prior

    # Posterior masteries under both outcomes
    _, p_post_corr = bkt_step(p_prior, is_correct=True, params=bkt_params)
    _, p_post_inc = bkt_step(p_prior, is_correct=False, params=bkt_params)

    p_post_corr = max(0.001, min(0.999, p_post_corr))
    p_post_inc = max(0.001, min(0.999, p_post_inc))

    h_post_corr = -(p_post_corr * math.log2(p_post_corr) + (1.0 - p_post_corr) * math.log2(1.0 - p_post_corr))
    h_post_inc = -(p_post_inc * math.log2(p_post_inc) + (1.0 - p_post_inc) * math.log2(1.0 - p_post_inc))

    expected_h_post = p_correct * h_post_corr + (1.0 - p_correct) * h_post_inc
    expected_gain = max(0.0, h_prior - expected_h_post)
    return float(expected_gain)


def select_diagnostic_question(
    eligible_item_indices: List[int],
    item_bank: List[Dict[str, Any]],
    bkt_states: Dict[str, Any],
    bkt_params: BKTParameters = DEFAULT_PARAMS,
) -> int:
    """
    Selects the item that maximizes total expected information gain across its KCs,
    prioritizing skills with fewest observations and high posterior entropy.
    """
    if not eligible_item_indices:
        return 0

    best_idx = eligible_item_indices[0]
    best_score = -1.0

    for idx in eligible_item_indices:
        item = item_bank[idx]
        kcs = item.get("knowledge_components") or [item.get("topic", "")]
        item_gain = 0.0

        for kc in kcs:
            kc_clean = str(kc).strip().lower()
            state = bkt_states.get(kc_clean)
            p_prior = getattr(state, "mastery_probability", 0.20) if state else 0.20
            obs_count = getattr(state, "observation_count", 0) if state else 0

            # Base expected information gain
            eig = compute_expected_information_gain(p_prior, bkt_params=bkt_params)
            # Weighting bonus for low evidence / unassessed KCs
            evidence_weight = 1.0 / (math.sqrt(obs_count) + 1.0)
            item_gain += eig * evidence_weight

        if item_gain > best_score:
            best_score = item_gain
            best_idx = idx

    return best_idx


def evaluate_bkt_calibration(
    predicted_probabilities: List[float],
    binary_outcomes: List[int],
    num_bins: int = 10,
) -> Dict[str, Any]:
    """
    Computes rigorous probabilistic calibration metrics for BKT response predictions:
    1. Expected Calibration Error (ECE): ECE = sum_m (|B_m| / N) * |acc(B_m) - conf(B_m)|
    2. Maximum Calibration Error (MCE): max_m |acc(B_m) - conf(B_m)|
    3. Brier Score: 1/N * sum((p_i - y_i)^2)
    4. Reliability Diagram Bins: List of bin statistics.
    """
    if len(predicted_probabilities) != len(binary_outcomes):
        raise ValueError("Length of predictions and binary outcomes must match.")

    n = len(predicted_probabilities)
    if n == 0:
        return {
            "total_samples": 0,
            "ece": 0.0,
            "mce": 0.0,
            "brier_score": 0.0,
            "bins": [],
        }

    preds = np.clip(np.array(predicted_probabilities, dtype=float), 0.0, 1.0)
    labels = np.array(binary_outcomes, dtype=int)

    # 1. Brier score
    brier_score = float(np.mean((preds - labels) ** 2))

    # 2. Binning for ECE and MCE
    bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
    ece = 0.0
    mce = 0.0
    bin_stats = []

    for i in range(num_bins):
        low, high = bin_boundaries[i], bin_boundaries[i + 1]
        if i == num_bins - 1:
            in_bin = (preds >= low) & (preds <= high)
        else:
            in_bin = (preds >= low) & (preds < high)

        bin_count = int(np.sum(in_bin))
        if bin_count > 0:
            bin_conf = float(np.mean(preds[in_bin]))
            bin_acc = float(np.mean(labels[in_bin]))
            gap = abs(bin_acc - bin_conf)
            ece += (bin_count / n) * gap
            mce = max(mce, gap)
            bin_stats.append({
                "bin_index": i + 1,
                "range": [round(low, 2), round(high, 2)],
                "count": bin_count,
                "confidence": round(bin_conf, 4),
                "accuracy": round(bin_acc, 4),
                "calibration_gap": round(gap, 4),
            })
        else:
            bin_stats.append({
                "bin_index": i + 1,
                "range": [round(low, 2), round(high, 2)],
                "count": 0,
                "confidence": round((low + high) / 2.0, 2),
                "accuracy": 0.0,
                "calibration_gap": 0.0,
            })

    return {
        "total_samples": n,
        "ece": round(float(ece), 4),
        "mce": round(float(mce), 4),
        "brier_score": round(float(brier_score), 4),
        "bins": bin_stats,
    }
