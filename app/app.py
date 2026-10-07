"""Bank churn dashboard, version 2 (with What-If Simulator).
Run from the project folder:  streamlit run app/app.py
"""
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import preprocess  # noqa: F401  (needed so the saved pipeline can be loaded)

st.set_page_config(page_title="Bank Churn Intelligence", page_icon="🏦", layout="wide")

FEATURES = ["CreditScore", "Geography", "Gender", "Age", "Tenure", "Balance",
            "NumOfProducts", "HasCrCard", "IsActiveMember", "EstimatedSalary"]


@st.cache_resource
def load_model():
    art = joblib.load(ROOT / "models" / "final_model.joblib")
    return art["pipeline"], float(art["threshold"])


@st.cache_data
def load_customers():
    return pd.read_csv(ROOT / "data" / "churn_clean.csv"), pd.read_csv(ROOT / "data" / "test.csv")


@st.cache_data
def score(which: str):
    all_df, test_df = load_customers()
    d = all_df if which == "All customers" else test_df
    return pd.DataFrame({"prob": pipe.predict_proba(d[FEATURES])[:, 1], "Exited": d["Exited"].values})


@st.cache_resource
def shap_explanation():
    import shap
    _, test_df = load_customers()
    Xt = pipe.named_steps["prep"].transform(test_df[FEATURES])
    return shap.TreeExplainer(pipe.named_steps["model"])(Xt)


pipe, THRESHOLD = load_model()


def risk_label(p: float) -> str:
    """High = flagged (at or above the threshold); Medium = above half the threshold; otherwise Low."""
    if p >= THRESHOLD:
        return "High"
    return "Medium" if p >= THRESHOLD / 2 else "Low"


def caution_notes(c: pd.DataFrame) -> list:
    """Plain-language warnings for unusual customers (the model has seen few like them)."""
    r, notes = c.iloc[0], []
    if r["Age"] < 21 or r["Age"] > 75:
        notes.append("Very young or very old customers are rare in the data, so this estimate is less reliable.")
    if r["NumOfProducts"] == 4:
        notes.append("Only 60 customers in the data held 4 products, so this estimate is less reliable.")
    if r["EstimatedSalary"] == 0:
        notes.append("A salary of 0 is unusual; the balance-to-salary feature is set to 0 in this case.")
    return notes


# ------------------------------------------------------------------ pages
def page_risk_calculator():
    st.header("Risk Calculator")
    st.caption("How to read: enter a customer's details to see how likely they are to leave. "
               "High means the customer is flagged for a retention follow-up.")
    defaults = dict(CreditScore=650, Geography="France", Gender="Female", Age=40, Tenure=5,
                    Balance=0.0, NumOfProducts=1, HasCrCard=True, IsActiveMember=True,
                    EstimatedSalary=100000.0)
    for k, v in defaults.items():
        st.session_state.setdefault(f"in_{k}", v)

    def load_test_customer():
        row = load_customers()[1].iloc[int(st.session_state["row_idx"])]
        for k in FEATURES:
            v = row[k]
            if k in ("HasCrCard", "IsActiveMember"):
                v = bool(v)
            elif k in ("Balance", "EstimatedSalary"):
                v = float(v)
            elif k not in ("Geography", "Gender"):
                v = int(v)
            st.session_state[f"in_{k}"] = v
        st.session_state["loaded_actual"] = int(row["Exited"])
        st.session_state["loaded_sig"] = tuple(st.session_state[f"in_{k}"] for k in FEATURES)

    with st.expander("Load a customer from the test set (to compare with the notebook)"):
        c1, c2 = st.columns([1, 3])
        c1.number_input("Row number (0 to 1999)", 0, 1999, 0, key="row_idx")
        c2.button("Load this customer", on_click=load_test_customer)

    left, right = st.columns(2)
    with left:
        st.slider("Credit score", 350, 850, key="in_CreditScore")
        st.selectbox("Country", ["France", "Germany", "Spain"], key="in_Geography")
        st.selectbox("Gender", ["Female", "Male"], key="in_Gender")
        st.slider("Age", 18, 92, key="in_Age")
        st.slider("Tenure (years with the bank)", 0, 10, key="in_Tenure")
    with right:
        st.number_input("Account balance", 0.0, 300000.0, step=1000.0, key="in_Balance")
        st.slider("Number of products", 1, 4, key="in_NumOfProducts")
        st.number_input("Estimated yearly salary", 0.0, 300000.0, step=1000.0, key="in_EstimatedSalary")
        st.checkbox("Has a credit card", key="in_HasCrCard")
        st.checkbox("Active member", key="in_IsActiveMember")

    s = st.session_state
    customer = pd.DataFrame([{
        "CreditScore": int(s["in_CreditScore"]), "Geography": s["in_Geography"], "Gender": s["in_Gender"],
        "Age": int(s["in_Age"]), "Tenure": int(s["in_Tenure"]), "Balance": float(s["in_Balance"]),
        "NumOfProducts": int(s["in_NumOfProducts"]), "HasCrCard": int(s["in_HasCrCard"]),
        "IsActiveMember": int(s["in_IsActiveMember"]), "EstimatedSalary": float(s["in_EstimatedSalary"]),
    }])
    p = float(pipe.predict_proba(customer)[:, 1][0])
    label = risk_label(p)

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Churn probability", f"{p:.1%}")
    m2.metric("Risk level", label)
    m3.metric("Flagged for follow-up", "Yes" if p >= THRESHOLD else "No")
    {"High": st.error, "Medium": st.warning, "Low": st.success}[label](
        f"{label} risk. The flag turns on at a probability of {THRESHOLD:.0%} or more.")
    st.caption(f"Exact probability: {p:.4f}")
    for note in caution_notes(customer):
        st.warning(note)
    if s.get("loaded_sig") == tuple(s[f"in_{k}"] for k in FEATURES):
        st.caption("Loaded test customer. In the data this customer "
                   + ("left the bank." if s["loaded_actual"] == 1 else "stayed with the bank."))


def page_distribution():
    st.header("Probability Distribution")
    st.caption("How to read: each bar counts customers by predicted churn probability. "
               "Customers to the right of the red line are flagged. Orange (customers who really left) "
               "should sit mostly to the right.")
    which = st.radio("Customers to show", ["All customers", "Test customers only"], horizontal=True)
    st.caption("The model was trained on 80% of the customers, so 'Test customers only' (the 20% it never saw) "
               "is the fairer view.")
    d = score(which)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(d.loc[d.Exited == 0, "prob"], bins=40, alpha=0.7, label="Stayed", color="#4C78A8")
    ax.hist(d.loc[d.Exited == 1, "prob"], bins=40, alpha=0.7, label="Left", color="#F58518")
    ax.axvline(THRESHOLD, color="red", linestyle="--", label=f"Threshold {THRESHOLD:.2f}")
    ax.set_xlabel("Predicted churn probability"); ax.set_ylabel("Customers"); ax.legend()
    st.pyplot(fig); plt.close(fig)
    flagged = int((d.prob >= THRESHOLD).sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Customers", f"{len(d):,}")
    c2.metric("Flagged", f"{flagged:,}")
    c3.metric("Share flagged", f"{flagged / len(d):.1%}")


def page_feature_importance():
    st.header("Feature Importance")
    st.caption("How to read: longer bars mean the feature matters more to the model's predictions. "
               "In the SHAP chart, each dot is a customer: red dots have a high value of that feature, "
               "and dots to the right push the risk up.")
    import shap
    tab1, tab2 = st.tabs(["Model importance", "SHAP summary"])
    with tab1:
        _, test_df = load_customers()
        names = pipe.named_steps["prep"].transform(test_df[FEATURES].head(5)).columns
        imp = pd.Series(pipe.named_steps["model"].feature_importances_, index=names).sort_values()
        fig, ax = plt.subplots(figsize=(7, 6))
        imp.plot(kind="barh", color="#4C78A8", ax=ax)
        ax.set_title("Model feature importance"); fig.tight_layout()
        st.pyplot(fig); plt.close(fig)
    with tab2:
        sv = shap_explanation()
        shap.plots.beeswarm(sv, show=False)
        fig = plt.gcf(); fig.tight_layout()
        st.pyplot(fig); plt.close(fig)
        st.caption("Age and number of products are the strongest drivers. Age appears in three engineered "
                   "features, so its total influence is larger than one bar suggests.")


def page_what_if():
    st.header("What-If Simulator")
    st.caption("How to read: pick a customer, then change things the bank could influence (activity, products, "
               "balance, tenure). The 'After' bar shows how the model's churn estimate would move. "
               "It shows what the model expects, not a guaranteed result.")
    _, test_df = load_customers()
    row_i = int(st.number_input("Test customer row number (0 to 1999)", 0, 1999, 501, key="wi_row"))
    base = test_df.iloc[row_i]
    k = f"wi{row_i}"  # new keys per customer, so the controls reset when the customer changes
    st.caption(f"Customer {row_i}: age {int(base.Age)}, {base.Geography}, {base.Gender}, "
               f"{int(base.NumOfProducts)} product(s), balance {base.Balance:,.0f}, "
               f"{'active' if base.IsActiveMember else 'inactive'}, tenure {int(base.Tenure)} years.")

    c1, c2 = st.columns(2)
    active = c1.checkbox("Active member", value=bool(base.IsActiveMember), key=f"{k}_act")
    products = c1.slider("Number of products", 1, 4, int(base.NumOfProducts), key=f"{k}_prod")
    balance = c2.number_input("Account balance", 0.0, 300000.0, float(base.Balance), step=1000.0, key=f"{k}_bal")
    tenure = c2.slider("Tenure (years with the bank)", 0, 10, int(base.Tenure), key=f"{k}_ten")

    before = pd.DataFrame([base[FEATURES].to_dict()])
    after = before.copy()
    after.loc[0, "IsActiveMember"] = int(active)
    after.loc[0, "NumOfProducts"] = int(products)
    after.loc[0, "Balance"] = float(balance)
    after.loc[0, "Tenure"] = int(tenure)
    p0 = float(pipe.predict_proba(before)[:, 1][0])
    p1 = float(pipe.predict_proba(after)[:, 1][0])

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Before", f"{p0:.1%}")
    m2.metric("After", f"{p1:.1%}", f"{(p1 - p0) * 100:+.1f} points", delta_color="inverse")
    m3.metric("Risk level", f"{risk_label(p0)} to {risk_label(p1)}")

    fig, ax = plt.subplots(figsize=(8, 2.6))
    colors = {"High": "#E45756", "Medium": "#F2B84B", "Low": "#54A24B"}
    ax.barh(["After", "Before"], [p1, p0], color=[colors[risk_label(p1)], colors[risk_label(p0)]])
    ax.axvline(THRESHOLD, color="black", linestyle="--", label=f"Flag threshold {THRESHOLD:.2f}")
    ax.set_xlim(0, 1); ax.set_xlabel("Churn probability")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.45), frameon=False)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)

    if abs(p1 - p0) < 1e-9:
        st.info("No changes yet. Adjust the controls above to see the effect.")
    else:
        direction = "fall" if p1 < p0 else "rise"
        st.write(f"The model expects the churn probability to **{direction}** from **{p0:.1%}** to **{p1:.1%}** "
                 f"({(p1 - p0) * 100:+.1f} points).")
    for note in caution_notes(after):
        st.warning(note)


# ------------------------------------------------------------------ menu
st.sidebar.title("🏦 Churn Intelligence")
page = st.sidebar.radio("Menu", ["Risk Calculator", "Distribution", "Feature Importance", "What-If Simulator"])
st.sidebar.caption(f"Model: XGBoost | flag threshold {THRESHOLD:.2f}")
{"Risk Calculator": page_risk_calculator, "Distribution": page_distribution,
 "Feature Importance": page_feature_importance, "What-If Simulator": page_what_if}[page]()
