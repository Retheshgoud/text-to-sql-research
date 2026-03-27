"""
Generates all charts for the research paper.
Saves plots to results/
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # no display needed, saves to file

from utils import load_results, compute_metrics


def plot_execution_accuracy(metrics):
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ["#d9534f", "#5cb85c"]
    bars = ax.bar(metrics["method"], metrics["execution_accuracy_pct"], color=colors, width=0.4)
    for bar, val in zip(bars, metrics["execution_accuracy_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{val}%", ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Execution Accuracy (%)")
    ax.set_title("Execution Accuracy: Baseline vs Improved")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Baseline\n(No Schema)", "Improved\n(Schema-Aware)"])
    plt.tight_layout()
    plt.savefig("results/chart_accuracy.png", dpi=150)
    plt.close()
    print("Saved: results/chart_accuracy.png")


def plot_latency_comparison(metrics):
    fig, ax = plt.subplots(figsize=(6, 4))
    x = range(len(metrics))
    width = 0.25
    ax.bar([i - width for i in x], metrics["avg_latency"], width=width, label="Avg", color="#5bc0de")
    ax.bar(x, metrics["median_latency"], width=width, label="Median", color="#428bca")
    ax.bar([i + width for i in x], metrics["p95_latency"], width=width, label="P95", color="#2d6a9f")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["Baseline\n(No Schema)", "Improved\n(Schema-Aware)", "Improved\n(+Retry)"])
    ax.set_ylabel("Latency (seconds)")
    ax.set_title("Latency Comparison: Baseline vs Improved vs Improved+Retry")
    ax.legend()
    plt.tight_layout()
    plt.savefig("results/chart_latency.png", dpi=150)
    plt.close()
    print("Saved: results/chart_latency.png")


def plot_success_per_query(df):
    pivot = df.pivot(index="question", columns="method", values="success")
    pivot = pivot.sort_values("improved", ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(pivot))
    ax.bar(x, pivot.get("baseline", 0).fillna(0).astype(int),
           label="Baseline", color="#d9534f", alpha=0.7)
    ax.bar(x, pivot.get("improved", 0).fillna(0).astype(int),
           label="Improved", color="#5cb85c", alpha=0.7, bottom=0)
    ax.set_ylabel("Success (1 = Pass, 0 = Fail)")
    ax.set_title("Per-Query Success: Baseline vs Improved")
    ax.set_xticks([])
    ax.set_xlabel(f"50 Queries (sorted by improved success)")
    ax.legend()
    plt.tight_layout()
    plt.savefig("results/chart_per_query.png", dpi=150)
    plt.close()
    print("Saved: results/chart_per_query.png")


def plot_error_analysis(df):
    failed = df[df["success"] == False].copy()
    if failed.empty:
        print("No failures to analyze.")
        return

    def categorize(err):
        if pd.isna(err):
            return "Unknown"
        err = str(err)
        if "no such table" in err:
            return "Wrong Table Name"
        if "no such column" in err:
            return "Wrong Column Name"
        if "no such function" in err:
            return "Wrong Function"
        if "syntax error" in err.lower():
            return "Syntax Error"
        return "Other"

    failed["error_type"] = failed["error"].apply(categorize)
    counts = failed.groupby(["method", "error_type"]).size().unstack(fill_value=0)

    counts.T.plot(kind="bar", figsize=(8, 4), color=["#d9534f", "#5cb85c"])
    plt.title("Error Type Breakdown by Method")
    plt.ylabel("Count")
    plt.xlabel("Error Type")
    plt.xticks(rotation=30, ha="right")
    plt.legend(title="Method")
    plt.tight_layout()
    plt.savefig("results/chart_errors.png", dpi=150)
    plt.close()
    print("Saved: results/chart_errors.png")


if __name__ == "__main__":
    df = load_results()
    metrics = compute_metrics(df)

    plot_execution_accuracy(metrics)
    plot_latency_comparison(metrics)
    plot_success_per_query(df)
    plot_error_analysis(df)

    print("\nAll charts saved to results/")
