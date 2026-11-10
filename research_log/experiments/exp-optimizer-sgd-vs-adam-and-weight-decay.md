---
type: experiment
status: done
date: 2026-11-06
seeds: [0]
results: [../../results/_legacy_v1/p0_forward_sgd_lr0.001/seed0, ../../results/_legacy_v1/p0_forward_sgd_lr0.01_m0.9/seed0, ../../results/_legacy_v1/p0_forward_adam_lr0.001_wd0.0001/seed0, ../../results/_legacy_v1/p0_inverse_sgd_lr0.01_m0.9/seed0]
related: [../ideas/003-pde-loss-small-not-correct.md, ../ideas/004-lbfgs-curvature-not-sampling.md, exp-p0-analytic-forward-inverse.md]
---

# 實驗：優化器（Adam vs SGD）與 weight decay

## 動機
使用者把 optimizer 換成 SGD 想試試看，並問「有沒有 weight decay」（原本沒有，Adam 的 weight_decay 預設為 0）。

## 方法
`experiments/p0_analytic.py` 加入 `--opt`、`--lr`、`--momentum`、`--wd`。其餘設定同 [Adam 基準](exp-p0-analytic-forward-inverse.md)。

```bash
python experiments/p0_analytic.py --mode forward --opt sgd --lr 1e-3
python experiments/p0_analytic.py --mode forward --opt sgd --lr 1e-2 --momentum 0.9
python experiments/p0_analytic.py --mode forward --opt adam --wd 1e-4
python experiments/p0_analytic.py --mode inverse --opt sgd --lr 1e-2 --momentum 0.9
```

- SGD 有 momentum 時用 Nesterov
- weight decay 只作用於網路權重，不作用於 log K、log w_s（否則會被拉向 log = 0）
- Adam 加 weight decay 時用 AdamW（解耦式）；wd = 0 時與 Adam 相同
- 學習率都在訓練中指數衰減到初值的 1/10

## 結果

| 設定 | 模式 | relL2_stage1 | 最終 relL2 | 質量誤差 | 備註 |
|---|---|---|---|---|---|
| Adam lr=1e-3（基準） | 正算 | ~72.6%* | **2.64%** | 3.67% | |
| AdamW lr=1e-3, wd=1e-4 | 正算 | 70.1% | **2.52%** | 3.34% | |
| SGD lr=1e-3 | 正算 | 88.0% | 16.1% | 24.1% | |
| SGD lr=1e-2, m=0.9 | 正算 | 100% | 100% | 100% | C≡0 |
| Adam lr=1e-3（基準） | 反算 | ~5.87%* | 6.17% | 3.01% | K=1.913 |
| SGD lr=1e-2, m=0.9 | 反算 | 100% | 100% | 100% | C≡0；K=0.500、w_s=4.99e-3（停在初值） |

\* 舊版沒有記錄 `relL2_stage1`，取第 14000 步的值。

**loss 分項（第一階段結束時）**：

| 設定 | pde | ic | bc | obs |
|---|---|---|---|---|
| Adam（14000 步） | 1.55e-3 | 2.3e-6 | 1.4e-5 | — |
| SGD lr=1e-3 | 5.66e-3 | 1.07e-4 | 2.9e-5 | — |
| SGD m=0.9（正算） | **1.8e-20** | 7.6e-2 | 1.3e-5 | — |
| SGD m=0.9（反算） | **5.9e-24** | 7.6e-2 | 9.8e-6 | 8.6e-2 |

**1000 步冒煙測試**：SGD lr=1e-3 的 IC loss 為 4.95e-2，同步數 Adam 為 8.6e-5（差約 600 倍）；SGD m=0.9 在 1000 步內就已崩到 C≡0（pde 2.5e-20）。

## 結論
1. **Weight decay 1e-4 沒有可辨識的影響**（2.52% vs 2.64%，單 seed 無法區分）。不是必要設定，但也沒有變差 → H10。
2. **SGD 無 momentum：可以收斂但很慢**。最終誤差是 Adam 的 6 倍，主因是 IC 沒擬合好，L-BFGS 的起點太差 → H9。
3. **SGD + momentum：崩到 C≡0 平凡解**。PDE 殘差小到 10⁻²⁰～10⁻²⁴，softplus 飽和使梯度消失，觀測 loss 和 L-BFGS 都拉不回來 → [idea 003](../ideas/003-pde-loss-small-not-correct.md) 失敗一。
4. **L-BFGS 不是平凡解的解藥** → [idea 004](../ideas/004-lbfgs-curvature-not-sampling.md) 限制 3。

## 限制
- 單一 seed。
- SGD 只試了兩組設定（lr 1e-3 無 momentum、lr 1e-2 有 momentum）。**SGD 適合的學習率沒有系統性掃描**，例如 lr 1e-3 + momentum 0.9，或加梯度裁剪。所以「SGD 不適合」的結論只限於這兩組設定，不能推廣成「SGD 本質上不適合」。
- AdamW 那組的訓練時間（372 s）與 checkpoint 測試共用 GPU，不可比。
- 結果只有 `net_legacy.pt`，無法續訓。
