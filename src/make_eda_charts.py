r"""Recreate the churn-rate bar charts (02 to 10) with a clean layout.
Run from the project folder:   python src/make_eda_charts.py
Overwrites reports/figures/02_... to 10_... with the fixed versions.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from preprocess import ROOT, load_data

FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
df = load_data(ROOT / "data" / "churn_clean.csv")

df["AgeBand"] = pd.cut(df["Age"], [17, 30, 40, 50, 60, 100], labels=["18-30", "31-40", "41-50", "51-60", "60+"])
df["CreditBand"] = pd.cut(df["CreditScore"], [0, 500, 600, 700, 800, 900],
                          labels=["<500", "500-600", "600-700", "700-800", "800+"])
df["ZeroBalance"] = (df["Balance"] == 0).map({True: "Zero balance", False: "Has balance"})


def churn_bar(col, n, labels=None):
    rate = df.groupby(col, observed=True)["Exited"].mean().mul(100).round(1)
    fig, ax = plt.subplots(figsize=(max(6, 0.7 * len(rate) + 3), 4))
    ax.bar(range(len(rate)), rate.values, color="#4C78A8")
    ax.set_ylim(0, rate.max() * 1.18)
    for i, v in enumerate(rate):
        ax.text(i, v + rate.max() * 0.02, f"{v}%", ha="center")
    ax.set_xticks(range(len(rate)))
    ax.set_xticklabels(labels if labels else [str(x) for x in rate.index])
    ax.set_title(f"Churn rate by {col}", pad=12)
    ax.set_ylabel("Churn %")
    fig.tight_layout()
    fig.savefig(FIG / f"{n:02d}_churn_by_{col}.png", dpi=150)
    plt.close(fig)
    print(f"Saved {n:02d}_churn_by_{col}.png")


churn_bar("Geography", 2)
churn_bar("Gender", 3)
churn_bar("NumOfProducts", 4)
churn_bar("HasCrCard", 5, ["No card", "Has card"])
churn_bar("IsActiveMember", 6, ["Inactive", "Active"])
churn_bar("AgeBand", 7)
churn_bar("Tenure", 8)
churn_bar("CreditBand", 9)
churn_bar("ZeroBalance", 10)
