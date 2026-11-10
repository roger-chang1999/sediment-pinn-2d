---
type: paper
title: "Hybrid physics-informed neural networks for simulating coupled flow-sediment-bed fields in large, deep reservoirs"
authors: Z. Lu, K. Wang, A. Deng, T. Wang, S. Xiao, J. Wang, X. He, X. Feng
venue: SSRN 預印本 7163967（**未經同儕審查**，PDF 浮水印 "Preprint not peer reviewed"）
pdf: data/papers/lu-reservoir-flow-sediment-bed-pinn.pdf（本機，不進版控）
source: 部分讀過全文（2026-11-08，本機 PDF pp. 1–4、6–17：摘要、前言、方法、資料、整體結果開頭；消融、觀測配置、雜訊實驗、結論未讀）
related: [../ideas/009-contribution-positioning-literature.md]
---

# Lu et al.（SSRN 預印本）：溪洛渡水庫的水流–泥砂–河床耦合 PINN

## 核心（讀全文確認）
- **方程**：**一維** Saint-Venant（Eq. 1–2）＋一維懸浮泥砂（Eq. 3，源項 αBω_s(S* − S)，挾沙力 S* 用 Han 公式）＋河床變形（Eq. 4）。沉速 ω_s 與挾沙力用經驗公式計算（Eq. 6–8），**不反算**。
- **全耦合、雙分支網路**：水動力分支輸出 Q、H；泥砂分支輸出 S、ΔZ_b（Eq. 11–12）；輸入含 x、t、斷面幾何、上下游邊界條件，並做 Fourier 編碼（Eq. 9–10）。5 層 × 256、SiLU；Adam（可加 weight decay、梯度裁剪）。
- **損失**：資料（觀測、邊界、初始）＋物理殘差（四個方程，殘差以各項絕對值和正規化，Eq. 20）＋積分水量守恆（Eq. 21）＋水位變化率一致性（Eq. 22）。
- **資料**（Table 1）：邊界條件用**實測**（白鶴灘站、溪洛渡站的日流量、水位、含沙量）；但 **12 個監督斷面的觀測與初始條件來自一維水動力–泥砂數值模式**，不是實測。驗證也是和數值模式的參考場比較。
- 結果（摘要）：未監督斷面 RMSE：流量 118.61 m³/s、水深 3.07 m、SSC 0.095 kg/m³、河床 2.46 m；優於 MLP。有觀測配置與雜訊實驗（未讀）。

## 和我們的關係
- **和我們的「水庫 SSC」題目最接近**，而且作者宣稱是「first PINN-based framework for coupled flow–sediment–bed simulation」。但它是一維、全耦合、訓練觀測來自數值模式，沒有反算參數。
- 它的殘差正規化（Eq. 20）和我們的權重問題（H17、H18）相關，可以作為另一種平衡方式的參考。

## 不可比之處
- 一維斷面 vs 二維水深平均；全耦合 vs 單向耦合；監督資料是模式輸出，不是實測 SSC。
- 預印本，未經審查。

## 待辦
- 讀消融、觀測配置與雜訊實驗（Sec. 4 後段），用來設計 6B。
