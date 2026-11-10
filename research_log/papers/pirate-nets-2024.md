---
type: paper
title: "PirateNets: Physics-informed Deep Learning with Residual Adaptive Networks"
authors: S. Wang, B. Li, Y. Chen, P. Perdikaris
venue: JMLR 25 (2024)
url: https://jmlr.org/papers/v25/24-0313.html
source: 依網路搜尋摘要＋既有知識；未讀全文
related: [../ideas/006-training-improvements-five-directions.md]
---

# PirateNets (2024)

## 核心
- 深層 PINN 很難訓練。PirateNets 用**可適應的殘差連接**：殘差分支的權重 α 初始化為 0，所以網路一開始等同淺層網路，訓練中逐漸「變深」。
- 通常搭配 Fourier features、物理資訊初始化、因果訓練等技巧（同團隊的 jaxpi 程式庫）。

## 用於淺水方程的證據（依搜尋，2026-11-07）
- Mullins & Soulaïmani（DTE AICCOMAS 2025）把 PirateNet 和因果訓練、課程學習結合用於二維 SWE；報告的是 2D Burgers 的誤差（2.1%、1.4%），SWE 被描述為下一步。
- ÉTS 碩士論文（Mullins, 2025）報告加強版 PINN 在自由液面演變（含變化底床）上優於標準 PINN。
- **都是作者自己或學位論文的結果，缺乏獨立的比較。**

## 和我們的關係
**這次五項實驗不列入**：它同時改了架構、初始化，通常還搭配 Fourier features 和因果訓練，和 #1、#3 混在一起難以歸因。等單項消融完成後，可以作為「組合」的參考設計。

## 來源
- [Mullins & Soulaïmani, DTE AICCOMAS 2025](https://dte_aicomas_2025.iacm.info/event/contribution/77aaf391-8735-11ef-b344-000c29ddfc0c)
- [Mullins 碩士論文](https://espace.etsmtl.ca/3638/1/Mullins_Mathieu.pdf)
