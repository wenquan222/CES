import numpy as np

def compute_nicv(traces, intermediate_values, num_bins=100):
    N, T = traces.shape
    unique_vals = np.unique(intermediate_values)
    K = len(unique_vals)
    val_to_idx = {v: i for i, v in enumerate(unique_vals)}
    class_idx = np.array([val_to_idx[v] for v in intermediate_values])

    global_mean = traces.mean(axis=0)
    var_total = traces.var(axis=0, ddof=0)

    class_means = np.zeros((K, T))
    class_counts = np.zeros(K)
    for k in range(K):
        mask = class_idx == k
        class_counts[k] = mask.sum()
        if class_counts[k] > 0:
            class_means[k] = traces[mask].mean(axis=0)

    prob_class = class_counts / N
    var_between = np.zeros(T)
    for k in range(K):
        var_between += prob_class[k] * (class_means[k] - global_mean) ** 2

    nicv = np.divide(var_between, var_total, out=np.zeros_like(var_between), where=var_total > 1e-12)
    nicv = np.clip(nicv, 0.0, 1.0)
    return nicv
