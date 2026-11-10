---
type: idea
status: confirmed
date: 2026-11-06
related: [002-p0-analytic-verification-design.md, 004-lbfgs-curvature-not-sampling.md, ../experiments/exp-p0-analytic-forward-inverse.md, ../experiments/exp-optimizer-sgd-vs-adam-and-weight-decay.md, ../papers/daw2023-r3-propagation-failure.md, ../papers/wang2024-causal-training.md]
---

# PDE loss 小，不代表解正確：兩種不同的失敗模式

## 從哪裡來
P0 正算的 Adam 階段：PDE loss 從 10⁻³ 持續下降，relL2 卻從 90% 只降到 73%（15000 步），直到 L-BFGS 才降到 2.6%。這正好印證一個常見的警告：PDE loss 小，不代表實測誤差也小。

使用者接著要求試 SGD，又看到更極端的版本：SGD + momentum 0.9 的 PDE loss 掉到 **10⁻²⁰**，relL2 剛好 **100%**。

## 兩種失敗要分開
| | Adam 第一階段 | SGD + momentum |
|---|---|---|
| relL2 | 73% | 100% |
| IC loss | 2×10⁻⁶（t=0 擬合很好） | 7.6×10⁻²（t=0 也錯） |
| 狀況 | t=0 正確，但沒有正確傳到後面的時間 | 整個場崩到 C≡0 |
| L-BFGS 能救嗎 | 能，到 2.6% | 不能，維持 100% |

### 失敗一：平凡解（trivial solution）
C≡0 完全滿足懸浮載守恆方程（沒有泥砂，就沒有平流、擴散、沉降）。SGD+momentum 的大步長把輸出層 softplus 推進飽和區，梯度 ≈ 0，IC loss 和觀測 loss 都拉不回來。反算模式下 K、w_s 完全停在初值。

### 失敗二：傳播失敗（propagation failure，推測）
只有初始條件告訴網路「這裡有泥砂」，資訊必須靠 PDE 從 t=0 傳到後面的時間。在後段，C≈0 也能讓殘差很小，網路容易在後段「偷懶」，讓泥砂團變淡或抹平。PINN 文獻稱為 propagation failure，見 [daw2023](../papers/daw2023-r3-propagation-failure.md)、[wang2024 causal](../papers/wang2024-causal-training.md)。

**這是根據 loss 數字推測的**：IC loss 很小、relL2 很大，而且 relL2 會隨步數慢慢下降。舊版程式**沒有存第一階段結束時的濃度場圖**，所以還沒有直接看到「後段變淡」→ 列為 [H7](../hypotheses.md)（open）。

## 使用者提出的解讀（記錄原話脈絡）
使用者問：「是不是 Adam 隨機抽樣容易抽到鼓勵 trivial solution 的位置，出現類似 data imbalance 的狀況，讓模型傾向 C=0？」

**部分正確**：
- 正確的地方：只有 IC 少數點在「拉」網路產生非零解，大量 PDE 配點不排斥 C≈0，確實像 data imbalance。
- 需要修正的地方：(1) Adam 沒有崩到 C≡0，崩掉的是 SGD+momentum；(2) 隨機重抽配點是抽樣策略，不是 Adam 的特性；我們的配點也有一半沿泥砂團軌跡加密；(3) L-BFGS 有效的原因不是解決抽樣問題，見 [004](004-lbfgs-curvature-not-sampling.md)。

## 對研究方法的意義
**真實資料沒有解析解可比。** 所以判斷訓練成敗，一定要同時看 IC/BC/觀測 loss，不能只看 PDE loss。已寫進 [methods.md](../methods.md) 協定四的陷阱。

## 接下來
- 驗證 H7：用 `--lbfgs 0` 存下第一階段結束時的圖，直接看是不是後段變淡
- 對策：因果訓練（[006](006-training-improvements-five-directions.md) 第 1 項）
