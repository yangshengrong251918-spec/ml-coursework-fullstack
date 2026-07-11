# -*- coding: utf-8 -*-
# TensorFlow 模型训练模块
# 构建神经网络、训练、保存模型

import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
import numpy as np
import os
import sys
import pickle

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_PATH, SCALER_PATH, DEFAULT_EPOCHS, DEFAULT_BATCH_SIZE
from model.utils import get_train_test_data


# 确保保存目录存在
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)


def build_model(layers_list=[128, 64], activation='relu', optimizer='adam'):
    """
    构建神经网络。
    layers_list: 每层神经元数，比如 [128, 64] 就是两个隐藏层
    activation: 激活函数
    optimizer: 优化器
    """
    model = models.Sequential()

    # 输入层 + 第一隐藏层（输入特征 10 个）
    model.add(layers.Dense(layers_list[0], activation=activation, input_shape=(10,)))
    model.add(layers.Dropout(0.2))

    # 中间的隐藏层
    for units in layers_list[1:]:
        model.add(layers.Dense(units, activation=activation))
        model.add(layers.Dropout(0.2))

    # 输出层，二分类用 sigmoid
    model.add(layers.Dense(1, activation='sigmoid'))

    model.compile(
        optimizer=optimizer,
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model


def train_model(epochs=DEFAULT_EPOCHS, batch_size=DEFAULT_BATCH_SIZE,
                layers_list=[128, 64], activation='relu', optimizer='adam',
                progress_callback=None):
    """
    执行训练。
    progress_callback: 可选，每轮结束后调用，参数 (epoch, logs)
    返回 (history, (X_test, y_test), scaler, y_pred_prob)
    """
    # 拿数据
    X_train, X_test, y_train, y_test, scaler = get_train_test_data()

    # 建模型
    model = build_model(layers_list, activation, optimizer)

    # 自定义回调，把进度传出去
    class ProgressCallback(callbacks.Callback):
        def on_epoch_end(self, epoch, logs=None):
            if progress_callback:
                progress_callback(epoch + 1, logs)

    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=batch_size,
        verbose=0,
        callbacks=[ProgressCallback()]
    )

    # 保存模型
    model.save(MODEL_PATH)
    print(f"模型已保存到 {MODEL_PATH}")

    # 保存 scaler
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"Scaler 已保存到 {SCALER_PATH}")

    # 预测概率，评估要用
    y_pred_prob = model.predict(X_test, verbose=0).flatten()

    return history, (X_test, y_test), scaler, y_pred_prob
