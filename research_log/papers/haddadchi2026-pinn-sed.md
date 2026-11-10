---
type: paper
title: "PINN-Sed: Interconnected Physics-Informed Machine Learning Model for High Resolution Suspended Sediment Transport in River Network"
authors: A. Haddadchi, N. Movahedi, R. Akbarian-Bafghi, M. Raissi
venue: Journal of Hydraulic Engineering, 153(1), 04026061 (2027；2026-09-28 線上發表)；CC BY 4.0
doi: 10.1061/JHEND8.HYENG-14926
pdf: data/papers/haddadchi2026-pinn-sed.pdf（本機，不進版控）
source: 已讀全文（2026-11-08，本機 PDF pp. 1–15：方法、資料、結果、限制；附錄 I–V 未讀）
related: [../ideas/001-origin-ssc-pinn-on-srh2d-hydraulics.md, ../ideas/009-contribution-positioning-literature.md]
---

# Haddadchi et al. (2026)：PINN-Sed，一維河網懸浮載

## 核心（讀全文確認）
- **方程**（Eq. 1）：一維斷面平均平流擴散，保守形式 ∂(Ac)/∂t + ∂(Qc)/∂x = B(r_y − d_e) + ∂/∂x(K ∂(Ac)/∂x)；沉降 d_e = αvc（Eq. 2，α=1）；再懸浮以單位水流功率（Eq. 3）；K = k_c u* h（Eq. 4，k_c=250）。
- **水理是給定的**：A、Q、B、h 來自水文模式 **TopNet** 的時間序列，內插到 PINN 網格，作為殘差中的已知量（Fig. 1）。這和我們的 A（單向耦合、固定水理場）是**同一種範式**，但在一維。
- **網路**：每條河段一個 PINN（輸入 x、t，情境 1、2 另加流量 Q），輸出 C；匯流點用 BC／IC 損失把上下游 PINN 接起來（Fig. 2）。11 層 × 128、tanh、Adam lr 1e-3、50,000 epochs、50,000 配點；**沒有 L-BFGS**。
- **資料**：紐西蘭 Manawatū 河 **3 個測站實測** 15 分鐘流量與 SSC（重取樣為 1 小時），**12 場洪水**（2018-05～2019-08），**依事件切分**：事件 1–6 訓練、7–12 驗證（情境 2 只用 4 場訓練）。
- **參數**：Eq. 3 的臨界水流功率係數在 PINN 中**固定為 1**；PINN **不反算任何參數**。對照的物理模式用遺傳演算法率定係數。
- **結果**（Table 2，驗證事件）：情境 1 的濃度一致性係數 ρc 0.83、事件輸砂量 RMSE 5.8 kt；物理模式 0.47／26.5 kt；LSTM 0.64／33.85 kt。只用 x、t 當輸入（情境 0）時驗證 ρc 0.02，無法外推到新事件。
- **損失權重**：所有項權重相同（Eq. 6，λ 皆為 1），「to avoid introducing additional hyperparameters」；作者把權重調整列為未來工作。

## 和我們的關係
- **H2（測站 SSC、事件輸砂量、跨事件泛化）在一維已經做到**，而且用實測資料、依事件切分、和物理模式與 LSTM 對照。我們若要宣稱貢獻，需要說明二維與 SRH-2D 帶來什麼新東西。
- 他們不反算參數、權重全為 1；我們的 H17（固定權重讓反算中的 PDE 失去作用）與 H18（gradnorm）可以對照討論，但他們沒有反算，情境不同。
- 他們把流量 Q 當網路輸入才能外推到新事件（情境 0 vs 1），對我們的網路輸入設計（是否加 h、u、v 當特徵）是重要參考；但要注意鏈鎖律問題（見 idea 001）（他們的殘差用給定的 A、Q，不經網路輸入微分）。

## 不可比之處
- 一維斷面平均 vs 二維水深平均；水文模式 TopNet vs 二維水動力模式 SRH-2D。
- 河網（匯流）vs 單一河段或水庫。
- 他們的 ρc、事件輸砂量 RMSE 是實測資料上的指標；我們目前只有解析解上的 relL2。

## 待辦
- 附錄 I（損失項清單）、IV（配點數敏感度）、V（散點圖）用到時再讀。
