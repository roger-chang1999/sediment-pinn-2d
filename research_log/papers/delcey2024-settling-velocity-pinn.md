---
type: paper
title: "Identification of Settling Velocity with Physics Informed Neural Networks For Sediment Laden Flows"
authors: Delcey, Cheny, Keck, Gans, Kiesgen de Richter
venue: Computer Methods in Applied Mechanics and Engineering (2024)；arXiv 2404.06802
source: 部分讀過全文（2026-11-08，子代理逐字讀取 arXiv HTML v1 的 Sec. 1.1–3；Sec. 4 只有摘要轉述；跳過前言）
related: [../ideas/009-contribution-positioning-literature.md, ../ideas/005-inverse-as-calibration-and-statistics.md]
---

# Delcey et al. (2024)：用 PINN 反算沉速

## 核心（逐字核對）
- 方程：2D (x, z) 垂直剖面，Boussinesq Navier–Stokes（渦度形式）＋鹽度＋泥砂輸送（Eq. 2），**不是水深平均**。網路同時輸出 S、C、u、w、ω，**流場由網路學，不是給定的**。
- 資料：半拉格朗日數值解（合成），子區域均勻網格 342×128×125（約 547 萬點），資料點與配點相同。兩種觀測：PILAT（觀測 S、C）與 PIV（觀測 u、w）。雜訊 0／15／25／35%（相對最大值的加性高斯雜訊）。
- 反算：**只有沉速 Vp 一個參數**；擴散相關參數（Sc、τ、Rs）固定，不反算。
- 結果：無雜訊時 Vp 誤差約 1–2%；觀測 C 時 35% 雜訊下最差約 −18%；只觀測速度時最差約 −36%（我們從 Table 4、5 計算）。
- 訓練：L = 1000·L_data + L_f；9 層 × 195、swish；Adam、batch 1024、70 epochs（約 37 萬步，我們推算）；沒有 L-BFGS、沒有多 seed。
- 可辨識性：沒有正式分析（唯一性、敏感度）；Table 4 隨雜訊不單調，暗示單次實現的變異，論文未討論。

## 和我們的關係
- 最接近「PINN 反算泥砂參數 + 雜訊」的文獻，和我們的反算（K、ws 同時反算）、H19（雜訊下 K 偏離）、6B 直接相關。
- 他們的 λ=1000 固定權重、資料點極密（547 萬點），和我們「6 站 × 40 時刻」的稀疏觀測情境差很多。

## 不可比之處
- 垂直剖面 NS vs 我們的水深平均平流擴散；流場由網路學 vs 我們給定流場。
- 觀測密度差好幾個數量級；只反算 Vp，不反算擴散係數，所以沒有 K–ws 互相補償的問題。
- 合成資料，沒有實測。

## 待辦
- 用到時讀 Sec. 4（殘差形狀作為 Vp 可信度的間接診斷，目前只有摘要轉述）。
