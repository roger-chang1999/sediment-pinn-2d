---
type: paper
title: "Source Tracing for Pollutants in River Channels Based on a Physics-Informed Neural Network"
authors: X. Zhao, H. Liu, F. Leng, W. Yang 等
venue: Water Resources Research (2026)
doi: 10.1029/2025wr040846
source: 只讀摘要（2026-11-08，OpenAlex）
related: [../ideas/009-contribution-positioning-literature.md, search-2026-11-08/search_log.md]
---

# Zhao et al. (2026)：PINN 反算河道污染源

## 核心（依摘要）
- 用 PINN 從**斷面觀測**反算污染源參數（釋放強度、位置）。
- 測試穩定流、非穩定流、帶雜訊的非穩定流；測試案例是**真實河系的數值模擬**（不是實測）。
- 能辨識出觀測河段之外的源參數，並重建整個計算域的污染物分布。

## 和我們的關係
- 河川輸送方程的 PINN 反問題，發表在 WRR；可以作為「PINN 反算河川輸送參數」的前例，和我們反算 K、ws 的定位比較。
- 它引用了 He & Tartakovsky 2021 與 Niu 2023（被引用追蹤找到）。

## 不可比之處
- 反算的是源項（強度、位置），不是擴散與沉降係數；污染物不沉降。
- 是否給定流場、維度（推測一維）需讀全文確認。

## 待辦
- 讀全文：維度、流場是否給定、雜訊設定、權重與優化策略。
