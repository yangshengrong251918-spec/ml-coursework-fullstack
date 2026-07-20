# API 对接文档

## 基本信息

- **Base URL**: `http://localhost:5000/api`
- **请求格式**: JSON (除批量预测接口使用 `multipart/form-data`)
- **响应格式**: JSON
- **跨域**: 已启用 CORS

---

## 1. 数据探索接口

### GET /api/data/summary

获取数据集摘要统计。

**响应示例：**
```json
{
  "totalSamples": 5000,
  "featureCount": 10,
  "churnRate": 0.273,
  "missingValues": {
    "tenure": 0,
    "monthly_charges": 0
  }
}
```

### GET /api/data/eda

获取 EDA 图表数据。

**响应示例：**
```json
{
  "correlationMatrix": {
    "features": ["tenure", "monthly_charges", "Churn"],
    "values": [[1.0, 0.1, -0.3], [0.1, 1.0, 0.2]]
  },
  "targetDistribution": {
    "0": 3635,
    "1": 1365
  }
}
```

### GET /api/data/boxplot

获取箱线图分组统计数据。

**响应示例：**
```json
{
  "tenure": {
    "0": [1, 20, 36, 55, 72],
    "1": [1, 8, 18, 35, 72]
  }
}
```

---

## 2. 模型训练接口

### POST /api/train/start

启动异步训练任务。

**请求参数：**
```json
{
  "epochs": 30,
  "batchSize": 32,
  "layers": [128, 64],
  "activation": "relu",
  "optimizer": "adam"
}
```

**参数说明：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| epochs | int | 30 | 训练轮次，范围 5~200 |
| batchSize | int | 32 | 批次大小 |
| layers | array | [128, 64] | 隐藏层神经元数 |
| activation | string | "relu" | 激活函数，可选 relu/tanh |
| optimizer | string | "adam" | 优化器，可选 adam/rmsprop |

**响应：**
```json
{
  "status": "success",
  "message": "训练已启动"
}
```

### GET /api/train/progress

获取训练进度和日志。

**响应示例：**
```json
{
  "isTraining": false,
  "progress": 30,
  "totalEpochs": 30,
  "logs": [
    {"epoch": 1, "loss": 0.693, "val_loss": 0.672, "accuracy": 0.72, "val_accuracy": 0.74}
  ],
  "result": {
    "accuracy": 0.89,
    "precision": 0.85,
    "recall": 0.78,
    "f1": 0.81
  }
}
```

### GET /api/train/curves

获取训练曲线数据。

**响应示例：**
```json
{
  "status": "done",
  "history": {
    "loss": [0.693, 0.512, 0.423],
    "val_loss": [0.672, 0.503, 0.418],
    "accuracy": [0.72, 0.80, 0.85],
    "val_accuracy": [0.74, 0.81, 0.86]
  }
}
```

---

## 3. 模型评估接口

### GET /api/evaluate

获取评估结果，含混淆矩阵和 ROC 曲线数据。

**响应示例：**
```json
{
  "status": "done",
  "metrics": {
    "accuracy": 0.89,
    "precision": 0.85,
    "recall": 0.78,
    "f1": 0.81
  },
  "confusionMatrix": {
    "matrix": [[700, 50], [80, 170]],
    "labels": ["未流失(0)", "流失(1)"]
  },
  "roc": {
    "fpr": [0.0, 0.1, 0.5, 1.0],
    "tpr": [0.0, 0.6, 0.9, 1.0],
    "thresholds": [1.0, 0.8, 0.5, 0.0],
    "auc": 0.93
  }
}
```

### GET /api/importance

获取特征重要性排序。

**响应示例：**
```json
[
  {"feature": "num_complaints", "importance": 8.5},
  {"feature": "tenure", "importance": 6.2}
]
```

---

## 4. 预测接口

### POST /api/predict

单条客户流失预测。

**请求示例：**
```json
{
  "tenure": 12,
  "monthly_charges": 65.5,
  "total_charges": 780,
  "num_complaints": 2,
  "contract_encoded": 0,
  "has_online_security": 0,
  "has_tech_support": 0,
  "paperless_billing": 1,
  "age": 32,
  "avg_monthly_gb": 15
}
```

**响应示例：**
```json
{
  "probability": 0.73,
  "prediction": 1,
  "suggestion": "风险比较高，建议优先跟进挽留"
}
```

### POST /api/predict/batch

批量预测（上传 CSV 文件）。

**请求格式：** `multipart/form-data`，字段名 `file`

**CSV 格式要求：**
- 必须包含所有特征列（共 10 列）
- 列名：tenure, monthly_charges, total_charges, num_complaints, contract_encoded, has_online_security, has_tech_support, paperless_billing, age, avg_monthly_gb
- 可选包含其他列，会被忽略

**响应示例：**
```json
{
  "status": "success",
  "count": 100,
  "results": [
    {
      "tenure": 12,
      "monthly_charges": 65.5,
      "num_complaints": 2,
      "contract_encoded": 0,
      "has_online_security": 0,
      "has_tech_support": 0,
      "paperless_billing": 1,
      "age": 32,
      "avg_monthly_gb": 15,
      "predicted_prob": 0.73,
      "prediction": 1
    }
  ]
}
```

### GET /api/predict/history

获取预测历史记录（最近 50 条）。

**响应示例：**
```json
[
  {
    "id": 1,
    "input": {"tenure": 12, "monthly_charges": 65.5},
    "result": {"probability": 0.73, "prediction": 1, "suggestion": "..."}
  }
]
```

### GET /api/predict/export

把最近的预测结果整理成 CSV，保存到服务端 `backend/data/export_results.csv`。

**响应示例：**
```json
{
  "status": "success",
  "downloadUrl": "/api/predict/export/download",
  "count": 10
}
```

### GET /api/predict/export/download

配合上面的接口使用，返回 `downloadUrl` 对应的 CSV 文件流（`Content-Disposition: attachment`），前端拿到后用 Blob 触发浏览器下载。若还没调用过 `/api/predict/export`，返回 404。

---

## 注意事项

1. 训练接口是异步的，调用后需轮询 `/api/train/progress` 获取结果
2. 模型未训练时调用预测接口会返回 400 错误
3. 所有时间相关的数据（在网时长等）单位均为"月"
4. 批量预测的 CSV 文件编码建议使用 UTF-8
