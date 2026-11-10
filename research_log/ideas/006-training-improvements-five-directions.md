---
type: idea
status: done
date: 2026-11-07
related: [003-pde-loss-small-not-correct.md, 004-lbfgs-curvature-not-sampling.md, ../papers/wang2024-causal-training.md, ../papers/wang2021-gradient-pathologies.md, ../papers/tancik2020-fourier-features.md, ../papers/wang2025-soap-gradient-alignment.md, ../papers/optimization-bottleneck-2026.md, ../papers/rathore2024-loss-landscape.md, ../papers/pirate-nets-2024.md]
---

# 訓練改進的五個方向：P0 消融實驗計畫（主線二）

## 從哪裡來
使用者問：「流體 PINN 的 SOTA 就是 Adam + L-BFGS 嗎？還是有優化空間？」查文獻後的結論：Adam + L-BFGS 是**標準基準，不是 SOTA**。改進方向分成四類：優化器、loss 權重平衡、抽樣與因果性、網路架構。

**要注意**：多數 SOTA 宣稱來自 Burgers、NS、Helmholtz 這類標準測試題，**很少有人在河川泥砂問題上獨立比較**。PirateNets 用於二維 SWE 的證據主要來自作者自己的會議論文和學位論文。

## 五項實驗（依「成本低、直接對症」排序）

| # | 做法 | 對症的問題 | 假設 | 文獻 |
|---|---|---|---|---|
| 1 | **因果訓練**：前段時間殘差降下來之前，壓低後段的權重 | 傳播失敗（[003](003-pde-loss-small-not-correct.md)） | [H12](../hypotheses.md) | [wang2024](../papers/wang2024-causal-training.md) |
| 2 | **自動 loss 權重**：依梯度範數平衡各項 | 手動權重（pde 1、ic 100、bc 10、obs 100）換到真實資料後必須重調 | [H13](../hypotheses.md) | [wang2021](../papers/wang2021-gradient-pathologies.md) |
| 3 | **Fourier features**：輸入先做隨機傅立葉映射 | 真實洪水的濃度鋒面比高斯泥砂團陡 | [H14](../hypotheses.md) | [tancik2020](../papers/tancik2020-fourier-features.md) |
| 4 | **SOAP**：準二階優化器，取代 Adam | 病態 loss 地形（[004](004-lbfgs-curvature-not-sampling.md)） | [H15](../hypotheses.md) | [wang2025](../papers/wang2025-soap-gradient-alignment.md) |
| 5 | **SSBroyden / Natural Gradient**：取代 L-BFGS | 更精確的曲率近似 | [H16](../hypotheses.md) | [optimization-bottleneck-2026](../papers/optimization-bottleneck-2026.md) |

PirateNets 這次不列入（[pirate-nets-2024](../papers/pirate-nets-2024.md)），因為它同時改架構和初始化，和 #3 混在一起難以歸因。

## 實驗設計原則
- **基準**：Adam lr=1e-3、15000 步 + L-BFGS 500 步、width 64 × depth 5、nf 8192
- **一次只改一個變因**（消融）。要組合，等單項結果出來再說。
- **多 seed**：每個設定至少 3 個 seed（0, 1, 2），報告平均 ± 標準差。現有基準只有 seed 0，**要補跑 seed 1、2**。
- **正算和反算都要跑**：正算看傳播失敗，反算看參數回收。
- **同時報告 `relL2_stage1` 和最終 `relL2`**（[methods.md](../methods.md) 協定一），才分得出是第一階段方法的貢獻，還是 L-BFGS 救回來的。
- 新方法要同時存第一階段結束時的濃度場圖，用來直接檢驗 H7。
- 計算成本只在 GPU 獨占時記錄。

## 預先寫下的預測（避免事後合理化）
- #1 因果訓練：如果傳播失敗是 Adam 卡住的主因，`relL2_stage1` 應該從 ~73% 大幅下降（例如 < 20%）；最終 relL2 改善幅度較小，因為 L-BFGS 本來就能救回來。
- #2 自動權重：最終 relL2 可能和基準相當，主要價值在**不用手調**；如果明顯變差，代表手動權重剛好調得不錯。
- #3 Fourier features：對平滑的高斯泥砂團**可能沒幫助甚至變差**（高頻偏差會產生雜訊）。這項在 P0 的訊息有限，在 P1 的陡鋒面才是真正的考驗。
- #4 SOAP：`relL2_stage1` 應該優於 Adam。
- #5 SSBroyden：最終 relL2 應該優於 L-BFGS，但單步計算量較大。

## ⚠️ 不要過度投入的提醒
P0 可以把誤差從 2.6% 壓到 0.01%，但真實資料的 **SSC 觀測誤差通常就有 10–20%**（採樣代表性、濁度轉換），再加上流場和閉合式誤差，優化器的精度提升很可能被蓋過。

所以這一組實驗的目標是「**夠好、夠穩定**」：不同 seed 得到一樣的結果、不會掉進平凡解。這對主線一的研究結論影響比較大。**不要把主線二的優化器改進當成研究主要貢獻**（見 [README](../README.md) 的因果線原則）。

## 更新（2026-11-07）：設計決策的來源

使用者同意「針對五點進行實驗」，但**以下實驗設計細節是 Claude 單方面決定的，沒有經過設計討論**（當時研究流程還沒有關卡一）。分析結果時要把這點納入考慮，必要時重新討論：

| 決策 | 選定 | 決定者 | 理由（當時） |
|---|---|---|---|
| 因果訓練 ε | 10、100 兩組 | Claude 預設未經討論 | 冒煙測試顯示 ε=100 時 1000 步後權重仍 ~1e-10，對 ε 敏感，所以跑兩組 |
| 因果訓練是否把 IC loss 計入累積 | 計入 | Claude 預設未經討論 | 讓後段權重在 IC 擬合好之前保持關閉；原文是否如此未核對 |
| 因果訓練時間分段數 | 32 | Claude 預設未經討論 | — |
| 自動權重版本 | 梯度範數平衡（λ_k = Σ‖∇L_j‖/‖∇L_k‖），每 100 步、EMA 0.9 | Claude 預設未經討論 | 常見做法；非 Wang 2021 原始的 max/mean 版本 |
| Fourier features | σ=1、m=64，空間與時間一起映射 | Claude 預設未經討論 | 沒有掃描 σ |
| SOAP | 自行實作的簡化版，precond_freq=10，lr 1e-3 | Claude 預設未經討論 | 不引入外部程式碼；與官方實作的差異寫在 sscpinn/optim.py |
| 第二階段替換 | 完整矩陣 BFGS 與 Oren–Luenberger 自我縮放 BFGS，共用基準第一階段 | Claude 預設未經討論 | 不等同 Urbán et al. 的 SSBroyden |
| Natural Gradient | 不做 | Claude 預設未經討論 | 計算量大 |
| seed 數 | 3（0、1、2） | Claude 預設未經討論 | — |
| 資料亂數改用獨立產生器（協定 v2） | 是 | Claude 預設未經討論 | 讓同一 seed 下各方法的資料相同 |

從下一個 node 開始，依 epistemic-provenance v0.2 的流程，實驗設計先經關卡一討論、使用者確認後才執行。

## 更新（2026-11-08）：結果與結論
實驗與兩輪分析見 [exp-p0-training-improvements-ablation](../experiments/exp-p0-training-improvements-ablation.md)。使用者確認的結論：新基準為完整 gradnorm（H18）；固定權重讓反算的 PDE 失去作用（H17）；因果訓練、SOAP、BFGS 變體不下結論。預測對照：#1 不符（實作偏離原文）、#2 遠優於預測、#3 方向符合、#4 正算符合／反算失敗、#5 正算不符。

