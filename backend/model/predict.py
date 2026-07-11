# -*- coding: utf-8 -*-
# 预测模块 — 加载模型，单条预测、批量预测

import tensorflow as tf
import numpy as np
import pandas as pd
import pickle
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_PATH, SCALER_PATH, FEATURE_NAMES


_model = None
_scaler = None


def load_model_and_scaler():
    """
    懒加载模型和 scaler。
    第一次调用的时候才从硬盘加载，后面直接用缓存的。
    """
    global _model, _scaler

    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"模型文件没找到，先训练再预测: {MODEL_PATH}")
        _model = tf.keras.models.load_model(MODEL_PATH)
        print("模型加载成功")

    if _scaler is None:
        if not os.path.exists(SCALER_PATH):
            raise FileNotFoundError(f"Scaler 文件没找到: {SCALER_PATH}")
        with open(SCALER_PATH, 'rb') as f:
            _scaler = pickle.load(f)
        print("Scaler 加载成功")

    return _model, _scaler


def predict_single(features_dict):
    """
    输入一个字典 {特征名: 值}，返回流失概率 (0~1 的 float)。
    """
    model, scaler = load_model_and_scaler()

    # 按 FEATURE_NAMES 的顺序构造输入向量
    try:
        input_array = np.array([[features_dict[name] for name in FEATURE_NAMES]])
    except KeyError as e:
        raise ValueError(f"缺了特征: {e}")

    input_scaled = scaler.transform(input_array)
    prob = model.predict(input_scaled, verbose=0)[0][0]
    return float(prob)


def predict_batch_from_csv(csv_path):
    """
    读取 CSV 文件，批量预测。
    CSV 必须包含 FEATURE_NAMES 里所有的列。
    返回 [{特征..., 预测概率}]
    """
    df = pd.read_csv(csv_path)

    # 检查有没有缺列
    missing = [col for col in FEATURE_NAMES if col not in df.columns]
    if missing:
        raise ValueError(f"CSV 缺少以下列: {missing}")

    model, scaler = load_model_and_scaler()

    X = df[FEATURE_NAMES].values
    X_scaled = scaler.transform(X)
    probs = model.predict(X_scaled, verbose=0).flatten()

    results = []
    for i in range(len(df)):
        row = df.iloc[i]
        record = {col: row[col] for col in FEATURE_NAMES}
        record['predicted_prob'] = float(probs[i])
        record['prediction'] = int(probs[i] > 0.5)
        results.append(record)

    return results
