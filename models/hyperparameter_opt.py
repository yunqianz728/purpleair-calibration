"""
Hyperparameter Optimization Module

Implements Bayesian optimization for gradient boosting models using Optuna.

The paper uses 20 trials per model to find optimal hyperparameters minimizing
weighted MAE on validation set.

Example:
    >>> from models.hyperparameter_opt import optimize_xgboost
    >>> best_params, study = optimize_xgboost(X_train, y_train, X_val, y_val)
"""

import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
import xgboost as xgb
import catboost as cb
import lightgbm as lgb
import numpy as np
from sklearn.metrics import mean_absolute_error
from loguru import logger
from typing import Dict, Tuple, Optional


def optimize_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    sample_weights: Optional[np.ndarray] = None,
    n_trials: int = 20,
    random_state: int = 42
) -> Tuple[Dict, optuna.Study]:
    """Optimize XGBoost hyperparameters using Bayesian optimization.

    Search space (following paper methodology):
    - learning_rate: [0.01, 0.3] (log scale)
    - max_depth: [3, 10]
    - n_estimators: [100, 1000]
    - subsample: [0.5, 1.0]
    - colsample_bytree: [0.5, 1.0]
    - reg_alpha: [0, 10] (L1 regularization)
    - reg_lambda: [0, 10] (L2 regularization)
    - min_child_weight: [1, 10]

    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        sample_weights: Optional sample weights for spatial similarity
        n_trials: Number of optimization trials (default: 20)
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (best_params dict, optuna Study object)

    Example:
        >>> best_params, study = optimize_xgboost(
        ...     X_train, y_train, X_val, y_val,
        ...     n_trials=20
        ... )
        >>> print(f"Best MAE: {study.best_value:.3f}")
        >>> print(f"Best params: {best_params}")
    """
    logger.info("Starting XGBoost hyperparameter optimization...")

    def objective(trial):
        """Optuna objective function."""
        params = {
            "objective": "reg:squarederror",
            "eval_metric": "mae",
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0, 10),
            "reg_lambda": trial.suggest_float("reg_lambda", 0, 10),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "random_state": random_state,
            "n_jobs": -1,
        }

        # Train model
        model = xgb.XGBRegressor(**params)
        model.fit(
            X_train,
            y_train,
            sample_weight=sample_weights,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=50,
            verbose=False
        )

        # Evaluate on validation set
        y_pred = model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)

        return mae

    # Create study
    study = optuna.create_study(
        direction="minimize",
        sampler=TPESampler(seed=random_state),
        pruner=MedianPruner(n_warmup_steps=5)
    )

    # Optimize
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    logger.info(f"Optimization complete. Best MAE: {study.best_value:.3f}")
    logger.info(f"Best parameters: {study.best_params}")

    return study.best_params, study


def optimize_catboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    sample_weights: Optional[np.ndarray] = None,
    n_trials: int = 20,
    random_state: int = 42
) -> Tuple[Dict, optuna.Study]:
    """Optimize CatBoost hyperparameters.

    Search space:
    - learning_rate: [0.01, 0.3]
    - depth: [4, 10]
    - iterations: [100, 1000]
    - l2_leaf_reg: [1, 10]
    - bagging_temperature: [0, 1]
    - random_strength: [0, 10]

    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        sample_weights: Optional sample weights
        n_trials: Number of optimization trials
        random_state: Random seed

    Returns:
        Tuple of (best_params, study)
    """
    logger.info("Starting CatBoost hyperparameter optimization...")

    def objective(trial):
        params = {
            "loss_function": "MAE",
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "depth": trial.suggest_int("depth", 4, 10),
            "iterations": trial.suggest_int("iterations", 100, 1000),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1, 10),
            "bagging_temperature": trial.suggest_float("bagging_temperature", 0, 1),
            "random_strength": trial.suggest_float("random_strength", 0, 10),
            "random_state": random_state,
            "verbose": False,
        }

        model = cb.CatBoostRegressor(**params)
        model.fit(
            X_train,
            y_train,
            sample_weight=sample_weights,
            eval_set=(X_val, y_val),
            early_stopping_rounds=50,
            verbose=False
        )

        y_pred = model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)

        return mae

    study = optuna.create_study(
        direction="minimize",
        sampler=TPESampler(seed=random_state),
        pruner=MedianPruner(n_warmup_steps=5)
    )

    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    logger.info(f"Optimization complete. Best MAE: {study.best_value:.3f}")

    return study.best_params, study


def optimize_lightgbm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    sample_weights: Optional[np.ndarray] = None,
    n_trials: int = 20,
    random_state: int = 42
) -> Tuple[Dict, optuna.Study]:
    """Optimize LightGBM hyperparameters.

    Search space:
    - learning_rate: [0.01, 0.3]
    - num_leaves: [20, 150]
    - n_estimators: [100, 1000]
    - subsample: [0.5, 1.0]
    - colsample_bytree: [0.5, 1.0]
    - reg_alpha: [0, 10]
    - reg_lambda: [0, 10]
    - min_child_weight: [1, 10]

    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        sample_weights: Optional sample weights
        n_trials: Number of optimization trials
        random_state: Random seed

    Returns:
        Tuple of (best_params, study)
    """
    logger.info("Starting LightGBM hyperparameter optimization...")

    def objective(trial):
        params = {
            "objective": "regression",
            "metric": "mae",
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 20, 150),
            "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0, 10),
            "reg_lambda": trial.suggest_float("reg_lambda", 0, 10),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "random_state": random_state,
            "n_jobs": -1,
            "verbose": -1,
        }

        model = lgb.LGBMRegressor(**params)
        model.fit(
            X_train,
            y_train,
            sample_weight=sample_weights,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)]
        )

        y_pred = model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)

        return mae

    study = optuna.create_study(
        direction="minimize",
        sampler=TPESampler(seed=random_state),
        pruner=MedianPruner(n_warmup_steps=5)
    )

    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    logger.info(f"Optimization complete. Best MAE: {study.best_value:.3f}")

    return study.best_params, study


if __name__ == "__main__":
    logger.info("Hyperparameter optimization module loaded")
