---
type: idea
status: open
date: 2026-11-05
related: [../papers/raissi2019-pinns.md, ../papers/niu2023-1d-coupled-flow-transport.md, ../papers/haddadchi2026-pinn-sed.md, ../papers/ohara2024-2d-swe-inversion.md, 002-p0-analytic-verification-design.md]
---

# 研究起點：以 SRH-2D 水理場驅動 SSC-PINNs（主線一）

## 來源
專案作者的原始研究構想與方法規劃（個人文件，未納入本 repo）。

## 研究問題
水庫或河川的懸浮載模擬常受三件事影響：上游入砂濃度歷線稀疏、侵蝕/沉降閉合參數不確定、洪水期間濃度劇烈變化。當流量歷線完整、SSC 卻只有零星採樣時，用率定曲線 Qs = aQ^b 設定泥砂邊界，可能表現不出遲滯現象。

想法是讓 PINN 學濃度函數 Cθ(x,y,t)，並同時滿足：
- 二維水深平均懸浮載守恆：∂(hC)/∂t + ∇·(hCu) = ∇·(hK∇C) + E − D + S_ext
- 少量實測 SSC
- 初始條件、邊界條件、全域質量收支

## 方程式的層級（使用者原始想法：要符合「多個方程式」）
Navier–Stokes →（靜水壓、淺水、水深積分）→ 二維 de Saint-Venant → 驅動懸浮載守恆。

**NS 本身不會進 loss**，它是推導 SWE 的來源。原始構想建議第一階段採**單向耦合**：
- **(A) 單向耦合（原始構想的主軸）**：SRH-2D 提供 h、u、v（可微重建），PINN 只學 C；SWE 殘差只拿來檢核水理場品質。
- **(B) 全耦合**：網路同時輸出 h、u、v、C，loss 包含連續方程、兩個動量方程和泥砂方程。比較接近「多方程式都符合」，但二維 SWE 的 PINN 本身就是研究課題，急變流和濕乾邊界很難處理。
- **(C) 混合版（Claude 建議，待討論）**：SRH-2D 流場當成觀測去訓練水理網路，再加上 SWE 殘差當正則化。

**尚未決定**：使用者還沒選 A/B/C，也還沒提供 SRH-2D 輸出和 SSC 實測資料。

## 實作上的關鍵陷阱
如果把 h、u 當成獨立的網路輸入特徵，計算 ∂(huC)/∂x 時就會漏掉 ∂h/∂x、∂u/∂x 項。我們的實作（`sscpinn/physics.py`）把 h、u、v 設計成 (x,y,t) 的**可微函數**，殘差直接對 hC、huC 做自動微分，鏈鎖律會自動算進去。

## 原始構想列出的應驗證假設
- 融入 PDE 和質量守恆約束後，模型在觀測稀疏時可能更穩定 → [H1](../hypotheses.md)
- 模型可能改善測站 SSC、事件累積量或跨事件泛化 → [H2](../hypotheses.md)
- 跨操作情境的代理模型可能降低查詢成本 → [H3](../hypotheses.md)

以及**不應先行宣稱**的結論：PINN 必然比 SRH-2D 準確；PDE 殘差越小，誤差就一定越小；單場訓練好就能推算所有新情境。

## 分階段計畫
P0 理論與程式驗證（解析解）→ P1 單事件固定流場 → P2 跨事件比較（M0 SRH-2D／M1 一般 NN／M2 SSC-PINN／M3 +質量守恆）→ P3 延伸課題（入流歷線重建、多情境代理）。

## 接下來
先做 P0，確認自動微分、通量方向和質量守恆寫對了，見 [002](002-p0-analytic-verification-design.md)。

## 更新（2026-11-08）：耦合方式已決定
使用者決定依原始構想採 **(A) 單向耦合**；(C) 混合版（Claude 建議）不採用。資料之後提供、不先做數值假想案例。見 [idea 007](007-mainline1-decisions-plan-a-method-first.md)。
