---
type: paper
title: "Gradient Alignment in Physics-informed Neural Networks: A Second-Order Optimization Perspective"
authors: S. Wang 等（Perdikaris 團隊）
venue: NeurIPS 2025；arXiv 2502.00604
url: https://arxiv.org/html/2502.00604v2
source: 已讀全文（2026-11-08，子代理逐字讀取 arXiv HTML v2；附錄 A–E 只有摘要轉述）
related: [../ideas/004-lbfgs-curvature-not-sampling.md, ../ideas/006-training-improvements-five-directions.md]
---

# Wang et al. (2025)：梯度對齊與 SOAP

## 核心（依摘要）
- 多項 loss 的**梯度方向互相衝突**，拖慢 PINN 訓練。
- 準二階方法透過隱式的預條件（preconditioning）讓梯度對齊；文中特別推薦 **SOAP**（Vyas et al. 2024，結合 Shampoo 和 Adam），並把它和牛頓法連結。
- 在 10 個 PDE 基準上報告 2–10 倍的精度提升，包含 Reynolds 數到 10,000 的紊流。

## 和我們的關係
- [idea 006](../ideas/006-training-improvements-five-directions.md) 第 4 項：用 SOAP 取代 Adam。
- 與 [idea 004](../ideas/004-lbfgs-curvature-not-sampling.md) 的「病態地形」論點一致。

## 實作要注意
- SOAP 原始實作在 SOAP 作者（Vyas et al.）的公開 repo，是單一 PyTorch 檔案；不在 PyPI 上。引入外部程式碼前要先讀過。
- 超參數（預條件更新頻率、β）要記錄在實驗中。

## 不可比之處
- 「2–10 倍」是相對於他們自己的基準設定，和我們的 P0 沒有直接對應。

## 全文核對（2026-11-08）
- 設定：PirateNet（3 個殘差區塊、width 256）、lr 1e-3 warmup 5000 步後指數衰減、每步 8192 配點；**搭配 gradnorm（每 1000 步）與因果訓練**；SOAP β=(0.99, 0.999)、preconditioning frequency 2。
- **沒有反問題**實驗；Table 3 的「Adam+L-BFGS」欄與 Baselines 段落「排除 L-BFGS」互相矛盾。
- 計算成本：文中稱約 2 倍，Table 7 的比值約 1.1–3.9 倍。幾處倍數宣稱與表格對不上（AC、LDC、GL、RT）。
- SOAP 原始論文（2409.11321）：L、R 以 β2 的 EMA 累積；特徵基底每 f 步用一次 power iteration + QR（首次用 eigh）；1D 參數用 AdamW；第一步就更新參數。
- **與我們不可比**：我們是簡化版 SOAP（第一步不更新、freq 10、預設 betas、純 MLP、固定權重）。
