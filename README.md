# SSC-PINNs：二維水理懸浮載濃度與輸砂量推估

> **English summary.** A physics-informed neural network (PINN) for the 2D depth-averaged suspended sediment concentration C(x, y, t). Hydrodynamics (h, u, v, τb) come from a given 2D model such as SRH-2D (one-way coupling), and the network learns only C. The conservative-form residual is computed by automatic differentiation through differentiable flow fields, so spatially varying h and u are handled by the chain rule. Status: the method has been verified on an analytic 2D Gaussian plume (forward and inverse estimation of diffusivity K and settling velocity ws). It includes a training-strategy ablation and a manufactured-solution check of the residual under non-uniform flow. **No field data have been used.** The next step, connecting real SRH-2D output and measured SSC, is open for anyone to pick up. The research log (`research_log/`, in Traditional Chinese) records every hypothesis, design decision, result and its provenance. See "給接手者" below.

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
| P0 延伸 | 訓練策略消融（因果訓練、gradnorm、Fourier features、SOAP、第二階段優化器） | ✅ 完成：建議流程為「Adam + gradnorm 權重 → L-BFGS（權重凍結）」 |
| 6A | 非均勻流場的殘差正確性（manufactured solution vs sympy，含負對照） | ✅ 測試通過；結論還在討論中 |
| 6B、6C | 帶雜訊反算的可辨識性；其他待驗證項目 | — |
| P1 | 單事件固定流場（SRH-2D） | ⏳ 等待 SRH-2D 輸出與實測 SSC |
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

> 上面兩張表是早期的固定權重結果；之後的比較與建議流程，見 `research_log/comparison_catalog.md` 與 `research_log/hypotheses.md`。

## 給接手者

這個專案目前沒有實地資料，方法驗證的部分已經完成。如果你手上有 SRH-2D 輸出和 SSC 實測資料，可以從這裡接手。

**1. 先了解現況**：讀 [research_log/hypotheses.md](research_log/hypotheses.md)。最上面是目前最前沿的待解問題，下面是所有假設的狀態，以及支持或推翻它們的證據。

**2. 目前建議的訓練流程**（[H18](research_log/hypotheses.md)，P0 正算與反算各 3 個 seed 都穩定）：

```bash
python experiments/p0_analytic.py --mode inverse --weighting gradnorm --s2-patience 50
```

**兩個階段都用 gradnorm 權重**：
- 第一階段（Adam）：每 100 步依梯度範數重算一次權重。
- 第二階段（L-BFGS）：沿用第一階段最後算出的 gradnorm 權重，然後凍結。L-BFGS 靠歷史梯度估計曲率，線搜尋也假設目標函數不變，所以這個階段不更新權重。

只在第二階段才開始用 gradnorm（第一階段用固定權重，`--stage2-weights gradnorm`）不夠穩定，3 個 seed 裡有 1 個的 K 偏到 0.16。不要用固定的大觀測權重（例如 100），它會讓 PDE 的梯度幾乎失效，L-BFGS 也會因線搜尋失敗而停住（H17）。

**3. 接上真實水理場**：把 SRH-2D 的 h、u、v、τb 重建成 (x, y, t) 的**可微函數**，填入 `sscpinn/physics.py` 的 `Hydro`。不要把 h、u 當成網路的輸入特徵，否則殘差會漏掉 ∂h/∂x、∂u/∂x 這類鏈鎖律項。`experiments/check_6a_residual.py` 示範了正確與錯誤做法的差別，換成新的重建方式後，可以先用它驗證。

**4. 還沒做的事**：
- P1：拿到資料後的單事件固定流場
- 6B：測站數與雜訊量對 K、ws 可辨識性的影響（H11、H19）
- H1–H3：和一般神經網路、SRH-2D 本身的比較

文獻定位見 [research_log/ideas/009](research_log/ideas/009-contribution-positioning-literature.md)。

## 用 epistemic-provenance skill 閱讀研究紀錄

`research_log/` 是用 [epistemic-provenance](https://github.com/roger-chang1999/epistemic-provenance) skill 維護的。它是一套給 Claude 用的研究紀錄流程，每個主張都記錄來源、證據和改變的過程，每個實驗也都經過設計與分析兩個討論關卡。

建議裝上這個 skill，再讓 Claude 帶你讀研究紀錄。它會依照紀錄的結構回答，分清楚假設、證據和推測，也能沿用同樣的格式繼續記錄你的實驗。

```bash
claude plugin marketplace add roger-chang1999/epistemic-provenance
claude plugin install epistemic-provenance@epistemic-provenance
```

然後在這個專案裡問 Claude，例如：

- 「我們現在研究進度到哪？」
- 「解釋 H17 是怎麼被發現的」
- 「我拿到 SRH-2D 資料了，我們來討論 P1 的實驗設計」

## 授權

- 程式碼（`sscpinn/`、`experiments/`、`tools/`）：[MIT](LICENSE)
- 研究紀錄與實驗結果（`research_log/`、`results/`）：[CC BY 4.0](research_log/LICENSE.md)，使用時請標明出處
- `research_log/papers/` 筆記中引用的文獻內容，版權屬於原作者
