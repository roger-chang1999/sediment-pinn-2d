---
type: paper
title: "Challenges in Training PINNs: A Loss Landscape Perspective"
authors: P. Rathore, W. Lei, Z. Frangella, L. Lu, M. Udell
venue: ICML 2024
source: 依既有知識整理，未在本專案中重讀全文
related: [../ideas/004-lbfgs-curvature-not-sampling.md, ../ideas/006-training-improvements-five-directions.md]
---

# Rathore et al. (2024)：PINN 訓練困難來自 loss 地形病態

## 核心
- PINN loss 中的微分算子造成 **ill-conditioning**（Hessian 條件數很大），是訓練困難的主因之一。
- 比較 Adam、L-BFGS、Adam + L-BFGS：**Adam + L-BFGS 優於任一單獨使用**。
- 提出在 Adam + L-BFGS 之後再接 NysNewton-CG（NNCG），進一步降低 loss。
- 測試題包含 convection、reaction、wave 等。

## 和我們的關係
- 直接支持 [idea 004](../ideas/004-lbfgs-curvature-not-sampling.md)：L-BFGS 有效是因為修正了曲率，不是修正抽樣。
- 我們 P0 的觀察（Adam 73% → L-BFGS 2.6%）和這篇的結論方向一致。
- NNCG 是 [idea 006](../ideas/006-training-improvements-five-directions.md) 第 5 項的候選之一。

## 不可比之處
- 測試題是一維 + 時間的標準題，我們是二維 + 時間、帶沉降匯項的平流–擴散。
- 網路大小、配點數不同，誤差數值不可直接比。
