---
type: paper
title: "Leveraging Physics-Informed Neural Networks for Efficient Modelling of Coastal Ecosystems Dynamics: A Case Study of Sundarbans Mangrove Forest"
authors: M. Fanous, J. M. Eden, J. Yang, S. See, V. Palade, A. Daneshkhah
venue: Ecological Informatics, 90, 103302 (2025)；CC BY-NC
doi: 10.1016/j.ecoinf.2025.103302
pdf: data/papers/fanous2025-sundarbans-pinn.pdf（本機，不進版控）
source: 部分讀過全文（2026-11-08，本機 PDF pp. 1–7：前言、方法、模型設定、結果開頭；討論與結論未讀）
related: [../ideas/009-contribution-positioning-literature.md]
---

# Fanous et al. (2025)：紅樹林海岸的淺水＋泥砂 PINN

## 核心（讀全文確認）
- **方程**：二維淺水方程（Eq. 1–2）＋水深平均泥砂方程 Eq. 3：∂c/∂t + ∂(u₁c)/∂x + ∂(u₂c)/∂y = ∂/∂x(e_s ∂c/∂x) + ∂/∂y(e_s ∂c/∂y)。**沒有沉降、侵蝕、沉積源項**，也**沒有 h 加權**（不是我們的保守形式 ∂(hC)/∂t + ∇·(huC)）。
- **全耦合**：網路輸入 (x, y, t)，輸出水位 η、速度 u₁、u₂、濃度 c（Fig. 2）。
- **資料**：有限元素模式 **Thetis** 的模擬輸出（50,000 點）只用來監督**水位與速度**；**濃度沒有資料，完全由方程 Eq. 3 推得**（Sec. 2.2）。沒有實測 SSC。
- 損失含因果權重（Eq. 7–9，引 Wang 2022）；NVIDIA Modulus、6 層 × 256、swish、Adam lr 3e-4 指數衰減、1,002,000 步；沒有 L-BFGS；不反算參數。
- 結果（Table 1）：相對 Thetis 的 RMSE，水位 ~0.007 m、速度 ~0.02 m/s、濃度 ~1e-6；PINN 訓練 24 小時 vs Thetis 5 天。作者稱是「first such application of PINNs in a fully coupled hydro-morphodynamic setting」。

## 和我們的關係
- **目前找到唯一的二維水深平均懸浮泥砂 PINN**，但走的是全耦合＋代理模型（取代數值模式），對應我們沒採用的 B；而且濃度沒有任何觀測，源項也簡化掉了。
- 和我們的 A（給定 SRH-2D 流場、用實測 SSC 推估濃度與率定參數）目的不同。

## 不可比之處
- 潮汐驅動的海岸 vs 河川或水庫洪水事件。
- 濃度 RMSE ~1e-6 是和數值模式比，且濃度量級未說明，不能當成實測精度。
- 泥砂方程無源項、非保守形式。

## 待辦
- 討論與結論章節用到時再讀（限制段落）。
