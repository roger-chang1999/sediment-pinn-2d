---
type: paper
title: "Mitigating Propagation Failures in Physics-informed Neural Networks using Retain-Resample-Release (R3) Sampling"
authors: A. Daw, J. Bu, S. Wang, P. Perdikaris, A. Karpatne
venue: ICML 2023
source: 依既有知識整理，未在本專案中重讀全文
related: [../ideas/003-pde-loss-small-not-correct.md]
---

# Daw et al. (2023)：傳播失敗與 R3 抽樣

## 核心
- 提出 **propagation failure** 的概念：PINN 的正確解必須從初始/邊界條件「傳播」到內部，但在傳播完成之前，網路可能在內部收斂到平凡解或錯誤解，而且殘差也很小。
- 特徵：殘差在空間/時間上高度不平衡，集中在少數區域。
- 提出 R3（Retain-Resample-Release）抽樣：保留殘差高的配點、其餘重抽，把配點逐步集中到殘差大的地方。

## 和我們的關係
- [idea 003](../ideas/003-pde-loss-small-not-correct.md) 的失敗二用的就是這個名詞。
- 使用者提出的「data imbalance」直覺，和這篇「殘差高度不平衡」的描述相近。
- R3 是因果訓練以外的另一種對策，這次五項實驗沒有列入；如果因果訓練效果不佳，可以作為替代方案。

## 不可比之處
- 測試題（convection、Allen–Cahn 等）和我們的問題不同。
