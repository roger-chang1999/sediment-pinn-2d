---
type: paper
title: "The Optimization Bottleneck in Physics-Informed Neural Networks（亦作 Curvature-Aware Optimization for High-Accuracy PINNs）"
authors: 見 arXiv 頁面
venue: arXiv 2604.05230（2026 年 4 月預印本，未經同儕審查）
url: https://arxiv.org/html/2604.05230v1
source: 依網路搜尋摘要與 alphaxiv 自動生成的概要（2026-11-07）；未讀全文，數字需核對原文
related: [../ideas/006-training-improvements-five-directions.md, ../papers/rathore2024-loss-landscape.md]
---

# Optimization Bottleneck in PINNs（2026 預印本）

## 核心（依摘要）
- 把 PINN 訓練視為**非線性最小平方問題**，認為訓練不佳主要來自病態性。
- 系統性比較：BFGS、**SSBFGS、SSBroyden**（自我縮放的擬牛頓法）、**Natural Gradient**、SPRING、SOAP，並以 AdamW 為基準。
- 另外提出用於 inviscid Burgers 和 Euler 方程的 PINN 方法。
- alphaxiv 概要提到：高波數 Helmholtz 問題上，Natural Gradient + Fourier features 勝過 SOAP 和 Adam，但計算量非常大。**這是自動生成的二手摘要，需核對原文。**

## 相關的早期工作（依既有知識）
Urbán, Stefanou & Pons (2025, JCP) "Unveiling the optimization process of PINNs: How accurate and competitive can PINNs be?"：使用 SSBroyden 等自我縮放擬牛頓法，報告標準 MLP 的相對誤差可以壓到 10⁻⁷ 以下。**作者與數字依記憶，引用前需核對。**

## 和我們的關係
- [idea 006](../ideas/006-training-improvements-five-directions.md) 第 5 項：用 SSBroyden 或 Natural Gradient 取代 L-BFGS。
- PyTorch 沒有內建 SSBroyden，需要自己實作；Natural Gradient 對 16,961 個參數的網路可能可行，但要估計記憶體。

## 不可比之處
- 預印本、未經同儕審查。
- 測試題以標準 PDE 為主。
