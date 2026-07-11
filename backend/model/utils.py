# -*- coding: utf-8 -*-
# 工具函数：造模拟数据、预处理、算评估指标这些

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, roc_curve, auc
import sys
import os

# 把上级目录加到path里，好引入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FEATURE_NAMES, RANDOM_SEED

np.random.seed(RANDOM_SEED)


def generate_churn_data(n_samples=5000):
    """
    生成模拟客户数据。
    n_samples: 要生成多少条
    返回一个 DataFrame，特征列 + Churn 列
    """
    tenure = np.random.randint(1, 73, size=n_samples)
    monthly_charges = np.random.uniform(20, 120, size=n_samples)
    total_charges = tenure * monthly_charges * np.random.uniform(0.8, 1.2, size=n_samples)
    num_complaints = np.random.poisson(0.5, size=n_samples).astype(int)
    contract_encoded = np.random.choice([0, 1, 2], size=n_samples, p=[0.4, 0.3, 0.3])
    has_online_security = np.random.choice([0, 1], size=n_samples, p=[0.5, 0.5])
    has_tech_support = np.random.choice([0, 1], size=n_samples, p=[0.4, 0.6])
    paperless_billing = np.random.choice([0, 1], size=n_samples, p=[0.6, 0.4])
    age = np.random.randint(18, 71, size=n_samples)
    avg_monthly_gb = np.random.uniform(1, 50, size=n_samples)

    # 构造流失标签的逻辑：投诉多、在网短、月费高 -> 更容易流失
    score = (
        -0.3 * tenure +
        0.1 * monthly_charges +
        0.5 * num_complaints -
        0.4 * contract_encoded +
        0.2 * has_online_security +
        -0.1 * age +
        0.05 * avg_monthly_gb
    )
    score += np.random.normal(0, 0.5, size=n_samples)
    prob = 1 / (1 + np.exp(-score))
    churn = (prob > 0.5).astype(int)
    # 再补一点随机流失，让流失率在 25%~30% 左右
    churn = churn | (np.random.rand(n_samples) < 0.1)
    churn = churn.astype(int)

    data = pd.DataFrame({
        'tenure': tenure,
        'monthly_charges': monthly_charges,
        'total_charges': total_charges,
        'num_complaints': num_complaints,
        'contract_encoded': contract_encoded,
        'has_online_security': has_online_security,
        'has_tech_support': has_tech_support,
        'paperless_billing': paperless_billing,
        'age': age,
        'avg_monthly_gb': avg_monthly_gb,
        'Churn': churn
    })
    return data


def preprocess_data(df, scaler=None, fit_scaler=True):
    """
    标准化处理。
    df: 数据框
    scaler: 如果传进来就用它 transform，否则 fit 一个新的
    fit_scaler: 是否要拟合新 scaler
    返回 X, y, scaler
    """
    X = df[FEATURE_NAMES].values
    y = df['Churn'].values if 'Churn' in df.columns else None

    if fit_scaler:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = scaler.transform(X)

    return X_scaled, y, scaler


def get_train_test_data(n_samples=5000):
    """生成数据并划分训练集测试集，返回 (X_train, X_test, y_train, y_test, scaler)"""
    df = generate_churn_data(n_samples)
    X_scaled, y, scaler = preprocess_data(df, fit_scaler=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    return X_train, X_test, y_train, y_test, scaler


# ---------- 以下是需求文档新增的评估功能 ----------

def calc_confusion_matrix_data(y_true, y_pred):
    """
    算混淆矩阵，返回一个 2x2 的列表，方便前端直接渲染
    """
    cm = confusion_matrix(y_true, y_pred)
    # 转成带标签的格式，前端好画热力图
    return {
        "matrix": cm.tolist(),
        "labels": ["未流失(0)", "流失(1)"]
    }


def calc_roc_data(y_true, y_pred_prob):
    """
    算 ROC 曲线需要的 FPR, TPR, 阈值，还有 AUC 值
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_prob)
    roc_auc = auc(fpr, tpr)
    return {
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist(),
        "auc": float(roc_auc)
    }


def calc_boxplot_data(df):
    """
    按 Churn 分组，算几个关键特征的统计量，前端画箱线图用。
    返回格式：{ feature_name: { "0": [min, q1, median, q3, max], "1": [...] } }
    """
    # 选几个有代表性的特征
    key_features = ['tenure', 'monthly_charges', 'num_complaints', 'age', 'avg_monthly_gb']
    result = {}
    for feat in key_features:
        groups = {}
        for label in [0, 1]:
            vals = df[df['Churn'] == label][feat].values
            if len(vals) > 0:
                groups[str(label)] = [
                    float(np.min(vals)),
                    float(np.percentile(vals, 25)),
                    float(np.median(vals)),
                    float(np.percentile(vals, 75)),
                    float(np.max(vals))
                ]
            else:
                groups[str(label)] = [0, 0, 0, 0, 0]
        result[feat] = groups
    return result


def get_feature_importance_simple(model, X_test, y_test, feature_names=None):
    """
    用 permutation importance 的简化版算特征重要性。
    就是随机打乱某个特征列，看模型准确率下降多少。
    下降越多 -> 这个特征越重要。
    """
    if feature_names is None:
        feature_names = FEATURE_NAMES

    # 先算基准准确率
    y_pred = (model.predict(X_test, verbose=0) > 0.5).astype(int)
    baseline = np.mean(y_pred.flatten() == y_test)

    importances = []
    for i in range(X_test.shape[1]):
        X_perm = X_test.copy()
        np.random.shuffle(X_perm[:, i])
        y_pred_perm = (model.predict(X_perm, verbose=0) > 0.5).astype(int)
        score = np.mean(y_pred_perm.flatten() == y_test)
        drop = baseline - score
        importances.append({
            "feature": feature_names[i],
            "importance": float(max(0, drop * 100))  # 转成百分比好看点
        })

    importances.sort(key=lambda x: x["importance"], reverse=True)
    return importances
