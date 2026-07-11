// API 封装 — 所有后端接口都在这

import axios from 'axios'

const BASE_URL = 'http://localhost:5000/api'

// -------- 数据探索 --------

export function getDataSummary() {
  return axios.get(`${BASE_URL}/data/summary`)
}

export function getEdaData() {
  return axios.get(`${BASE_URL}/data/eda`)
}

export function getBoxplotData() {
  return axios.get(`${BASE_URL}/data/boxplot`)
}

// -------- 训练 --------

export function startTraining(params) {
  return axios.post(`${BASE_URL}/train/start`, params)
}

export function getTrainProgress() {
  return axios.get(`${BASE_URL}/train/progress`)
}

export function getTrainCurves() {
  return axios.get(`${BASE_URL}/train/curves`)
}

// -------- 评估 --------

export function getEvaluate() {
  return axios.get(`${BASE_URL}/evaluate`)
}

export function getImportance() {
  return axios.get(`${BASE_URL}/importance`)
}

// -------- 预测 --------

export function predict(data) {
  return axios.post(`${BASE_URL}/predict`, data)
}

export function predictBatch(file) {
  const formData = new FormData()
  formData.append('file', file)
  return axios.post(`${BASE_URL}/predict/batch`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getPredictHistory() {
  return axios.get(`${BASE_URL}/predict/history`)
}

export function exportResults() {
  return axios.get(`${BASE_URL}/predict/export`)
}
