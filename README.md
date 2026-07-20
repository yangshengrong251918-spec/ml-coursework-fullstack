# YangShengRong_ChurnML - 客户流失预测系统

基于 TensorFlow 的客户流失预测系统，提供数据探索、模型训练、在线预测等功能。

## 环境要求

- Python 3.8+（推荐使用 conda 管理虚拟环境）
- Node.js 16+（推荐使用 nvm 管理版本）
- 操作系统：Windows 10/11

## 项目结构

```
YangShengRong_ChurnML/
│
├── backend/                              # 后端 Python 项目
│   ├── app.py                            # Flask 主应用
│   ├── config.py                         # 配置文件（超参数、路径等）
│   ├── requirements.txt                  # Python 依赖列表
│   ├── model/                            # 模型相关
│   │   ├── train.py                      # 模型训练脚本
│   │   ├── predict.py                    # 预测接口逻辑
│   │   └── utils.py                      # 数据预处理、特征工程、评估指标
│   ├── data/                             # 数据存放
│   │   └── churn_data.csv                # 模拟数据集（训练自动生成）
│   └── saved_models/                     # 训练好的模型文件
│       └── churn_model.h5
│
├── frontend/                             # Vue 2 前端项目（Vue CLI 2.0）
│   ├── build/                            # webpack 构建配置
│   ├── config/                           # 环境变量配置
│   ├── src/
│   │   ├── assets/                       # 静态资源
│   │   ├── components/                   # 功能组件
│   │   │   ├── EDACharts.vue             # 数据探索图表（热力图、分布图、箱线图）
│   │   │   ├── TrainControl.vue          # 训练控制面板
│   │   │   ├── TrainCurve.vue            # 训练曲线（损失/准确率）
│   │   │   ├── ModelEval.vue             # 评估指标与混淆矩阵、ROC 曲线
│   │   │   ├── FeatureImportance.vue     # 特征重要性图
│   │   │   ├── PredictForm.vue           # 在线预测表单 + 批量上传
│   │   │   └── PredictHistory.vue        # 预测历史记录
│   │   ├── views/
│   │   │   └── Dashboard.vue             # 主视图
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── utils/
│   │   │   └── api.js                    # 后端 API 调用封装
│   │   ├── App.vue
│   │   └── main.js
│   ├── static/
│   ├── .gitignore
│   ├── index.html
│   └── package.json
│
├── .gitignore
├── README.md
└── API对接文档.md
```

## 快速开始

### 1. 后端启动

```bash
# 创建 conda 虚拟环境
conda create -n YangShengRong_ChurnML python=3.8 -y
conda activate YangShengRong_ChurnML

# 安装依赖
cd backend
pip install -r requirements.txt

# 启动服务
python app.py
```

后端默认运行在 `http://localhost:5000`。

### 2. 前端启动

```bash
# 确保 Node.js 版本
nvm use 16

# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

前端默认运行在 `http://localhost:8080`，已配置代理到后端 5000 端口。

### 3. 使用流程

1. 打开浏览器访问 `http://localhost:8080`
2. 页面加载后，左侧"数据探索"区域会自动显示数据摘要、相关性热力图、目标分布和箱线图
3. 在"模型训练控制"面板设置参数（轮次、层数、激活函数、优化器），点击"开始训练"
4. 训练过程中可实时查看进度条和日志表格
5. 训练完成后，"训练曲线"区域显示损失/准确率曲线
6. "模型评估"区域展示准确率、精确率、召回率、F1 分数，以及混淆矩阵热力图和 ROC 曲线（含 AUC 值）
7. "特征重要性"展示各特征对预测结果的影响排序
8. 在"在线客户流失预测"中输入客户特征，点击"预测"获取流失概率和建议
9. 可切换到"批量预测"标签页，上传 CSV 文件批量预测并下载结果
10. 每次预测后，"预测历史记录"表格会更新

## 数据集说明

- 训练数据集为模拟生成的客户数据，共 5000 条样本，10 个特征 + 1 个目标列（Churn）
- 首次训练时自动生成并保存到 `backend/data/churn_data.csv`
- 流失率约 25%~30%，类别略有不平衡，符合真实业务场景

## API 接口文档

详见 [API对接文档.md](./API对接文档.md)，简要接口清单如下：

### 数据探索

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 数据摘要 | GET | /api/data/summary | 样本数、特征数、流失率、缺失值 |
| EDA 数据 | GET | /api/data/eda | 相关性矩阵、目标分布 |
| 箱线图 | GET | /api/data/boxplot | 按流失分组的特征统计数据 |

### 模型训练

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 启动训练 | POST | /api/train/start | 异步训练，返回状态 |
| 训练进度 | GET | /api/train/progress | 当前进度、日志、结果 |
| 训练曲线 | GET | /api/train/curves | Loss/Acc 历史数据 |

### 模型评估

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 评估结果 | GET | /api/evaluate | 指标、混淆矩阵、ROC |
| 特征重要性 | GET | /api/importance | Top 10 特征排序 |

### 预测

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 单条预测 | POST | /api/predict | 输入特征字典，返回概率和建议 |
| 批量预测 | POST | /api/predict/batch | 上传 CSV 文件，返回预测结果 |
| 预测历史 | GET | /api/predict/history | 获取当前会话的预测记录 |
| 导出结果 | GET | /api/predict/export | 导出预测结果到 CSV 文件 |

## 注意事项

- 首次训练自动生成模拟数据，无需外部数据文件
- 模型保存在 `backend/saved_models/churn_model.h5`
- Scaler 保存在 `backend/saved_models/scaler.pkl`
- 预测历史记录存储在服务端内存中，重启服务后清空
- 批量预测 CSV 需包含全部 10 个特征列（列名见 `config.py` 中的 `FEATURE_NAMES`）
- 训练接口为异步操作，启动后需轮询 `/api/train/progress` 获取结果
- 后端已通过 `flask-cors` 开启跨域支持（`frontend/src/utils/api.js` 中直接请求 `http://localhost:5000`），因此无需依赖 `config/index.js` 里的 proxyTable 配置
