---
type: paper
title: "1-D coupled surface flow and transport equations revisited via the physics-informed neural network approach"
authors: J. Niu, W. Xu, H. Qiu, S. Li, F. Dong
venue: Journal of Hydrology, 625, 130048 (2023)
doi: 10.1016/j.jhydrol.2023.130048
source: 專案作者原始構想中的文獻整理（二手）；未讀全文
related: [../ideas/001-origin-ssc-pinn-on-srh2d-hydraulics.md]
---

# Niu et al. (2023)：一維淺水 + 平流–擴散的耦合 PINN

## 核心（二手整理，未讀全文）
以 PINN 求解一維淺水方程與平流–擴散方程的耦合問題。

## 和我們的關係（主線一）
- 支持「PINN 可以同時處理水流和輸運方程」的可行性，對應 [idea 001](../ideas/001-origin-ssc-pinn-on-srh2d-hydraulics.md) 的全耦合選項 (B)。
- 是原始構想的文獻整理中最接近「水流 + 物質輸運」的 PINN 文獻之一。

## 不可比之處
不是二維水庫 SSC 的實測驗證：一維、無實測資料。

## 待辦
讀全文，確認：是否全耦合（網路同時輸出 h、u、C）、loss 權重怎麼設、有沒有遇到傳播失敗。
