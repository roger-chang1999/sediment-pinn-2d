---
type: paper
title: "Respecting causality for training physics-informed neural networks"
authors: S. Wang, S. Sankaran, P. Perdikaris
venue: Computer Methods in Applied Mechanics and Engineering (2024)；arXiv 2203.07404
source: 已讀全文（2026-11-08，子代理逐字讀取 arXiv HTML v1）
related: [../ideas/003-pde-loss-small-not-correct.md, ../ideas/006-training-improvements-five-directions.md]
---

# Wang, Sankaran & Perdikaris (2024)：因果訓練

## 核心
時間相依問題中，一般 PINN 同時最小化所有時刻的殘差，可能先在後段時間擬合出錯誤的解，**違反物理的因果性**（應該先有早期解，才能決定後期解）。

做法：把時間切成 N_t 段，第 i 段殘差的權重設為

w_i = exp( −ε · Σ_{k<i} L_r(t_k) )

前面時段的殘差還大時，後面的權重接近 0；前面降下來後，後面的權重才逐漸打開。ε 是「因果參數」，可以由小到大逐步調整；當所有 w_i 都接近 1（例如 min w_i > 0.99）時，表示已依序學完。

測試題包含 Allen–Cahn、Kuramoto–Sivashinsky、Lorenz 系統、二維 NS 等。

## 和我們的關係
- 直接對應 [idea 003](../ideas/003-pde-loss-small-not-correct.md) 的失敗二（傳播失敗）：P0 正算的 Adam 階段 IC 擬合很好、relL2 仍有 73%，推測是後段時間沒學好。
- [idea 006](../ideas/006-training-improvements-five-directions.md) 第 1 項。

## 實作要注意
- 需要按時間分段計算殘差 → 配點的時間要分層抽樣（每段數量相近），否則各段的 L_r 雜訊不一致。
- ε 的選擇：太大會讓後段永遠學不到；太小等於沒有因果權重。原文用多組 ε 逐步放寬。
- 權重 w_i 要 stop-gradient（不對 w 反向傳播）。

## 不可比之處
- 原文的測試題多是混沌或強非線性問題，我們的 P0 是線性平流–擴散。效果幅度可能不同。

## 全文核對（2026-11-08）
- 因果權重 Eq. 3.2：w_i = exp(−ε Σ_{k=1}^{i−1} L_r(t_k))，**累積和從 k=1 起，IC 不計入**；權重用 stop-gradient。
- ε 退火：[1e-2, 1e-1, 1, 10, 100]，min w_i > δ=0.99 時進入下一個 ε；λ_ic 1e2–1e4；N_t 32–100。
- 搭配 modified MLP、精確週期邊界、time-marching；只用 Adam，**沒有 L-BFGS**；**只做正問題**（Sec. 6）。
- 文中有幾處不一致：w_i 初始化（Algorithm 1 為 1，停止準則段落為 0）、λ_ic 值、Allen-Cahn 深度。
- **我們的實作偏差**：IC 計入累積和、ε 固定不退火、沒有停止準則（見 [exp-p0-training-improvements-ablation](../experiments/exp-p0-training-improvements-ablation.md)）。
