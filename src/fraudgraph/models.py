"""Small fixed-budget paired experiments; no test-set tuning."""
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier


def make_model(name, seed=42, threads=2):
    if name == "logistic":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                             LogisticRegression(C=1., class_weight="balanced", max_iter=3000, random_state=seed))
    if name == "xgboost":
        return make_pipeline(SimpleImputer(strategy="median"),
            XGBClassifier(n_estimators=250, max_depth=4, learning_rate=.05, subsample=.9,
                          colsample_bytree=.9, min_child_weight=5, reg_lambda=5,
                          tree_method="hist", eval_metric="aucpr", random_state=seed, n_jobs=threads))
    raise ValueError(name)
