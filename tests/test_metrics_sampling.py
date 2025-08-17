import time
import numpy as np
from scipy.stats import entropy
from jsonAI.main import Jsonformer
from jsonAI.model_backends import ModelBackend

def kl_divergence(p, q):
    epsilon = 1e-10
    p = np.array(p) + epsilon
    q = np.array(q) + epsilon
    return entropy(p, q)

class DummyBackend(ModelBackend):
    def generate(self, *args, **kwargs):
        return ""

def run_number_experiment(n_samples=10000, low=0, high=20):
    true_dist = np.ones(high - low + 1) / (high - low + 1)
    schema = {"type": "number", "minimum": low, "maximum": high}
    def deterministic_sample(low, high):
        jf = Jsonformer(
            model_backend=DummyBackend(),
            json_schema=schema,
            prompt=f"Sample a number from the distribution [{low}-{high}]",
            fallback_order=["deterministic"],
            validate_output=False,
        )
        return jf.generate_data()
    start = time.time()
    samples = [deterministic_sample(low, high) for _ in range(n_samples)]
    elapsed = time.time() - start
    int_samples = [int(round(s)) for s in samples]
    hist, _ = np.histogram(int_samples, bins=np.arange(low, high + 2), density=True)
    kl = kl_divergence(true_dist, hist)
    return ("number", kl, elapsed)

def run_integer_experiment(n_samples=10000, low=0, high=20):
    true_dist = np.ones(high - low + 1) / (high - low + 1)
    schema = {"type": "integer", "minimum": low, "maximum": high}
    def deterministic_sample(low, high):
        jf = Jsonformer(
            model_backend=DummyBackend(),
            json_schema=schema,
            prompt=f"Sample an integer from the distribution [{low}-{high}]",
            fallback_order=["deterministic"],
            validate_output=False,
        )
        return jf.generate_data()
    start = time.time()
    samples = [deterministic_sample(low, high) for _ in range(n_samples)]
    hist, _ = np.histogram(samples, bins=np.arange(low, high + 2), density=True)
    elapsed = time.time() - start
    kl = kl_divergence(true_dist, hist)
    return ("integer", kl, elapsed)

def run_boolean_experiment(n_samples=10000):
    true_dist = np.array([0.5, 0.5])
    schema = {"type": "boolean"}
    def deterministic_sample():
        jf = Jsonformer(
            model_backend=DummyBackend(),
            json_schema=schema,
            prompt="Sample a boolean value",
            fallback_order=["deterministic"],
            validate_output=False,
        )
        return jf.generate_data()
    start = time.time()
    samples = [deterministic_sample() for _ in range(n_samples)]
    elapsed = time.time() - start
    hist = np.array([samples.count(False), samples.count(True)]) / n_samples
    kl = kl_divergence(true_dist, hist)
    return ("boolean", kl, elapsed)

def run_enum_experiment(n_samples=10000):
    enum_values = ["red", "green", "blue"]
    true_dist = np.ones(len(enum_values)) / len(enum_values)
    schema = {"type": "string", "enum": enum_values}
    def deterministic_sample():
        jf = Jsonformer(
            model_backend=DummyBackend(),
            json_schema=schema,
            prompt="Sample a color",
            fallback_order=["deterministic"],
            validate_output=False,
        )
        return jf.generate_data()
    start = time.time()
    samples = [deterministic_sample() for _ in range(n_samples)]
    elapsed = time.time() - start
    hist = np.array([samples.count(v) for v in enum_values]) / n_samples
    kl = kl_divergence(true_dist, hist)
    return ("enum", kl, elapsed)

def test_sampling_metrics():
    results = []
    results.append(run_number_experiment())
    results.append(run_integer_experiment())
    results.append(run_boolean_experiment())
    results.append(run_enum_experiment())
    print("type\tKL_div_loss\ttime")
    for typ, kl, t in results:
        print(f"{typ}\t{kl:.6f}\t{t:.4f}")
    for _, kl, _ in results:
        assert kl < 0.5, "KL divergence too high, sampling is not uniform enough"

if __name__ == "__main__":
    test_sampling_metrics()
