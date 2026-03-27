"""
Metrics and comparison utilities.
Computes execution accuracy, exact match, and latency stats
across baseline and improved results.
"""
import pandas as pd


def load_results():
    frames = []
    for path in ["results/results_baseline.csv", "results/results_improved.csv", "results/results_retry.csv"]:
        try:
            frames.append(pd.read_csv(path))
        except FileNotFoundError:
            pass
    return pd.concat(frames, ignore_index=True)


def compute_metrics(df):
    metrics = df.groupby("method").agg(
        total_queries=("question", "count"),
        successful=("success", "sum"),
        execution_accuracy=("success", "mean"),
        avg_latency=("latency", "mean"),
        median_latency=("latency", "median"),
        p95_latency=("latency", lambda x: x.quantile(0.95)),
    ).reset_index()

    metrics["execution_accuracy_pct"] = (metrics["execution_accuracy"] * 100).round(1)
    metrics["avg_latency"] = metrics["avg_latency"].round(2)
    metrics["median_latency"] = metrics["median_latency"].round(2)
    metrics["p95_latency"] = metrics["p95_latency"].round(2)

    # Exact match: generated SQL matches ground truth exactly (case-insensitive)
    df["exact_match"] = df["generated_sql"].str.strip().str.lower() == df["ground_truth_sql"].str.strip().str.lower()
    exact = df.groupby("method")["exact_match"].mean().reset_index()
    exact.columns = ["method", "exact_match_rate"]
    exact["exact_match_rate"] = (exact["exact_match_rate"] * 100).round(1)

    metrics = metrics.merge(exact, on="method")
    return metrics


def print_report(metrics):
    print("=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)
    for _, row in metrics.iterrows():
        print(f"\nMethod: {row['method'].upper()}")
        print(f"  Execution Accuracy : {row['execution_accuracy_pct']}%")
        print(f"  Exact Match Rate   : {row['exact_match_rate']}%")
        print(f"  Avg Latency        : {row['avg_latency']}s")
        print(f"  Median Latency     : {row['median_latency']}s")
        print(f"  P95 Latency        : {row['p95_latency']}s")
        print(f"  Queries Run        : {int(row['total_queries'])}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    df = load_results()
    metrics = compute_metrics(df)
    print_report(metrics)
    metrics.to_csv("results/metrics_summary.csv", index=False)
    print("Saved to results/metrics_summary.csv")
