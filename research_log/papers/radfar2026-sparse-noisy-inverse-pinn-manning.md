---
type: paper
title: "How sparse and how noisy? Systematic benchmarking of inverse physics-informed neural networks for Manning friction estimation in shallow water equations"
authors: S. Radfar
venue: Physics of Fluids (2026)
doi: 10.1063/5.0349054
source: 只讀摘要（2026-11-08，OpenAlex；摘要被截斷）
related: [../ideas/009-contribution-positioning-literature.md, ../ideas/008-method-reverification-branches.md, search-2026-11-08/search_log.md]
---

# Radfar (2026)：反算 PINN 在稀疏、雜訊觀測下估 Manning 係數

## 核心（依摘要）
- 系統性測試**觀測稀疏度、雜訊、觀測變數類型**對反算 Manning 係數的影響。
- 兩個 benchmark：一維 MacDonald 渠道（解析解）、二維有橫向拋物床面的斜坡渠道（有限體積解）。
- Manning 係數為可訓練正值純量，與流場一起反算；**兩階段優化：先擬合觀測，再加入物理殘差**。
- 二維：只要 5 個水深與流速觀測、雜訊到場標準差的 20%，誤差 < 5%；誤差下限等於參考解本身的離散誤差。一維：誤差隨觀測數增加而系統性下降（摘要後段被截斷）。

## 和我們的關係
- **6B 的方法學範本**：稀疏度 × 雜訊 × 觀測類型的系統性設計，正是 6B（H11、H19）要做的事，只是對象是水理參數，不是泥砂的 K、ws。
- 「先擬合觀測、再加物理」的兩階段策略，和我們觀察到的權重問題（H17：obs 權重過高讓 PDE 失去作用）方向相反，值得讀全文比較。

## 不可比之處
- 反算的是 Manning 係數（一個參數）；我們是 K、ws 兩個，可能互相補償。
- 觀測是水深、流速；我們是濃度。

## 待辦
- 讀全文：兩階段策略的細節、雜訊定義、多 seed、和權重的關係。
