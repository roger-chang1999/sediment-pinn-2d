# 假設索引（中樞）

這是最常回來查的檔案。每條假設都連到「哪個想法提出的」「哪些實驗支持或推翻」。狀態用語：

- **open**：尚未驗證
- **planned**：已設計實驗，尚未執行
- **supported**：有證據支持，但條件有限（例如單一 seed）
- **confirmed**：多次或多條件驗證成立
- **refuted**：被推翻
- **superseded**：被更精確的假設取代

## 當前最前沿的待分析問題

1. **P0 訓練改進 node 已結束（2026-11-08，使用者確認結論）**：新基準為**完整 gradnorm**（Adam + gradnorm → L-BFGS 凍結權重），見 H17、H18、[exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md)。下一步：使用者決定把三項重新驗證（6A 不均勻流場實作、6B 雜訊觀測下的反算、6C 未決項目）掛在此 node 底下作為分枝，見 [idea 008](ideas/008-method-reverification-branches.md)；執行順序待定。
2. **雜訊觀測下的反算**（H19、H11）：觀測權重過高時 loss 越低、K 越偏；需要不依賴正確答案的停止或判斷方式。真實 SSC 誤差 10–20%，直接關係主線一。
3. **不均勻流場的鏈鎖律項尚未測到**（H4 的限制，[idea 007](ideas/007-mainline1-decisions-plan-a-method-first.md)）。
3. **主線一決策（2026-11-08，使用者決定）**：資料之後提供、目前先確認模型方法；耦合採原始構想的 **A 單向耦合**；不先做數值假想案例。見 [idea 007](ideas/007-mainline1-decisions-plan-a-method-first.md)。

## 主線一：研究的原始動機（見 [idea 001](ideas/001-origin-ssc-pinn-on-srh2d-hydraulics.md)）

| # | 假設 | 狀態 | 提出於 | 支持/推翻證據 |
|---|---|---|---|---|
| H1 | 融入 PDE 與質量守恆約束後，模型在 SSC 觀測稀疏時比純資料驅動 NN 更穩定 | **open** | 原始構想、[idea 001](ideas/001-origin-ssc-pinn-on-srh2d-hydraulics.md) | 尚無。需 P2 的 M1（一般 NN）vs M2（SSC-PINN）對照。P0 的「反算 1000 步 19.7% vs 正算 90.0%」顯示觀測對 PINN 有幫助，但**不是** H1 要的對照（H1 是比較有無 PDE，不是有無觀測） |
| H2 | SSC-PINN 能改善測站 SSC、事件累積量 Ms 或跨事件泛化 | **open** | 原始構想 | 尚無。需 P1/P2 真實或數值假想資料 |
| H3 | 跨操作情境的代理模型能降低重複查詢成本 | **open**（延伸課題，P3） | 原始構想 | 尚無 |

## 主線二：實作後衍生的方法論問題（見 [idea 002](ideas/002-p0-analytic-verification-design.md) 起；是主線一的工具與檢核，不是研究原始目的）

| # | 假設 | 狀態 | 提出於 | 支持/推翻證據 |
|---|---|---|---|---|
| H4 | 保守形式殘差（h、u、v 為可微函數）+ 自動微分的實作正確 | **confirmed**（實作類：通過解析解驗證測試；均勻流場條件下） | [idea 002](ideas/002-p0-analytic-verification-design.md) | [exp-p0-analytic-forward-inverse](experiments/exp-p0-analytic-forward-inverse.md)：正算 relL2 2.64%，質量誤差 3.67%。限制：均勻流場，**h、u 隨空間變化的鏈鎖律項尚未測到**，要等 P1 |
| H5 | PINN 反算能從稀疏帶雜訊觀測找回閉合參數 K、w_s | **supported**（單 seed、單一條件） | [idea 002](ideas/002-p0-analytic-verification-design.md) | [exp-p0-analytic-forward-inverse](experiments/exp-p0-analytic-forward-inverse.md)：6 站、5% 雜訊，K 1.913（真值 2.0）、w_s 0.992e-3（真值 1e-3）。**限制：P0 的方程式結構完全正確，結果不能外推為「真實河川能找到正確參數」**，見 [idea 005](ideas/005-inverse-as-calibration-and-statistics.md) |
| H6 | PDE loss 小不代表解正確；存在「平凡解」和「傳播失敗」兩種失敗模式 | **confirmed**（實驗類：多條件——Adam 正算、SGD 正算、SGD+momentum 正算與反算都觀察到）。**只限「PDE loss 小 ≠ 正確」與「平凡解」**；「傳播失敗」是推測，見 H7（open） | [idea 003](ideas/003-pde-loss-small-not-correct.md) | Adam：PDE ~1e-3、relL2 73%；SGD+momentum：PDE 1e-20、relL2 100%（C≡0），正算與反算皆然。見 [exp-optimizer-sgd-vs-adam-and-weight-decay](experiments/exp-optimizer-sgd-vs-adam-and-weight-decay.md) |
| H7 | Adam 第一階段卡在 ~73%，主因是傳播失敗（後段時間泥砂團變淡或抹平） | **open**（由 loss 數字推測） | [idea 003](ideas/003-pde-loss-small-not-correct.md) | IC loss 2e-6、relL2 73%，與傳播失敗一致。2026-11-08：因果訓練（H12）因實作偏離原文，**無法用來回答**；v2 已存 `snapshots_stage1.png`，尚未檢視。使用者認為第一階段指標不需比較（[exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md) 第 1 輪），此假設優先度降低 |
| H8 | L-BFGS 有效是因為修正病態 loss 地形的曲率；它需要好的起點，也無法逃離梯度消失的平凡解 | **supported**（依賴文獻：「修正曲率」的機制解釋來自 rathore2024，我們只觀察到與之一致的現象，沒有獨立驗證機制） | [idea 004](ideas/004-lbfgs-curvature-not-sampling.md) | [exp-optimizer-sgd-vs-adam-and-weight-decay](experiments/exp-optimizer-sgd-vs-adam-and-weight-decay.md)、[exp-p0-analytic-forward-inverse](experiments/exp-p0-analytic-forward-inverse.md)：Adam 起點 73%→2.6%；SGD 起點 88%→16.1%；C≡0 起點 100%→100%。**未解釋**：反算時 L-BFGS 讓 relL2 略變差（5.87%→6.17%）。2026-11-08：v2 診斷顯示反算 base 的 L-BFGS 是線搜尋失敗、obs 權重主導（H17），v1 的變差可能同機制（未驗證）。文獻：[rathore2024](papers/rathore2024-loss-landscape.md) |
| H9 | SGD 在 P0 的表現遠差於 Adam | **supported**（只限測過的兩組設定） | [exp-optimizer](experiments/exp-optimizer-sgd-vs-adam-and-weight-decay.md) | SGD lr=1e-3：16.1%；SGD lr=1e-2+m0.9：崩潰。**沒有系統性掃描 SGD 學習率**，不能推廣成「SGD 本質上不適合」 |
| H10 | weight decay 1e-4 對 P0 結果沒有可辨識的影響 | **supported**（單 seed） | [exp-optimizer](experiments/exp-optimizer-sgd-vs-adam-and-weight-decay.md) | AdamW wd=1e-4：2.52% vs Adam 2.64%；單 seed 無法區分差異是否來自雜訊 |
| H11 | 參數可識別性取決於測站數和雜訊量；觀測太少時 K 和 w_s 會互相補償 | **open** | [idea 005](ideas/005-inverse-as-calibration-and-statistics.md) | 待辦：測站 6→3→1、雜訊 5%→20%，每組多 seed，看 K、w_s 的分散程度與相關性 |
| H12 | 因果訓練能大幅降低 Adam 的 `relL2_stage1`（預測 < 20%） | **open**（不下結論：實作偏離原文——IC 計入累積和、未做 ε 退火） | [idea 006](ideas/006-training-improvements-five-directions.md) #1 | [exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md)：第一階段 70–84%，與 base 無差異。文獻：[wang2024-causal-training](papers/wang2024-causal-training.md)（已讀全文） |
| H13 | 自動 loss 權重（梯度範數平衡）可達到與手動權重相當的結果，不需手調 | **superseded**（結果遠優於預測，由 H18 取代） | [idea 006](ideas/006-training-improvements-five-directions.md) #2 | [exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md)。實作公式對應 [wang2023-expert-guide](papers/wang2023-expert-guide.md)，不是 [wang2021-gradient-pathologies](papers/wang2021-gradient-pathologies.md) 的 max/mean 版 |
| H14 | Fourier features 對 P0 平滑的高斯泥砂團沒有幫助，甚至略差 | **supported**（實驗類，3 seed；只測 σ=1） | [idea 006](ideas/006-training-improvements-five-directions.md) #3 | [exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md)：正算最終 72–75%；反算 K ≈ 0.025、質量誤差 65–74%。真正的檢驗在 P1 陡鋒面 |
| H15 | SOAP 的 `relL2_stage1` 優於 Adam | **supported**（實驗類，3 seed；只限正算） | [idea 006](ideas/006-training-improvements-five-directions.md) #4 | [exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md)：正算 1.0–1.2% vs Adam 69–84%。反算 K 0.04–0.10（真值 2.0），原因未決（見 H19）。簡化實作、未搭配 gradnorm，與 [wang2025-soap-gradient-alignment](papers/wang2025-soap-gradient-alignment.md) 不可比 |
| H16 | SSBroyden 或 Natural Gradient 的最終 relL2 優於 L-BFGS | **open**（不下結論：只測了完整矩陣 BFGS 與 Oren–Luenberger 自我縮放 BFGS，不等同 SSBroyden；NG 未測） | [idea 006](ideas/006-training-improvements-five-directions.md) #5 | [exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md)：正算 BFGS 10.6／15.4%、SS-BFGS 11.8／46.8%，L-BFGS 2.4／5.0%（2 個有效 seed）；反算比較無效（第二階段沒跑） |
| H17 | 反算中固定權重 obs 100 讓 PDE 的梯度貢獻降到千分之幾到百分之幾（兩階段皆然），使 L-BFGS 線搜尋失敗、K 不受約束 | **supported**（實驗類，3 seed；P0） | [exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md) 第 1 輪（使用者觀察「PDE 幾乎等於沒加」） | 起點 obs 占 loss 96–98%、K 梯度 ~1e-6；PDE:obs 梯度貢獻 1:680／1:250／1:13；只換第二階段權重即可讓 L-BFGS 重新運作（3/3） |
| H18 | 完整 gradnorm（Adam + gradnorm → L-BFGS 凍結權重）在 P0 正、反算都穩定，作為新基準 | **supported**（實驗類，3 seed；P0；未嚴格收斂） | [exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md) 第 2 輪（使用者提議，Claude 修正為完整版） | 正算 0.35–0.68%；反算 K 1.936／2.032／1.973、relL2 0.75／0.59／2.48%；只在第二階段用 gradnorm 的 seed 2 失敗（K 0.162） |
| H19 | 觀測權重相對 PDE 過高時，loss 降低伴隨 K 偏離（擬合觀測雜訊） | **open**（推測，1 例） | [exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md) 第 2 輪 | 換權重 s2：第 2000 步後 loss 急降、K 1.55→0.16；SOAP、Fourier 反算的 K 偏小型態類似。與 [idea 005](ideas/005-inverse-as-calibration-and-statistics.md) 的等效參數警告相關 |
| H20 | 正算 base seed 2 的 Adam 終點讓 L-BFGS 線搜尋失敗（83.6% 不變），與權重無關 | **open**（1 例，機制未知） | [exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md) 第 1 輪 | 3 步、t=0.0054，起點 pde 2.9e-3 為主 |

## 已排除或刻意不主張的論述

- ~~PINN 找到了真實河川的「正確」閉合參數~~：真實資料的結構誤差會被吸收成等效參數，只能主張「給定閉合式下的等效參數」，並以獨立事件檢驗可轉移性（[idea 005](ideas/005-inverse-as-calibration-and-statistics.md)）。
- ~~SGD 本質上不適合 PINN~~：只測了兩組設定，見 H9。
- ~~L-BFGS 解決了隨機抽樣造成的 data imbalance~~：L-BFGS 修正的是曲率；抽樣是另一件事，而且 L-BFGS 救不了平凡解（[idea 003](ideas/003-pde-loss-small-not-correct.md)、[004](ideas/004-lbfgs-curvature-not-sampling.md)）。
- ~~PINN 必然比 SRH-2D 準確或快速~~：原始構想明列為不應先行宣稱的結論。
