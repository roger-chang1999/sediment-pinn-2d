---
type: paper
title: "Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations"
authors: M. Raissi, P. Perdikaris, G. E. Karniadakis
venue: Journal of Computational Physics, 378, 686–707 (2019)
doi: 10.1016/j.jcp.2018.10.045
source: 依既有知識整理，未在本專案中重讀全文
related: [../ideas/001-origin-ssc-pinn-on-srh2d-hydraulics.md, ../ideas/005-inverse-as-calibration-and-statistics.md]
---

# Raissi et al. (2019)：PINN 原始論文

## 核心
把 PDE 殘差、初始和邊界條件寫進神經網路的 loss，用自動微分計算導數。同一個框架同時處理：
- **forward**（資料驅動的 PDE 求解）
- **inverse**（從資料辨識 PDE 參數），例如從圓柱繞流的速度資料反推 NS 方程中的係數，以及推出壓力場

## 和我們的關係
- 我們的 forward / inverse 兩種模式（[idea 005](../ideas/005-inverse-as-calibration-and-statistics.md)）直接沿用這篇的定義。
- 這篇常用 tanh MLP + L-BFGS，我們的 Adam → L-BFGS 兩階段是之後文獻常見的做法。

## 不可比之處
- 測試題（Burgers、Schrödinger、NS 圓柱繞流等）是平滑或週期性問題，不是平流主導的泥砂輸運。
- 沒有處理傳播失敗、平凡解這類後來才被系統研究的訓練問題。
