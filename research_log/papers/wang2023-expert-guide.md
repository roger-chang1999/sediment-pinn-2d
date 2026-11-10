---
type: paper
title: "An Expert's Guide to Training Physics-informed Neural Networks"
authors: S. Wang, S. Sankaran, H. Wang, P. Perdikaris
venue: arXiv 2308.08468 (2023)
source: 部分讀過全文（2026-11-08，子代理逐字讀取 arXiv HTML 的 Algorithm 1、Eq. 2.9–2.16、Sec. 5.2、6.1、7；benchmark 迭代數只有摘要轉述）
related: [../experiments/exp-p0-training-improvements-ablation.md, wang2021-gradient-pathologies.md]
---

# Wang et al. (2023)：PINN 訓練實務指南

## 核心（逐字核對過的部分）
- 梯度範數權重 Eq. 2.12–2.14：λ̂_k = (Σ_j ‖∇L_j‖) / ‖∇L_k‖，對 ic、bc、r **全部**加權（殘差也有權重）。
- 移動平均 Eq. 2.15：λ_new = α λ_old + (1−α) λ̂_new（α 乘在**舊**值上），預設 f=1000、α=0.9；權重 stop-gradient。
- 也提供 NTK 版本（較穩定但較貴）；文中建議先用梯度版。
- 優化：Adam lr 1e-3 指數衰減；「不建議使用 weight decay，尤其是正問題」。文中沒有 L-BFGS、沒有反問題。

## 和我們的關係
- 我們的 `--weighting gradnorm` 就是這個公式（λ 套在 pde、ic、bc、obs 四項），但更新頻率是每 100 步（原文預設 1000），由 Claude 預設未經討論。
- 它讓我們的 P0 反算 K 3/3 回收，成為新基準（[exp-p0-training-improvements-ablation](../experiments/exp-p0-training-improvements-ablation.md)）。

## 不可比之處
- 原文 benchmark 都是正問題、無雜訊觀測；我們用在帶 5% 雜訊觀測的反問題，且加了 obs 項。
- 原文提到梯度權重在 mini-batch 下「較不穩定」，我們沒有特別檢查。
