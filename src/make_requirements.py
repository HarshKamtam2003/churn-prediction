r"""Write requirements.txt with the exact library versions of this environment.
Run from the project folder (with the venv active):   python src/make_requirements.py
"""
from importlib.metadata import version

from preprocess import ROOT

PACKAGES = ["pandas", "numpy", "scikit-learn", "xgboost", "shap",
            "matplotlib", "seaborn", "plotly", "streamlit", "joblib"]
lines = [f"{p}=={version(p)}" for p in PACKAGES]
(ROOT / "requirements.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
