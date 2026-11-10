---
type: idea
status: confirmed
date: 2026-11-05
related: [001-origin-ssc-pinn-on-srh2d-hydraulics.md, ../experiments/exp-p0-analytic-forward-inverse.md, ../methods.md]
---

# P0 設計：用二維高斯泥砂團的解析解驗證程式（主線二的起點）

## 為什麼先做解析解
真實資料的誤差可能來自四個地方：水理場、入砂邊界、閉合參數、網路本身，很難分辨。先在**答案完全已知**的情況下確認方法和程式是對的：如果 PINN 對不上解析解，就是程式有 bug，不會和其他誤差來源混在一起。

使用者第一次看到 P0 時問「你沒有資料怎麼訓練的」。這裡記下回答：正算模式**沒有用任何觀測資料**。PDE 配點只是隨機抽的 (x,y,t) 座標，不需要知道那裡的濃度，只要求方程式成立；初始值和邊界值由解析解提供。反算模式的「觀測」，是用解析解加 5% 雜訊**造出來的合成資料**。

## 解析解
均勻水理場（h = 2 m、u = 1 m/s、v = 0.1 m/s），K_x = K_y = K，D = α_d w_s C，E = 0：

C(x,y,t) = C₀ · σ₀²/σ² · exp(−r²/2σ²) · exp(−α_d w_s t/h)，σ² = σ₀² + 2Kt

真值：K = 2 m²/s、w_s = 1×10⁻³ m/s、C₀ = 1 kg/m³、σ₀ = 60 m。計算域 1000 m × 400 m × 500 s。Peclet 數 UL/K = 500，屬於平流主導。

## 兩種模式
- **forward（正算）**：已知 K、w_s，loss = PDE + IC + BC。PINN 的角色等同求解器，像 SRH-2D 一樣。
- **inverse（反算）**：K、w_s 未知（初值 0.5、5×10⁻³），加入 6 站 × 40 時刻的合成觀測。對應實務上的閉合參數率定。

## 設計上的選擇
- 輸出 Cθ = C₀ · softplus(N)，保證非負
- 網路輸入用物理座標，內部正規化到 [−1,1]，所以自動微分得到的就是物理單位的導數
- PDE 配點：一半均勻抽樣，一半沿泥砂團軌跡加密（加密寬度用 K = 1 估計，不偷看真值 K = 2）
- 訓練：Adam 15000 步（lr 1e-3 指數衰減到 1e-4）→ L-BFGS 500 步（固定配點）

## 預測
如果程式正確，正算 relL2 應該能到幾 % 以內，質量應該照 exp(−w_s t/h) 衰減，反算應該能把 K、w_s 拉回真值附近。

## 結果
見 [exp-p0-analytic-forward-inverse](../experiments/exp-p0-analytic-forward-inverse.md)：正算 2.6%、反算 6.2%，K = 1.91、w_s = 0.99×10⁻³。**預測成立，程式驗證通過（H4、H5）。**

但訓練過程出現意料之外的現象：Adam 階段 PDE loss 很小，誤差卻卡在 73%。這開啟了 [003](003-pde-loss-small-not-correct.md)。
