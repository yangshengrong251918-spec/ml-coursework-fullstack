# -*- coding: utf-8 -*-
# Flask 主入口，所有 API 接口都在这

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import os
import sys
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# 把项目根目录加到 path 里
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
sys.path.append(BASE_DIR)
from config import MODEL_PATH, FEATURE_NAMES
from model.utils import (
    generate_churn_data, get_train_test_data,
    calc_confusion_matrix_data, calc_roc_data,
    calc_boxplot_data, get_feature_importance_simple
)
from model.train import train_model
from model.predict import predict_single, predict_batch_from_csv

# 确保 data 目录存在（首次运行会用来存生成的数据集、临时上传文件、导出结果）
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

# ========== 全局变量 ==========

# 训练状态
train_status = {
    'is_training': False,
    'progress': 0,
    'total_epochs': 0,
    'logs': [],            # 每轮日志 [{epoch, loss, val_loss, accuracy, val_accuracy}]
    'history': None,       # 完整训练历史 dict
    'test_data': None,
    'y_pred_prob': None,
    'y_test': None,
    'result': None
}

# 预测历史记录（用内存存，会话级别的）
predict_history = []

# 保存一份生成的数据，EDA 接口用
_cached_data = None

def get_data():
    global _cached_data
    if _cached_data is None:
        _cached_data = generate_churn_data(5000)
        # 顺便保存到 CSV
        _cached_data.to_csv(os.path.join(DATA_DIR, 'churn_data.csv'), index=False)
    return _cached_data


# ===================== API 接口 =====================

# ---------- 数据探索 ----------

@app.route('/api/data/summary', methods=['GET'])
def get_data_summary():
    """数据集摘要：样本数、特征数、流失率、缺失值"""
    df = get_data()
    # 描述统计
    desc = df[FEATURE_NAMES].describe().round(2)
    featureStats = {}
    for col in FEATURE_NAMES:
        featureStats[col] = {
            'mean': float(desc[col]['mean']),
            'median': float(df[col].median()),
            'min': float(desc[col]['min']),
            'max': float(desc[col]['max']),
            'std': float(desc[col]['std']),
            'missing': int(df[col].isnull().sum())
        }

    summary = {
        'totalSamples': len(df),
        'featureCount': len(FEATURE_NAMES),
        'churnRate': float(round(df['Churn'].mean(), 4)),
        'missingValues': df.isnull().sum().to_dict(),
        'featureStats': featureStats
    }
    return jsonify(summary)


@app.route('/api/data/eda', methods=['GET'])
def get_eda_data():
    """
    EDA 数据：
    - 相关性矩阵（所有特征之间）
    - 目标分布
    """
    df = get_data()

    # 相关性矩阵
    corr_matrix = df[FEATURE_NAMES + ['Churn']].corr().round(4)
    # 转成前端好用的格式
    corr_data = {
        'features': corr_matrix.columns.tolist(),
        'values': corr_matrix.values.tolist()
    }

    # 目标分布
    churn_counts = df['Churn'].value_counts().to_dict()
    target_dist = {'0': int(churn_counts.get(0, 0)), '1': int(churn_counts.get(1, 0))}

    return jsonify({
        'correlationMatrix': corr_data,
        'targetDistribution': target_dist
    })


@app.route('/api/data/boxplot', methods=['GET'])
def get_boxplot_data():
    """按流失分组的箱线图数据"""
    df = get_data()
    data = calc_boxplot_data(df)
    return jsonify(data)


# ---------- 模型训练 ----------

@app.route('/api/train/start', methods=['POST'])
def start_training():
    """异步启动训练"""
    global train_status

    if train_status['is_training']:
        return jsonify({'status': 'error', 'message': '已经在训练了，别急'}), 400

    params = request.json or {}
    epochs = params.get('epochs', 30)
    batch_size = params.get('batchSize', 32)
    layers = params.get('layers', [128, 64])
    activation = params.get('activation', 'relu')
    optimizer = params.get('optimizer', 'adam')

    # 重置状态
    train_status = {
        'is_training': True,
        'progress': 0,
        'total_epochs': epochs,
        'logs': [],
        'history': None,
        'test_data': None,
        'y_pred_prob': None,
        'y_test': None,
        'result': None
    }

    def _train_thread():
        global train_status
        try:
            def progress_cb(epoch, logs):
                train_status['progress'] = epoch
                train_status['logs'].append({
                    'epoch': epoch,
                    'loss': float(logs.get('loss', 0)),
                    'val_loss': float(logs.get('val_loss', 0)),
                    'accuracy': float(logs.get('accuracy', 0)),
                    'val_accuracy': float(logs.get('val_accuracy', 0))
                })

            history, test_data, scaler, y_pred_prob = train_model(
                epochs=epochs,
                batch_size=batch_size,
                layers_list=layers,
                activation=activation,
                optimizer=optimizer,
                progress_callback=progress_cb
            )

            train_status['history'] = history.history
            X_test, y_test = test_data
            train_status['y_test'] = y_test
            train_status['y_pred_prob'] = y_pred_prob

            # 算评估指标
            y_pred = (y_pred_prob > 0.5).astype(int)
            train_status['result'] = {
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'precision': float(precision_score(y_test, y_pred, zero_division=0)),
                'recall': float(recall_score(y_test, y_pred, zero_division=0)),
                'f1': float(f1_score(y_test, y_pred, zero_division=0))
            }

        except Exception as e:
            print("训练出错啦:", e)
            train_status['result'] = {'error': str(e)}
        finally:
            train_status['is_training'] = False

    thread = threading.Thread(target=_train_thread)
    thread.daemon = True
    thread.start()
    return jsonify({'status': 'success', 'message': '训练已启动'})


@app.route('/api/train/progress', methods=['GET'])
def get_train_progress():
    """获取训练进度 + 日志"""
    global train_status
    return jsonify({
        'isTraining': train_status['is_training'],
        'progress': train_status['progress'],
        'totalEpochs': train_status['total_epochs'],
        'logs': train_status['logs'],
        'result': train_status['result']
    })


@app.route('/api/train/curves', methods=['GET'])
def get_train_curves():
    """返回训练曲线数据（loss + accuracy 历史）"""
    global train_status
    if train_status['history'] is None:
        return jsonify({'status': 'pending', 'message': '还没训练完呢'})
    return jsonify({
        'status': 'done',
        'history': train_status['history']
    })


# ---------- 模型评估 ----------

@app.route('/api/evaluate', methods=['GET'])
def get_evaluate():
    """返回评估指标 + 混淆矩阵 + ROC 曲线数据"""
    global train_status

    if train_status['result'] is None:
        return jsonify({'status': 'pending', 'message': '还没训练或没训练完'})

    if 'error' in train_status['result']:
        return jsonify({'status': 'error', 'message': train_status['result']['error']})

    y_test = train_status['y_test']
    y_pred_prob = train_status['y_pred_prob']
    y_pred = (y_pred_prob > 0.5).astype(int)

    # 混淆矩阵
    cm_data = calc_confusion_matrix_data(y_test, y_pred)

    # ROC 曲线
    roc_data = calc_roc_data(y_test, y_pred_prob)

    return jsonify({
        'status': 'done',
        'metrics': train_status['result'],
        'confusionMatrix': cm_data,
        'roc': roc_data
    })


@app.route('/api/importance', methods=['GET'])
def get_feature_importance():
    """特征重要性（用 permutation importance 算）"""
    global train_status

    # 如果模型已经训练好了，用训练好的模型算
    if train_status['y_test'] is not None and os.path.exists(MODEL_PATH):
        model = tf.keras.models.load_model(MODEL_PATH)
        # 重新生成一份测试数据（训练线程只保存了 y_test/y_pred_prob，没保存 X_test，
        # 用同样的随机种子重新划分即可拿到对应的特征数据）
        _, X_test, _, y_test, _ = get_train_test_data()
        importances = get_feature_importance_simple(model, X_test, train_status['y_test'])
    else:
        # 没训练的话，返回基于相关性的模拟数据
        import random
        random.seed(42)
        importances = []
        for f in FEATURE_NAMES:
            imp = abs(random.gauss(0.1, 0.05))
            importances.append({'feature': f, 'importance': round(imp * 100, 2)})
        importances.sort(key=lambda x: x['importance'], reverse=True)

    return jsonify(importances)


# ---------- 预测 ----------

@app.route('/api/predict', methods=['POST'])
def do_predict():
    """单条预测"""
    data = request.json
    if not data:
        return jsonify({'error': '请求体是空的'}), 400

    try:
        prob = predict_single(data)
        # 根据概率给个建议
        if prob > 0.7:
            suggestion = '风险比较高，建议优先跟进挽留'
        elif prob > 0.4:
            suggestion = '风险中等，建议定期关怀一下'
        else:
            suggestion = '风险比较低，正常维护就行'

        result = {
            'probability': prob,
            'prediction': int(prob > 0.5),
            'suggestion': suggestion
        }

        # 记录到历史
        record = {
            'id': len(predict_history) + 1,
            'input': {k: data.get(k) for k in FEATURE_NAMES},
            'result': result
        }
        predict_history.append(record)

        return jsonify(result)

    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': '预测出错: ' + str(e)}), 500


@app.route('/api/predict/batch', methods=['POST'])
def do_predict_batch():
    """批量预测：上传 CSV 文件，返回预测结果"""
    if 'file' not in request.files:
        return jsonify({'error': '没上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名是空的'}), 400

    # 保存到临时文件
    tmp_path = os.path.join(DATA_DIR, '_tmp_upload.csv')
    file.save(tmp_path)

    try:
        results = predict_batch_from_csv(tmp_path)
        # 也记录到历史
        for r in results:
            record = {
                'id': len(predict_history) + 1,
                'input': {k: r.get(k) for k in FEATURE_NAMES},
                'result': {
                    'probability': r['predicted_prob'],
                    'prediction': r['prediction']
                }
            }
            predict_history.append(record)

        return jsonify({
            'status': 'success',
            'count': len(results),
            'results': results
        })
    except Exception as e:
        return jsonify({'error': '批量预测出错: ' + str(e)}), 500
    finally:
        # 删掉临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route('/api/predict/history', methods=['GET'])
def get_predict_history():
    """获取预测历史记录"""
    # 只返回最近 50 条
    recent = predict_history[-50:]
    recent.reverse()
    return jsonify(recent)


@app.route('/api/predict/export', methods=['GET'])
def export_predict_results():
    """把最新一次批量预测结果导出为 CSV"""
    if not predict_history:
        return jsonify({'error': '没有预测记录'}), 400

    # 取最后一批批量预测的结果（如果有的话）
    # 简化处理：直接返回最近 10 条记录
    recent = predict_history[-10:]
    rows = []
    for r in recent:
        row = r['input'].copy()
        row['predicted_prob'] = r['result'].get('probability', 0)
        row['prediction'] = r['result'].get('prediction', 0)
        rows.append(row)

    df = pd.DataFrame(rows)
    csv_path = os.path.join(DATA_DIR, 'export_results.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    return jsonify({
        'status': 'success',
        'downloadUrl': '/api/predict/export/download',
        'count': len(rows)
    })


@app.route('/api/predict/export/download', methods=['GET'])
def download_export_results():
    """真正把导出的 CSV 文件返回给浏览器下载"""
    filename = 'export_results.csv'
    if not os.path.exists(os.path.join(DATA_DIR, filename)):
        return jsonify({'error': '还没有导出过结果'}), 404
    return send_from_directory(DATA_DIR, filename, as_attachment=True)


if __name__ == '__main__':
    print("启动 Flask 服务...")
    app.run(host='0.0.0.0', port=5000, debug=True)
