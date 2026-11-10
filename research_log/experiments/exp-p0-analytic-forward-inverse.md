---
type: experiment
status: done
date: 2026-11-06
seeds: [0]
results: [../../results/_legacy_v1/p0_forward_adam_lr0.001/seed0, ../../results/_legacy_v1/p0_inverse_adam_lr0.001/seed0]
related: [../ideas/002-p0-analytic-verification-design.md, ../ideas/003-pde-loss-small-not-correct.md, ../ideas/004-lbfgs-curvature-not-sampling.md]
---

# 實驗：P0 解析解驗證，正算與反算（Adam 基準）

## 方法
腳本 `experiments/p0_analytic.py`（commit ef9822b 時的版本；當時還沒有 `--opt` 等參數，等同現在的預設值）。

```bash
python experiments/p0_analytic.py --mode forward   # 現行版本的等價指令
python experiments/p0_analytic.py --mode inverse
```

- 網路：MLP 5 × 64，tanh，Xavier 初始化，輸出 C₀·softplus
- 第一階段：Adam lr 1e-3 → 1e-4 指數衰減，15000 步，每步重抽 8192 個 PDE 配點和 1024 個 BC 點
- 第二階段：L-BFGS 500 次迭代、history 50、strong Wolfe，固定 16384 個配點
- Loss 權重：pde 1、ic 100、bc 10、obs 100
- 硬體：RTX 2070 8GB；GPU 獨占

## 結果

| 項目 | 正算 | 反算 |
|---|---|---|
| relL2（最終，L-BFGS 後） | **2.64%** | **6.17%** |
| relL2（第 14000 步，Adam） | 72.6% | 5.87% |
| 質量守恆最大相對誤差 | 3.67% | 3.01% |
| K（真值 2.0） | 固定 | 1.913（初值 0.5） |
| w_s（真值 1.0e-3） | 固定 | 0.992e-3（初值 5e-3） |
| 訓練時間 | 281 s | 305 s |

**Adam 階段的 relL2 軌跡**（每 1000 步評估一次）：

| 步數 | 0 | 1000 | 3000 | 5000 | 8000 | 10000 | 14000 |
|---|---|---|---|---|---|---|---|
| 正算 | 481% | 90.0% | 87.6% | 85.3% | 81.5% | 79.0% | 72.6% |
| 反算 | 482% | 19.7% | 11.1% | 8.3% | 6.4% | 5.9% | 5.9% |
| 反算 K | 0.50 | 0.41 | 0.26 | 0.35 | 1.20 | 1.62 | 1.90 |

## 結論
1. **程式驗證通過**：保守形式殘差、自動微分、通量方向正確（H4 confirmed）；誤差最大約 0.02 kg/m³，是峰值的 2–3%。
2. **參數可回收**：K 誤差 4%、w_s 誤差 1%，從離真值 4–5 倍的初值出發（H5 confirmed，但只有單 seed、6 站、5% 雜訊這一個條件）。
3. **觀測大幅加速收斂**：1000 步時反算 19.7%，正算 90.0%。少量觀測能「錨定」泥砂團位置。
4. **PDE loss 小但解不對**：正算 Adam 階段 PDE loss 約 10⁻³，relL2 仍有 73% → 開啟 [idea 003](../ideas/003-pde-loss-small-not-correct.md)。
5. **L-BFGS 效果不對稱**：正算 72.6% → 2.6%（大幅改善），反算 5.87% → 6.17%（略變差）→ 記錄在 [idea 004](../ideas/004-lbfgs-curvature-not-sampling.md) 的「尚未解釋」。

K 的軌跡不是單調的（0.5 → 0.26 → 1.90）：先往錯誤方向走，8000 步後才轉向。這個「先錯後對」現象值得在多 seed 時觀察是否穩定出現。

## 限制
- 單一 seed。
- 舊版程式沒有存 `relL2_stage1`，也沒有存第一階段結束時的圖；表中 Adam 階段的數值取自第 14000 步的 log。
- 結果只有權重（`net_legacy.pt`），沒有優化器狀態，無法續訓。
- 均勻流場：沒有測到 h、u 隨空間變化時的鏈鎖律項，那要等 P1。
