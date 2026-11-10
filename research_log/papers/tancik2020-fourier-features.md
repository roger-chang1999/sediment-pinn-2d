---
type: paper
title: "Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains"
authors: M. Tancik, P. P. Srinivasan, B. Mildenhall, et al.
venue: NeurIPS 2020
source: 依既有知識整理，未在本專案中重讀全文
related: [../ideas/006-training-improvements-five-directions.md]
---

# Tancik et al. (2020)：Fourier features

## 核心
- MLP 有**頻譜偏差（spectral bias）**：傾向先學低頻、很難學到高頻細節。
- 把輸入 v 先映射成 γ(v) = [cos(2πBv), sin(2πBv)]，B 的元素從 N(0, σ²) 抽樣，網路就能學到高頻函數。σ 控制可學的頻率範圍。
- 用 NTK 理論解釋：Fourier 映射改變了 NTK 的頻譜衰減。

PINN 上的延伸：Wang, Wang & Perdikaris (2021, CMAME) "On the eigenvector bias of Fourier feature networks"，處理多尺度 PDE。

## 和我們的關係
- [idea 006](../ideas/006-training-improvements-five-directions.md) 第 3 項。
- 真實洪水的濃度鋒面比 P0 的高斯泥砂團陡很多。

## 預先的擔心
- σ 選太大會產生高頻雜訊，對平滑的 P0 高斯泥砂團**可能沒幫助甚至變差**。所以 P0 的結果只能說明「不會破壞平滑解」，真正的價值要到 P1 的陡鋒面才看得出來。
- 我們的輸入在網路內部已正規化到 [−1,1]，σ 要相對於這個範圍選。時間座標是否要一起做 Fourier 映射，也是需要決定的設計。

## 不可比之處
- 原文是影像、3D 形狀回歸，不是 PDE。
