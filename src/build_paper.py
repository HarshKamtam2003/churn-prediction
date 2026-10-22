r"""Build the research paper (Word file) from your saved results and figures.

Run from the project folder:
    python src/build_paper.py --author "Your Full Name" --portal "Portal or company name"

Output: reports/Churn_Research_Paper.docx
Tables are read from the CSV files in reports/, and charts from reports/figures/,
so the paper always matches your saved results.
"""
import argparse
import re
from datetime import date

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from preprocess import ROOT

ap = argparse.ArgumentParser()
ap.add_argument("--author", default="[Author name]")
ap.add_argument("--portal", default="[Portal or company name]")
args = ap.parse_args()

FIGS = ROOT / "reports" / "figures"
REP = ROOT / "reports"
NAVY = RGBColor(0x1F, 0x3A, 0x5F)
APP_URL = "https://bank-churn-data-model.streamlit.app"
TITLE = "Predictive Churn Intelligence for Retail Banking"
SUBTITLE = "Identifying and explaining customer attrition with machine learning"

# ---------------------------------------------------------------- document setup
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Inches(1)
sec.top_margin = sec.bottom_margin = Inches(0.9)

normal = doc.styles["Normal"]
normal.font.name, normal.font.size = "Calibri", Pt(11)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.12
for name, size in [("Heading 1", 15), ("Heading 2", 12.5)]:
    st = doc.styles[name]
    st.font.name, st.font.size, st.font.bold = "Calibri", Pt(size), True
    st.font.color.rgb = NAVY
    st.paragraph_format.space_before = Pt(14 if name == "Heading 1" else 10)
    st.paragraph_format.space_after = Pt(5)
    st.paragraph_format.keep_with_next = True

# page number in the footer
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fp.add_run()
for kind, text in [("begin", None), (None, "PAGE"), ("end", None)]:
    if kind:
        el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind)
    else:
        el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = text
    run._r.append(el)
run.font.size = Pt(9)


def add_runs(par, text, size=None, italic=False):
    """Write text into a paragraph; **double stars** make bold."""
    for i, chunk in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not chunk:
            continue
        r = par.add_run(chunk)
        r.bold = i % 2 == 1
        r.italic = italic
        if size:
            r.font.size = Pt(size)


def H1(t): doc.add_heading(t, level=1)
def H2(t): doc.add_heading(t, level=2)


def P(text, align=None, after=None):
    par = doc.add_paragraph()
    add_runs(par, text)
    if align == "j":
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if after is not None:
        par.paragraph_format.space_after = Pt(after)
    return par


def bullets(items, style="List Bullet"):
    for t in items:
        par = doc.add_paragraph(style=style)
        add_runs(par, t)
        par.paragraph_format.space_after = Pt(2)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


_t = {"n": 0}


def table(caption, header, rows, widths, align=None, size=9):
    """caption above, then a table. widths in inches; align: list of 'l'/'r'/'c' per column."""
    _t["n"] += 1
    cap = doc.add_paragraph()
    add_runs(cap, f"**Table {_t['n']}.** {caption}", size=9.5)
    cap.paragraph_format.keep_with_next = True
    cap.paragraph_format.space_after = Pt(3)
    tb = doc.add_table(rows=1, cols=len(header))
    tb.style = "Table Grid"
    tb.autofit = False
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    align = align or ["l"] + ["r"] * (len(header) - 1)
    amap = {"l": WD_ALIGN_PARAGRAPH.LEFT, "r": WD_ALIGN_PARAGRAPH.RIGHT, "c": WD_ALIGN_PARAGRAPH.CENTER}

    def fill(row, values, head=False):
        for j, v in enumerate(values):
            c = row.cells[j]
            c.width = Inches(widths[j])
            par = c.paragraphs[0]
            par.paragraph_format.space_after = Pt(1)
            par.paragraph_format.space_before = Pt(1)
            par.paragraph_format.line_spacing = 1.0
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER if head else amap[align[j]]
            r = par.add_run(str(v)); r.font.size = Pt(size)
            if head:
                r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); shade(c, "1F3A5F")

    fill(tb.rows[0], header, head=True)
    for k, vals in enumerate(rows):
        row = tb.add_row()
        fill(row, vals)
        if k % 2 == 1:
            for c in row.cells:
                shade(c, "EEF2F7")
    for j, col in enumerate(tb.columns):  # real column widths (also needed by LibreOffice and Google Docs)
        col.width = Inches(widths[j])
    for row in tb.rows[:-1]:  # keep a small table on one page
        for c in row.cells:
            for par in c.paragraphs:
                par.paragraph_format.keep_with_next = True
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return _t["n"]


_f = {"n": 0}


def figure(files, caption, width, ncols=1):
    """Insert one or more images (grid with ncols columns) with a caption below."""
    _f["n"] += 1
    files = [files] if isinstance(files, str) else files
    tb = doc.add_table(rows=0, cols=ncols)
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i in range(0, len(files), ncols):
        row = tb.add_row()
        for j, f in enumerate(files[i:i + ncols]):
            par = row.cells[j].paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.space_after = Pt(0)
            path = FIGS / f
            if path.exists():
                par.add_run().add_picture(str(path), width=Inches(width))
            else:
                r = par.add_run(f"[Missing figure: {f}]"); r.italic = True
                print("WARNING: figure not found:", f)
    cap = doc.add_paragraph()
    add_runs(cap, f"**Figure {_f['n']}.** {caption}", size=9.5)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    return _f["n"]


def read(name, **kw):
    path = REP / name
    if not path.exists():
        print("WARNING: results file not found:", name)
        return None
    return pd.read_csv(path, index_col=0, **kw)


# ---------------------------------------------------------------- title page
for _ in range(5):
    doc.add_paragraph()
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run(TITLE); r.bold = True; r.font.size = Pt(26); r.font.color.rgb = NAVY
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run(SUBTITLE); r.italic = True; r.font.size = Pt(14)
for _ in range(2):
    doc.add_paragraph()
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run(args.author); r.font.size = Pt(14); r.bold = True
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
t.add_run(date.today().strftime("%B %Y")).font.size = Pt(12)
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
t.add_run("Live dashboard: " + APP_URL).font.size = Pt(10)
doc.add_page_break()

# ---------------------------------------------------------------- abstract
H1("Abstract")
P("Customer churn is costly for retail banks, and retention is easier when at-risk customers are identified early. "
  "This study builds a system that predicts which customers are likely to leave a bank, gives each a churn "
  "probability, and explains the main drivers of that risk. Using records for 10,000 retail bank customers, of whom "
  "20.4% left, we compare Logistic Regression, Decision Tree, Random Forest, Gradient Boosting and XGBoost inside a "
  "leakage-free preprocessing pipeline. A tuned XGBoost model performed best (test ROC-AUC 0.871; cross-validated "
  "0.864). With a decision threshold of 0.29 chosen from the precision-recall curve, it identifies 67.6% of churners "
  "at 60.7% precision. SHAP and partial dependence analysis show that age, the number of products held, activity "
  "status and country are the strongest drivers: customers aged 45-60 churn about five times as often as those "
  "under 40, and customers holding three or four products churn at 83-100%. We turn these findings into five "
  "retention actions, examine fairness across gender and country, and deploy the model as an interactive "
  "dashboard. The data is a single practice dataset, and the results show association, not causation.", "j")
P("**Keywords:** customer churn, retail banking, XGBoost, SHAP, explainable machine learning, retention")

# ---------------------------------------------------------------- 1 introduction
H1("1. Introduction and business context")
P("Customer churn, the loss of customers who stop using a bank's services, is a persistent problem in retail "
  "banking. Retaining an existing customer is generally cheaper than winning a new one, so a bank that can see who "
  "is likely to leave, and why, can act earlier and spend its retention effort where it matters most.", "j")
P("This project builds an end-to-end churn intelligence system with four aims:", "j", after=2)
bullets([
    "predict which customers are likely to leave and give each a churn probability;",
    "explain the main drivers of churn in plain language, which also supports the transparency that banks are "
    "generally expected to provide for model-driven decisions;",
    "turn the findings into targeted retention actions; and",
    "make the model usable through an interactive dashboard.",
])
P("Section 2 describes the data and Section 3 explores it. Section 4 sets out the methodology and Section 5 the "
  "model results. Section 6 explains the final model, Section 7 gives recommendations, and Sections 8 and 9 cover "
  "responsible use and limitations. Section 10 concludes.", "j")

# ---------------------------------------------------------------- 2 data
H1("2. Data")
P(f"The data file, European_Bank.csv, was downloaded from the project portal of {args.portal}. It holds records for "
  "10,000 retail bank customers in three countries (France, Germany and Spain) with 14 columns. The target, "
  "**Exited**, is 1 if the customer left the bank and 0 if the customer stayed.", "j")
P("**Cleaning.** Two identifier columns (CustomerId and Surname) carry no predictive value and were dropped. A Year "
  "column held the value 2025 for every row, so it carries no information and was also dropped. There were no "
  "missing values and no duplicate rows. The final dataset has 10 predictors and the target (Table 1).", "j")
table("Data dictionary (variables used in modelling).", ["Variable", "Type", "Meaning"], [
    ["CreditScore", "Number", "Customer's credit score; higher means more creditworthy"],
    ["Geography", "Category", "Country of residence (France, Germany, Spain)"],
    ["Gender", "Category", "Female or Male"],
    ["Age", "Number", "Age in years"],
    ["Tenure", "Number", "Years the customer has been with the bank"],
    ["Balance", "Number", "Money held in the account"],
    ["NumOfProducts", "Number", "Number of bank products held (accounts, cards, loans)"],
    ["HasCrCard", "0/1", "1 if the customer has a credit card"],
    ["IsActiveMember", "0/1", "1 if the customer actively uses the bank"],
    ["EstimatedSalary", "Number", "Estimated yearly income"],
    ["Exited (target)", "0/1", "1 if the customer left the bank, 0 if the customer stayed"],
], [1.45, 0.8, 3.9], ["l", "l", "l"])
P("**Class balance.** 2,037 of the 10,000 customers left, a churn rate of 20.4% (Figure 1). Because only about one "
  "customer in five churns, a model that predicted that nobody leaves would already be right about 80% of the time. "
  "Accuracy alone is therefore a poor measure of quality, and models in this study are judged on precision, recall, "
  "F1 and ROC-AUC.", "j")
figure("01_churn_rate.png", "Customers who stayed and left (churn rate 20.4%).", 3.4)

# ---------------------------------------------------------------- 3 EDA
H1("3. Exploratory data analysis")
P("This section shows who churns. Each chart reports the churn rate, the share of customers in a group who left.", "j")
H2("3.1 Country and gender")
P("Customers in Germany churn at 32.4%, about twice the rate in France (16.2%) and Spain (16.7%). Women churn more "
  "than men (25.1% against 16.5%) (Figure 2).", "j")
figure(["02_churn_by_Geography.png", "03_churn_by_Gender.png"],
       "Churn rate by (a) country and (b) gender.", 3.05, 2)
H2("3.2 Products and activity")
P("The number of products is the most striking pattern. Customers holding two products are the safest (7.6% churn), "
  "single-product customers churn at 27.7%, and churn jumps to 82.7% for three products and 100% for four. The "
  "three- and four-product groups are small (266 and 60 customers, together 3.3% of the bank), so the rates are "
  "real but cover few customers. Inactive members churn at 26.9% against 14.3% for active members (Figure 3).", "j")
figure(["04_churn_by_NumOfProducts.png", "06_churn_by_IsActiveMember.png"],
       "Churn rate by (a) number of products and (b) activity status.", 3.05, 2)
H2("3.3 Age")
P("Churn rises steeply with age: 7.5% for ages 18-30, 12.1% for 31-40, 34.0% for 41-50 and 56.2% for 51-60. It then "
  "falls to 24.8% for customers over 60 (Figure 4).", "j")
figure("07_churn_by_AgeBand.png", "Churn rate by age band.", 3.6)
H2("3.4 Variables with little effect")
P("Having a credit card (20.8% churn without, 20.2% with), tenure (about 17-23% in every year) and credit score "
  "(23.6% below 500 and about 20% above 600) make little difference. One result runs against the initial "
  "expectation: customers with a zero balance churn less (13.8%) than customers with a balance (24.1%) (Figure 5).", "j")
figure(["05_churn_by_HasCrCard.png", "08_churn_by_Tenure.png", "09_churn_by_CreditBand.png",
        "10_churn_by_ZeroBalance.png"],
       "Churn rate by (a) credit card, (b) tenure, (c) credit score band and (d) zero balance.", 2.9, 2)
table("Highest-churn groups compared with a reference group.", ["Group", "Churn rate", "Reference group"], [
    ["4 products", "100.0%", "2 products: 7.6%"],
    ["3 products", "82.7%", "2 products: 7.6%"],
    ["Age 51-60", "56.2%", "Age 18-30: 7.5%"],
    ["Age 41-50", "34.0%", "Age 18-30: 7.5%"],
    ["Germany", "32.4%", "France 16.2%, Spain 16.7%"],
], [1.7, 1.2, 2.6], ["l", "r", "l"])
H2("3.5 Correlations and outliers")
P("Age has the strongest correlation with churn (+0.29), followed by activity (-0.16) and balance (+0.12). The "
  "correlation with the number of products is weak (-0.05) even though its effect on churn is large, because the "
  "effect is not a straight line: two products are safest, while one, three and four are riskier. This favours "
  "models that can capture non-linear patterns (Figure 6). Balance and the number of products are moderately "
  "linked (-0.30), which is not high enough to cause concern.", "j")
figure("11_correlation_heatmap.png", "Correlation between numeric features and churn.", 4.4)
P("Boxplots show high ages (62-92) and a few very low credit scores (about 350-400), but these are plausible values "
  "and all outliers were kept. Balance shows no outliers (Figure 7).", "j")
figure("12_outliers.png", "Boxplots of age, balance and credit score.", 5.6)

# ---------------------------------------------------------------- 4 methodology
H1("4. Methodology")
H2("4.1 Preprocessing and feature engineering")
P("All steps were built as one scikit-learn pipeline, so training and the dashboard use exactly the same "
  "transformations. Geography and Gender were one-hot encoded, dropping the first category to avoid redundancy. "
  "Numeric features were standardised only for Logistic Regression, since tree-based models do not need scaling, "
  "and the scaler was fitted on training data only to prevent data leakage. Five features were engineered "
  "(Table 3).", "j")
table("Engineered features.", ["Feature", "Definition", "Idea"], [
    ["BalanceSalaryRatio", "Balance / EstimatedSalary (0 if salary is 0)", "Size of balance relative to income"],
    ["ProductDensity", "NumOfProducts / (Tenure + 1)", "Products per year with the bank"],
    ["EngagementProduct", "IsActiveMember x NumOfProducts", "Activity combined with product holding"],
    ["AgeTenure", "Age x Tenure", "Age and loyalty together"],
    ["AgeByTenure", "Age / (Tenure + 1)", "Age relative to time with the bank"],
], [1.55, 2.5, 2.1], ["l", "l", "l"])
P("Adding 1 to Tenure avoids division by zero for new customers.", after=6)
H2("4.2 Train-test split")
P("The data was split 80/20 with stratification on the target and a fixed random seed (42). The training set holds "
  "8,000 customers (churn rate 20.375%) and the test set 2,000 customers (20.350%, 407 churners). Matching churn "
  "rates confirm that the split is balanced. The test set was not used for any modelling choice.", "j")
H2("4.3 Models and tuning")
P("A Logistic Regression (with and without class weighting) served as the interpretable benchmark. We then trained a "
  "Decision Tree (maximum depth 5) and a Random Forest (300 trees), followed by Gradient Boosting and XGBoost. "
  "Random Forest, Gradient Boosting and XGBoost were tuned with randomised search (15 settings each) using 5-fold "
  "stratified cross-validation scored on ROC-AUC (Table 4).", "j")
table("Tuned model settings.", ["Model", "Selected settings", "CV AUC"], [
    ["Random Forest", "500 trees, depth 8, min. leaf 10, max. features 0.5", "0.858"],
    ["Gradient Boosting", "200 trees, depth 4, learning rate 0.03, subsample 0.8", "0.863"],
    ["XGBoost", "300 trees, depth 3, learning rate 0.03, subsample 0.8, column sample 0.85", "0.864"],
], [1.5, 4.0, 0.7], ["l", "l", "r"])
H2("4.4 Evaluation and choice of threshold")
P("Models were compared on accuracy, precision, recall, F1 and ROC-AUC, and on the gap between training and test "
  "scores to detect overfitting. The final model was chosen by cross-validated AUC on the training data, which "
  "keeps the test set unbiased. A churn probability must be turned into a yes or no flag by a threshold. The default "
  "of 0.5 is rarely best when only one customer in five churns, so the threshold was chosen from the "
  "precision-recall curve of cross-validated predictions on the training data, at the point that maximises F1.", "j")
H2("4.5 Dashboard")
P(f"The locked model and its pipeline are deployed as an interactive Streamlit dashboard ({APP_URL}). Its four "
  "modules are a Risk Calculator (probability, Low/Medium/High label and follow-up flag for any customer), a "
  "Distribution page (predicted risk across customers with the threshold marked), a Feature Importance page "
  "(importance and SHAP), and a What-If Simulator that shows the risk before and after changes to activity, "
  "products, balance or tenure. Its predictions were checked against the notebook results, and edge cases (new "
  "customers, zero balance, four products, very young and very old customers) were tested (Appendix B).", "j")

# ---------------------------------------------------------------- 5 results
H1("5. Model results")
H2("5.1 Baseline and tree-based models")
d4 = read("day4_results.csv")
if d4 is not None:
    rows = [[m] + [f"{r[c]:.3f}" for c in ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC (test)",
                                            "ROC-AUC (train)", "CV AUC mean", "Overfit gap (AUC)"]]
            for m, r in d4.iterrows()]
    table("Baseline and tree-based models on the test set (default 0.5 threshold).",
          ["Model", "Acc.", "Prec.", "Recall", "F1", "AUC test", "AUC train", "CV AUC", "Gap"],
          rows, [1.7, 0.5, 0.5, 0.55, 0.5, 0.6, 0.65, 0.55, 0.6], size=8.5)
P("Table 5 shows the results. Plain Logistic Regression reaches 80.8% accuracy but finds only 18.9% of churners, barely better than "
  "predicting that nobody leaves (79.7% on the test set). Balancing the classes raises recall to 70.8%, at the cost "
  "of many false alarms (454 stayers flagged). The Decision Tree and Random Forest are clearly stronger, with test "
  "AUC of 0.844 and 0.851 (Figure 8). The Random Forest overfits: its training AUC is 1.000 against 0.851 on "
  "the test set, a gap of 0.149, while the other models show gaps close to zero. Cross-validation scores are close to "
  "test scores (spread 0.013-0.020), so the results are stable.", "j")
figure("13_confusion_matrices.png", "Confusion matrices of the four baseline models on the test set (threshold 0.5).", 4.3)
H2("5.2 Tuned and boosted models")
d5 = read("day5_comparison.csv")
if d5 is not None:
    rows = [[m] + [f"{r[c]:.3f}" for c in ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "CV AUC"]]
            for m, r in d5.iterrows()]
    table("All models compared on the test set (default 0.5 threshold).",
          ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "CV AUC"],
          rows, [2.1, 0.7, 0.75, 0.6, 0.55, 0.7, 0.65])
P("Table 6 compares all models. Tuning improved the Random Forest (test AUC 0.862) and the boosted models did better still. XGBoost had the "
  "best cross-validated AUC (0.864), the best test AUC (0.871), the highest F1 (0.606) and the highest accuracy "
  "(0.872) (Figure 9). It was selected as the final model, and its tree structure also works well with SHAP "
  "explanations.", "j")
figure("14_roc_curves.png", "ROC curves of the tuned models on the test set.", 4.0)
H2("5.3 Decision threshold")
P("At the default 0.5 threshold, XGBoost finds 48.6% of churners at 80.5% precision. The precision-recall curve "
  "(Figure 10) shows that a lower threshold finds many more churners for a smaller loss in precision. The "
  "threshold of 0.29 maximises F1 on cross-validated training predictions. On the test set it gives precision "
  "0.607, recall 0.676 and F1 0.640 (Table 7).", "j")
figure("15_precision_recall.png", "Precision-recall curve of the final model; the red dot marks the chosen threshold.", 3.3)
table("Final model at the default and chosen thresholds (test set).", ["Threshold", "Precision", "Recall", "F1"], [
    ["0.50 (default)", "0.805", "0.486", "0.606"],
    ["0.29 (chosen)", "0.607", "0.676", "0.640"],
], [1.7, 1.1, 1.1, 1.1])
P("In practical terms (Figure 11), the model flags 453 of the 2,000 test customers (22.7%). Of these, 275 are "
  "real churners and 178 are false alarms. It misses 132 churners (32.4% of all churners) and correctly leaves "
  "1,415 stayers alone. Whether this balance is right depends on the cost of a retention offer compared with the "
  "value of a saved customer; a higher threshold would reduce false alarms at the price of missing more "
  "churners.", "j")
figure("16_final_confusion_matrix.png", "Confusion matrix of the final XGBoost model at threshold 0.29 (test set).", 3.0)

# ---------------------------------------------------------------- 6 explainability
H1("6. Explaining the final model")
H2("6.1 Which features matter")
P("SHAP values show how much each feature moves a customer's predicted risk. By mean absolute SHAP value, age "
  "(0.79) and the number of products (0.74) lead, followed by engagement (0.33), Germany (0.26) and gender (0.21). "
  "Balance, balance-to-salary ratio, salary and activity status each contribute 0.06-0.10 (Figures 12 and 13). Two "
  "points help reading these bars. Age enters through three features (Age, AgeTenure and AgeByTenure), so its "
  "total influence is larger than one bar suggests. The effect of activity is shared between IsActiveMember and "
  "EngagementProduct, so the single activity bar understates it.", "j")
figure(["17_feature_importance.png", "19_shap_bar.png"],
       "(a) Model feature importance and (b) mean absolute SHAP value for each feature.", 3.1, 2)
figure("18_shap_beeswarm.png",
       "SHAP summary: each dot is a customer; red means a high feature value, and dots to the right raise the risk.", 4.6)
H2("6.2 How risk changes with each feature")
P("Partial dependence plots (Figure 14) show the average predicted risk as one feature changes. Risk rises "
  "from about 10% for customers up to their mid-30s to a peak of around 50% in the late 50s and early 60s, then falls sharply after about 65. By "
  "number of products it is about 27% for one product, 11% for two, 75% for three and 83% for four. Balance has "
  "almost no effect on its own (about 20% across the range), and inactive customers sit at about 27% against 16% "
  "for active ones.", "j")
figure("23_partial_dependence.png", "Partial dependence of predicted churn risk on age, products, balance and activity.", 5.0)
H2("6.3 Why individual customers are flagged")
P("SHAP also explains single customers (Figure 15). The highest-risk customer in the test set (risk 0.995, who did "
  "leave) is a 58-year-old man in Germany with four products, who is inactive and holds a balance far above his "
  "salary. Holding four products adds the most risk, followed by age, inactivity and country. A customer exactly at "
  "the threshold (risk 0.29) is a 61-year-old woman in Spain with one product who is active: her age pushes the "
  "risk up, while being active pulls it down. The lowest-risk customer (0.009) is a 26-year-old man in France "
  "with two products who is active; two products and a young age both lower the risk.", "j")
figure(["20_shap_waterfall_high_risk.png", "21_shap_waterfall_near_threshold.png",
        "22_shap_waterfall_low_risk.png"],
       "SHAP explanations for (a) the highest-risk, (b) a threshold-level and (c) the lowest-risk test customer.", 4.4, 1)
H2("6.4 Comparison with Logistic Regression")
d6 = read("day6_logreg_vs_shap.csv")
if d6 is not None:
    rows = [[f, f"{r['SHAP importance']:.3f}", r["SHAP direction"], f"{r['LogReg coef']:.3f}",
             r["LogReg direction"], int(r["SHAP rank"]), int(r["LogReg rank"])]
            for f, r in d6.head(8).iterrows()]
    table("Top features in SHAP compared with Logistic Regression (all features in Appendix A).",
          ["Feature", "SHAP importance", "SHAP direction", "LogReg coefficient", "LogReg direction",
           "SHAP rank", "LogReg rank"], rows, [1.6, 0.8, 0.7, 0.85, 0.75, 0.6, 0.65], size=8.5)
P("The two methods agree on the direction of effect for 13 of 16 features, and both place age, Germany and "
  "gender in their top five. They differ on two points. The number of products ranks second in SHAP but eighth in "
  "Logistic Regression, because its effect is not a straight line and a linear model cannot represent it. "
  "Activity ranks first in Logistic Regression but ninth in SHAP, because XGBoost spreads it across IsActiveMember "
  "and EngagementProduct.", "j")
H2("6.5 Main drivers in plain language")
table("Main churn drivers (churn rate of the group relative to its comparison group).",
      ["Driver", "Group compared", "Times as likely to churn"], [
    ["Age", "Aged 45-60 against under 40", "5.0"],
    ["Products", "3-4 products against 2 products", "11.3"],
    ["Activity", "Inactive against active members", "1.9"],
    ["Country", "Germany against France and Spain", "2.0"],
    ["Gender", "Women against men", "1.5"],
], [1.3, 3.2, 1.6], ["l", "l", "r"])

# ---------------------------------------------------------------- 7 recommendations
H1("7. Recommendations")
P("The recommendations tie each action to a driver in the data. They describe associations, so each should be "
  "tested on a pilot group before a wide rollout.", "j")
bullets([
    "**Customers aged 45-60.** Churn is five times that of customers under 40 (34.0% at 41-50 and 56.2% at 51-60). "
    "Offer a relationship-manager call and a review of products suited to this stage of life.",
    "**Customers with three or more products.** They are rare (3.3% of customers) but churn at 83-100%. Contact "
    "them for a service and fee review to find out what is going wrong before they leave.",
    "**Inactive members.** They churn 1.9 times as often as active members. Run a re-engagement campaign with "
    "reminders of benefits and prompts to use the bank's services, followed by a call for those who stay silent.",
    "**Customers in Germany.** Churn is double that of France and Spain (32.4%). Investigate local pricing, service "
    "quality and competition, and consider a targeted offer.",
    "**Single-product customers.** Customers with two products churn least (7.6% against 27.7% for one). Test "
    "offering a suitable second product to a pilot group, with a similar group left alone for comparison.",
], "List Number")
P("In daily use, customers with a churn probability of 0.29 or more form the contact list, ordered by probability. "
  "The SHAP explanation tells the contacting agent which issue to address, and the pilot results show which actions "
  "actually keep customers.", "j")

# ---------------------------------------------------------------- 8 responsible use
H1("8. Responsible use and fairness")
P("Churn scores should support better service, not worse treatment. We therefore checked how the final model behaves "
  "across gender and country on the test set (Table 10).", "j")
d9 = read("day9_fairness.csv")
if d9 is not None:
    rows = [[g, int(r["Customers"])] + [f"{r[c]:.1f}" for c in ["Actual churn %", "Flagged %", "Recall %", "Precision %"]]
            for g, r in d9.iterrows()]
    table("Model behaviour by group on the test set (threshold 0.29).",
          ["Group", "Customers", "Actual churn %", "Flagged %", "Recall %", "Precision %"],
          rows, [1.8, 0.9, 1.0, 0.8, 0.8, 0.9])
P("Precision is similar across groups (58.9% to 61.9%), so a flagged customer is about equally likely to be a real "
  "churner whichever group the customer belongs to. Recall differs: the model finds 78.1% of churners in Germany "
  "against 61.1% in France and 61.7% in Spain, and 71.2% of women who churn against 62.6% of men. Flag rates follow "
  "actual churn rates, but the highest-risk groups are flagged somewhat more than their churn rate alone would "
  "suggest (Germany 37.9% flagged against 30.0% churn; women 28.8% against 25.1%). Group sizes in the test set "
  "are modest (475 to 1,070), so differences of a few points should be read with care.", "j")
P("Several practices follow from this. Gender and country are inputs to the model, and gender is the fifth most "
  "important feature. A bank should decide whether it needs them, and test a version without them. Flags should "
  "trigger supportive retention actions and never worse prices or terms. Group-level results should be monitored over "
  "time, and a person should review decisions that affect customers. Finally, per-customer SHAP explanations let "
  "staff, customers and regulators see why a customer was flagged.", "j")

# ---------------------------------------------------------------- 9 limitations
H1("9. Limitations")
bullets([
    "**Single dataset.** All results come from one dataset of 10,000 customers; they may not generalise to other "
    "banks, countries or periods.",
    "**No time dimension.** The Year column was constant (2025), so the model cannot learn how churn changes over "
    "time or detect drift.",
    "**Possibly synthetic fields.** The estimated salary may be synthetic or weakly related to reality.",
    "**Association, not causation.** Patterns such as the effect of the number of products may reflect other factors; "
    "recommendations should be tested before rollout.",
    "**Missed churners.** At the chosen threshold, 132 of 407 churners (32.4%) are not flagged, and 178 stayers are.",
    "**Costs not modelled.** The threshold maximises F1; a bank with real cost figures could choose a different "
    "balance.",
    "**One split.** Test results come from a single 2,000-customer test set, although cross-validation on the "
    "training data gave consistent results.",
    "**Demonstration only.** The dashboard is a demonstration and should not be used for real customer decisions.",
])

# ---------------------------------------------------------------- 10 conclusion
H1("10. Conclusion")
P("A tuned XGBoost model predicts bank customer churn well (test ROC-AUC 0.871) and, at a threshold of 0.29, finds "
  "about two thirds of churners at 61% precision. Age, the number of products, activity and country explain most of "
  "the risk, and SHAP lets every flag be explained. The findings translate into five concrete retention actions, "
  "and a live dashboard lets staff score customers and test what-if changes. Next steps are to validate the "
  "recommendations on a pilot group, estimate the costs behind the threshold, and test the model on newer data over "
  "time.", "j")

# ---------------------------------------------------------------- references
H1("References")
refs = [
    f"{args.portal}. (2026). European bank customer churn dataset (European_Bank.csv) [Data set]. Project portal, "
    "accessed October 2026.",
    "Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5-32.",
    "Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. Proceedings of the 22nd ACM SIGKDD "
    "International Conference on Knowledge Discovery and Data Mining, 785-794.",
    "Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. Annals of Statistics, "
    "29(5), 1189-1232.",
    "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. Advances in Neural "
    "Information Processing Systems, 30.",
    "Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, "
    "12, 2825-2830.",
]
for ref in refs:
    par = doc.add_paragraph(ref)
    par.paragraph_format.left_indent = Inches(0.3)
    par.paragraph_format.first_line_indent = Inches(-0.3)
    par.paragraph_format.space_after = Pt(4)

# ---------------------------------------------------------------- appendices
doc.add_page_break()
H1("Appendix A. Logistic Regression and SHAP compared (all features)")
if d6 is not None:
    rows = [[f, f"{r['SHAP importance']:.3f}", r["SHAP direction"], f"{r['LogReg coef']:.3f}",
             r["LogReg direction"], int(r["SHAP rank"]), int(r["LogReg rank"])]
            for f, r in d6.iterrows()]
    table("All features: SHAP importance and Logistic Regression coefficient.",
          ["Feature", "SHAP importance", "SHAP direction", "LogReg coefficient", "LogReg direction",
           "SHAP rank", "LogReg rank"], rows, [1.6, 0.8, 0.7, 0.85, 0.75, 0.6, 0.65], size=8.5)
P("SHAP direction shows whether higher feature values raise (+) or lower (-) risk, based on the correlation between "
  "the feature and its SHAP value; for features with a non-linear effect, such as the number of products, this is "
  "only a rough guide.", after=6)
H1("Appendix B. Dashboard edge-case tests")
P("The base customer is a 40-year-old French woman with a credit score of 650, five years of tenure, a balance of "
  "80,000, two products, a credit card, active status and a salary of 100,000. Each row changes one or more of these "
  "values.", "j")
table("Model output for unusual customers.", ["Case", "Churn probability", "Flagged"], [
    ["Typical customer", "0.0751", "No"],
    ["Tenure = 0", "0.1076", "No"],
    ["Balance = 0", "0.0349", "No"],
    ["4 products", "0.9134", "Yes"],
    ["Very young (18)", "0.0317", "No"],
    ["Very old (92)", "0.0312", "No"],
    ["Salary = 0", "0.0481", "No"],
    ["Tenure 0, balance 0, 4 products", "0.7760", "Yes"],
    ["Lowest credit score (350)", "0.1255", "No"],
], [3.2, 1.5, 1.0], ["l", "r", "c"])
P("All cases produce valid probabilities between 0 and 1. The dashboard shows a caution for very young or old "
  "customers, for four products and for a salary of zero, because the model has seen few such customers.", "j")

out = REP / "Churn_Research_Paper.docx"
doc.save(out)
print("Saved", out)
