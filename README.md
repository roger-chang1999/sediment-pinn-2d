# SSC-PINNs：二維水理懸浮載濃度與輸砂量推估

以二維水深平均水理場（SRH-2D）驅動物理資訊神經網路（PINNs），推估懸浮載濃度 C(x,y,t)、斷面輸砂率 Qs(t) 與事件累積懸浮載輸送量 Ms。

控制方程式（二維水深平均懸浮載守恆）：

```
∂(hC)/∂t + ∂(huC)/∂x + ∂(hvC)/∂y = ∂(hKx ∂C/∂x)/∂x + ∂(hKy ∂C/∂y)/∂y + E − D + S_ext
D = α_d · w_s · C,    E = M · max(τ_b/τ_ce − 1, 0)
```

這是一個個人研究專案。目前只用解析解與合成資料驗證方法，沒有使用任何實測資料。

## 專案結構

```
sscpinn/            核心套件
  model.py          SSCNet：Cθ = C_ref·softplus(Nθ(x*,y*,t*))
  physics.py        保守形式 SSC 殘差（h、u、v 為可微函數，自動處理鏈鎖律）、全域質量積分
experiments/
  p0_analytic.py    P0 解析解驗證（二維高斯泥砂團平流–擴散–沉降），正算／反算
research_log/       研究記錄：假設索引、評估協定、想法演變、文獻筆記、實驗記錄（先讀 research_log/README.md）
results/<設定標籤>/seed<k>/   各實驗輸出
  config.json       設定
  ckpt_stage1.pt    第一階段完整狀態（可續訓）
  final.pt          L-BFGS 後最終權重
  summary.json、snapshots.png、training.png
  net_legacy.pt     （舊版結果，只有權重，無法續訓）
```

## 執行

```bash
pip install -r requirements.txt
python experiments/p0_analytic.py --mode forward   # 正算：已知 K、w_s，只用 PDE+IC+BC
python experiments/p0_analytic.py --mode inverse   # 反算：稀疏合成觀測反推 K、w_s

# 優化器與 weight decay
python experiments/p0_analytic.py --opt sgd --lr 1e-2 --momentum 0.9 --wd 1e-4

# 多 seed、續訓、分段訓練
python experiments/p0_analytic.py --seed 1
python experiments/p0_analytic.py --iters 30000 --resume          # 從 checkpoint 延長到 30000 步
python experiments/p0_analytic.py --iters 30000 --stop-at 10000   # 依 30000 步排程，先跑到 10000 步
```

續訓與不中斷訓練的權重完全一致（含亂數狀態還原）。學習率 lr(it) = lr0·0.1^(it/iters)，延長 `--iters` 時續訓起點 lr 會依新總步數回升。

## 進度

| 階段 | 內容 | 狀態 |
|---|---|---|
| P0 | 解析解驗證：AD、通量、質量守恆、參數反算 | ✅ 完成 |
| P1 | 單事件固定流場（數值假想案例或 SRH-2D） | ⏳ 規劃中 |
| P2 | 跨事件比較：SRH-2D／一般 NN／PINNs（M0–M3） | — |
| P3 | 入流泥砂歷線重建、多情境代理模型 | — |

### P0 結果（RTX 2070，Adam 15000 步 + L-BFGS 500 步）

| 項目 | 正算 | 反算（6 站、5% 雜訊） |
|---|---|---|
| 濃度場相對 L2 誤差 | 2.6% | 6.2% |
| 全域質量守恆最大誤差 | 3.7% | 3.0% |
| K（真值 2.0 m²/s） | — | 1.91 |
| w_s（真值 1.0e-3 m/s） | — | 0.99e-3 |

觀察：正算在 Adam 階段 PDE loss 已很小，但濃度場誤差仍達 73%，L-BFGS 後才降到 2.6%——PDE loss 小不代表解正確；稀疏觀測能明顯加速收斂。

### 優化器與 weight decay 比較（seed 0，15000 步 + L-BFGS 500 步）

| 設定 | 模式 | 第一階段後 relL2 | 最終 relL2 | 質量守恆誤差 | 備註 |
|---|---|---|---|---|---|
| Adam lr=1e-3 | 正算 | ~73% | **2.6%** | 3.7% | 基準 |
| AdamW lr=1e-3, wd=1e-4 | 正算 | 70% | **2.5%** | 3.3% | 與基準相當 |
| SGD lr=1e-3 | 正算 | 88% | 16.1% | 24.1% | IC 擬合慢，L-BFGS 救不完 |
| SGD lr=1e-2, momentum 0.9 | 正算 | 100% | 100% | 100% | 崩到 C≡0 平凡解 |
| Adam lr=1e-3 | 反算 | — | **6.2%** | 3.0% | K=1.91, w_s=0.99e-3 |
| SGD lr=1e-2, momentum 0.9 | 反算 | 100% | 100% | 100% | 崩到 C≡0，K、w_s 停在初值 |

C≡0 完全滿足 PDE（殘差 ~1e-20）；softplus 輸出層進入飽和區後梯度消失，連觀測 loss 與 L-BFGS 都拉不回來。
