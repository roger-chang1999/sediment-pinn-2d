---
type: experiment
status: done
date: 2026-11-06
seeds: [0]
results: [暫存於 %TEMP%/ckpttest，已刪除]
related: [../methods.md]
---

# 實驗（方法論）：checkpoint 續訓是否等同不中斷訓練

## 動機
使用者要求依設定存下權重，以便之後跑多 seed 驗證、或增加 iteration 繼續優化。需要先確認「中斷後續訓」不會改變結果，否則續訓的實驗不能和一次跑完的實驗比較。

## 方法
`experiments/p0_analytic.py` 加入：
- `ckpt_stage1.pt`：網路、優化器狀態、log K、log w_s、loss 歷史、CPU/CUDA 亂數狀態；每 `--ckpt-every` 步原子寫入（先寫 .tmp 再改名）
- `final.pt`：L-BFGS 後權重
- `config.json`：設定。續訓時檢查 mode、opt、lr、momentum、wd、nf、width、depth、seed 是否一致
- `--resume`、`--stop-at N`（依 `--iters` 的排程訓練，到第 N 步先停）
- 學習率改成 lr(it) = lr0 · 0.1^(it/iters) 直接由步數計算，續訓時不需要還原 scheduler

測試：

```bash
# A：一次跑完
python experiments/p0_analytic.py --mode $m --iters 500 --lbfgs 10 --ckpt-every 100 --out A
# B：跑到 300 步停，再續訓到 500
python experiments/p0_analytic.py --mode $m --iters 500 --lbfgs 10 --ckpt-every 100 --stop-at 300 --out B
python experiments/p0_analytic.py --mode $m --iters 500 --lbfgs 10 --ckpt-every 100 --resume --out B
```

## 結果

| 模式 | ckpt_stage1.pt 權重最大差 | final.pt 權重最大差 | K（A / B） |
|---|---|---|---|
| forward | 0.00e+00 | 0.00e+00 | 2.0 / 2.0 |
| inverse | 0.00e+00 | 0.00e+00 | 0.56716 / 0.56716 |

其他檢查：
- 延長訓練（500 → 700 步，`--resume`）正常，hist 長度 700
- 設定不符時拒絕續訓，並列出不同的設定（例如 lr 0.001 vs 0.002）
- 已有 checkpoint 卻沒加 `--resume` 時拒絕執行，避免覆蓋

**開發過程中發現的 bug**：`torch.load(map_location="cuda")` 會把 RNG 狀態搬到 GPU，`set_rng_state` 需要 CPU ByteTensor → 改成 `map_location="cpu"`。

## 結論
**續訓和不中斷訓練的結果完全一致（bitwise）**，包含 L-BFGS 之後。多 seed、延長訓練的實驗可以安全地使用續訓。

## 限制
- 延長 `--iters` 時，續訓起點的學習率會依新的總步數回升（例如 15000 → 30000，lr 從 lr0/10 回到 lr0/√10）。這是刻意的設計，但這種「延長訓練」和「一開始就設 30000 步」**不等價**。
- Windows 終端按 Ctrl+C 時的存檔路徑未實測。
- 只在 500 步的小規模上測試。
