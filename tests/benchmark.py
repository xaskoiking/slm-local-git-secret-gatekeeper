import json
import os
import sys
import time
import random
from tqdm import tqdm

# Ensure we can import from src
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'src'))

try:
    from hooks.main import fast_scan, slm_validation
except ImportError:
    print(f"Error: Could not import scanner modules from {os.path.join(BASE_DIR, 'src')}")
    sys.exit(1)

def calc_metrics(tp, fp, total_p):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / total_p if total_p > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return precision, recall, f1

def run_benchmark(dataset_path=None, use_real_slm=True, limit=100):
    if dataset_path is None:
        dataset_path = os.path.join(BASE_DIR, "data", "synthetic", "mock_dataset.json")
    
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset {dataset_path} not found. Run generate_mock_data.py first.")
        return

    with open(dataset_path, "r") as f:
        dataset = json.load(f)
    
    if limit:
        dataset = random.sample(dataset, min(limit, len(dataset)))

    print("="*60)
    print(f"BENCHMARKING: Regex-only Baseline vs. Gatekeeper Hybrid (N={len(dataset)})")
    print(f"Using Real SLM: {use_real_slm}")
    print("="*60)

    # Regex-only Baseline
    regex_tp = 0
    regex_fp = 0
    
    # Gatekeeper Hybrid (Regex + SLM)
    hybrid_tp = 0
    hybrid_fp = 0
    
    total_leaks = sum(1 for d in dataset if d['label'] == 'LEAK')
    total_safe = len(dataset) - total_leaks

    # 2. Hybrid Approach (Stage 2 & 3)
    # Initialize validator once for the entire benchmark
    validator = None
    if use_real_slm:
        print("INFO: Initializing persistent Gatekeeper SLM...")
        from models.inference import SLMValidator
        validator = SLMValidator()

    start_time = time.time()

    for i, entry in enumerate(tqdm(dataset, desc="Validating Samples")):
        snippet = entry['snippet']
        actual_label = entry['label']
        
        # 1. Regex Baseline (Stage 1)
        candidates = fast_scan(snippet)
        
        is_baseline_threat = len(candidates) > 0
        if actual_label == "LEAK":
            if is_baseline_threat: regex_tp += 1
        else:
            if is_baseline_threat: regex_fp += 1

        # 2. Hybrid Approach (PIVOT: Regex OR SLM Safety Net)
        is_hybrid_threat = False
        if is_baseline_threat:
            # If Regex caught it, we RETAIN it to ensure max Recall
            is_hybrid_threat = True
        else:
            # If Regex missed it, run SLM as a safety net
            if use_real_slm and validator:
                # Deep scan the whole snippet
                is_hybrid_threat = validator.scan_for_secrets(snippet)
            elif not use_real_slm:
                # Simulated Safety Net (Higher recall mock logic)
                if actual_label == "LEAK":
                    is_hybrid_threat = random.random() < 0.30 # SLM catches some missed ones
                else:
                    is_hybrid_threat = random.random() < 0.05 # Some FPs from deep scan
        
        if actual_label == "LEAK":
            if is_hybrid_threat: hybrid_tp += 1
        else:
            if is_hybrid_threat: hybrid_fp += 1

        # Intermediate reporting every 5 samples
        if (i + 1) % 5 == 0:
            temp_count = i + 1
            print(f"\n--- INTERMEDIATE RESULTS ({temp_count}/{len(dataset)}) ---")
            # Recalculate total_leaks for the processed subset
            current_total_leaks = sum(1 for d in dataset[:temp_count] if d['label'] == 'LEAK')
            g_p, g_r, g_f = calc_metrics(regex_tp, regex_fp, current_total_leaks)
            h_p, h_r, h_f = calc_metrics(hybrid_tp, hybrid_fp, current_total_leaks)
            print(f"Regex: Prec={g_p:.2f}, Rec={g_r:.2f}, F1={g_f:.2f}")
            print(f"Hybrid: Prec={h_p:.2f}, Rec={h_r:.2f}, F1={h_f:.2f}")
            print("-" * 40)

    end_time = time.time()
    avg_latency = ((end_time - start_time) / len(dataset)) * 1000 # ms

    g_prec, g_rec, g_f1 = calc_metrics(regex_tp, regex_fp, total_leaks)
    h_prec, h_rec, h_f1 = calc_metrics(hybrid_tp, hybrid_fp, total_leaks)

    print("\n" + "="*60)
    print(f"{'Tool':<20} | {'Prec.':<6} | {'Rec.':<6} | {'F1':<6}")
    print("-" * 60)
    print(f"{'Regex-only (Baseline)':<20} | {g_prec:<6.2f} | {g_rec:<6.2f} | {g_f1:<6.2f}")
    print(f"{'Gatekeeper (Hybrid)':<20} | {h_prec:<6.2f} | {h_rec:<6.2f} | {h_f1:<6.2f}")
    print("-" * 60)
    print(f"Total Samples: {len(dataset)}")
    print(f"Avg. Latency: {avg_latency:.2f}ms per snippet")
    print("="*60)

    results = {
        "regex": {"precision": g_prec, "recall": g_rec, "f1": g_f1, "tp": regex_tp, "fp": regex_fp},
        "hybrid": {"precision": h_prec, "recall": h_rec, "f1": h_f1, "tp": hybrid_tp, "fp": hybrid_fp},
        "latency_ms_per_snippet": avg_latency,
        "total_samples": len(dataset),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Ensure benchmarks dir exists in parent repo
    bench_dir = os.path.join(BASE_DIR, "benchmarks")
    os.makedirs(bench_dir, exist_ok=True)
    with open(os.path.join(bench_dir, "benchmark_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSUCCESS: Results saved to benchmarks/benchmark_results.json")

    return results

if __name__ == "__main__":
    # Run with real SLM on 100 samples for final results
    run_benchmark(use_real_slm=True, limit=500)
