# -*- coding: utf-8 -*-
# 配置文件 — 存放路径、超参数、特征列名这些

import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 模型保存
MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "churn_model.h5")
SCALER_PATH = os.path.join(BASE_DIR, "saved_models", "scaler.pkl")

# 数据文件
DATA_PATH = os.path.join(BASE_DIR, "data", "churn_data.csv")

# 训练默认参数
DEFAULT_EPOCHS = 30
DEFAULT_BATCH_SIZE = 32
DEFAULT_LAYERS = [128, 64]     # 两层隐藏层
DEFAULT_ACTIVATION = 'relu'
DEFAULT_OPTIMIZER = 'adam'

# 特征列名（顺序固定，训练和预测时都用这个顺序）
FEATURE_NAMES = [
    'tenure', 'monthly_charges', 'total_charges', 'num_complaints',
    'contract_encoded', 'has_online_security', 'has_tech_support',
    'paperless_billing', 'age', 'avg_monthly_gb'
]

# 随机种子，固定下来方便复现
RANDOM_SEED = 42
