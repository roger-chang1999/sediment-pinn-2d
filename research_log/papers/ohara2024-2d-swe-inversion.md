---
type: paper
title: "Physics-informed neural networks for inversion of river flow and geometry with shallow water model"
authors: Y. Ohara, D. Moteki, S. Muramatsu, K. Hayasaka, H. Yasuda
venue: Physics of Fluids, 36, 106633 (2024)
doi: 10.1063/5.0232852
source: 專案作者原始構想中的文獻整理（二手）；未讀全文
related: [../ideas/001-origin-ssc-pinn-on-srh2d-hydraulics.md, ../ideas/005-inverse-as-calibration-and-statistics.md]
---

# Ohara et al. (2024)：二維淺水 PINN 反算流場與河床

## 核心（二手整理，未讀全文）
以二維淺水方程的 PINN 反算流場，以及河床高程或糙率。

## 和我們的關係
- 顯示 PINN 在**二維水理逆問題**上的潛力，和 [idea 005](../ideas/005-inverse-as-calibration-and-statistics.md)「PINN 的價值在反算」的論點一致。
- 如果之後採用全耦合或混合版（[idea 001](../ideas/001-origin-ssc-pinn-on-srh2d-hydraulics.md) 的 B/C），這篇的二維 SWE 殘差實作和訓練策略是主要參考。

## 不可比之處
沒有處理二維 SSC：只有水理，沒有泥砂。

## 待辦
讀全文：二維 SWE PINN 怎麼處理濕乾邊界、用了什麼觀測、訓練技巧。
