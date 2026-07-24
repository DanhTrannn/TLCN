from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from repurchase_ml.contracts import NUMERICAL_FEATURES


def build_dummy_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("model", DummyClassifier(strategy="prior")),
        ]
    )


def build_logistic_pipeline(class_weight: str | None = None) -> Pipeline:
    numerical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    preprocessing = ColumnTransformer(
        transformers=[("numerical", numerical_pipeline, list(NUMERICAL_FEATURES))],
        remainder="drop",
    )
    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            (
                "model",
                LogisticRegression(
                    class_weight=class_weight,
                    max_iter=1000,
                    random_state=20260724,
                ),
            ),
        ]
    )

