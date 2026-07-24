ML_STAGES = (
    "resolve_gold_publication",
    "build_point_in_time_features",
    "build_repurchase_labels",
    "validate_ml_dataset",
    "temporal_split",
    "train_dummy_and_logistic",
    "optional_train_random_forest",
    "evaluate_and_select",
    "persist_model_artifact_manifest",
    "batch_score_eligible_customers",
    "validate_predictions",
    "publish_repurchase_scores",
    "publish_ml_audit",
)

