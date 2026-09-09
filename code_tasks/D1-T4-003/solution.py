# -*- coding: utf-8 -*-
"""
D1-T4-003 solution: the matching stage of a template attack.

Log-likelihood: log P(t | template_k) ∝ -0.5 * [ (t - μ_k)^T Σ_k^{-1} (t - μ_k) + log det Σ_k ]

Points for numerical stability:
- Tikhonov regularization Sigma_k <- Sigma_k + lambda*I to avoid singularity
- np.linalg.slogdet rather than log(det(...))
- np.linalg.solve (LU- or Cholesky-based) rather than multiplying by inv
"""
from typing import Dict, Tuple
import numpy as np


def template_attack_match(
    test_trace: np.ndarray,
    templates: Dict[int, Tuple[np.ndarray, np.ndarray]],
) -> np.ndarray:
    """
    Return the (256,) log-likelihood array.
    """
    test_trace = np.asarray(test_trace, dtype=np.float64).ravel()
    D = test_trace.shape[0]

    log_lik = np.full(256, -np.inf, dtype=np.float64)

    for k, (mean_k, cov_k) in templates.items():
        if not (0 <= k < 256):
            continue
        mean_k = np.asarray(mean_k, dtype=np.float64).ravel()
        cov_k = np.asarray(cov_k, dtype=np.float64)
        if mean_k.shape[0] != D or cov_k.shape != (D, D):
            log_lik[k] = -1e18
            continue

        # Tikhonov regularization
        trace_sigma = np.trace(cov_k)
        lam = 1e-6 * max(trace_sigma, 1.0)
        cov_reg = cov_k + lam * np.eye(D)

        # log det via slogdet (numerically stable)
        sign, logdet = np.linalg.slogdet(cov_reg)
        if sign <= 0:
            # Extreme case: still singular. Increase the regularization
            cov_reg = cov_k + (lam * 100) * np.eye(D)
            sign, logdet = np.linalg.slogdet(cov_reg)
            if sign <= 0:
                log_lik[k] = -1e18
                continue

        diff = test_trace - mean_k
        # Use solve for the quadratic form, not inv
        try:
            sol = np.linalg.solve(cov_reg, diff)
        except np.linalg.LinAlgError:
            log_lik[k] = -1e18
            continue
        quad = float(diff @ sol)

        # log P drops the constant -0.5 * D * log(2*pi) (it does not affect the argmax)
        log_lik[k] = -0.5 * (quad + logdet)

    return log_lik
