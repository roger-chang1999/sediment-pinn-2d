# 比較實驗總目錄

這份文件把專案做過的每一組「A vs B」比較用統一格式列出，方便快速查閱，也方便寫論文或簡報時直接引用。格式：

- **比較內容**：什麼設定 vs 什麼設定
- **比較點**：為什麼這樣比（想回答什麼問題）
- **數據表格**：實驗數據（註明協定，見 [methods.md](methods.md)）
- **簡單結論**：這組數據說明了什麼

每一條最後保留對應的假設編號和原始記錄連結。順序依研究依賴鏈（和 [research_tree_overview](research_tree_overview.md) 的分支一致），不是時間順序。

---

## 一、P0 正確性驗證

### 1. 正算 vs 反算（有無觀測資料）

- **比較內容**：同一個 P0 問題，正算（已知 K、w_s，只用 PDE + IC + BC）vs 反算（K、w_s 未知，加 6 站 × 40 時刻、5% 雜訊的合成觀測）。Adam 基準設定，seed 0。
- **比較點**：PINN 能不能當求解器？加入稀疏觀測後收斂行為怎麼變？參數能不能回收？
- **數據表格**（協定一、二、三）：

  | | 1000 步 relL2 | 14000 步 relL2 | 最終 relL2 | 質量誤差 | K / w_s |
  |---|---|---|---|---|---|
  | 正算 | 90.0% | 72.6% | 2.64% | 3.67% | 固定真值 |
  | 反算 | 19.7% | 5.87% | 6.17% | 3.01% | 1.913 / 0.992e-3 |

- **簡單結論**：兩者最終都可用（2.6%、6.2%）。觀測讓 Adam 階段收斂快很多，能「錨定」泥砂團位置；反算最終值較高，可能受 5% 觀測雜訊限制。參數回收成功，但只是單 seed 點估計。
  （H4、H5，[exp-p0-analytic-forward-inverse](experiments/exp-p0-analytic-forward-inverse.md)）

---

## 二、訓練失敗模式與優化器

### 2. 優化器：Adam vs SGD vs SGD + momentum（正算）

- **比較內容**：Adam lr=1e-3、SGD lr=1e-3（無 momentum）、SGD lr=1e-2 + Nesterov momentum 0.9。其他設定相同，seed 0。
- **比較點**：使用者想試 SGD。PINN 文獻幾乎都用 Adam 起手，想確認在我們的問題上差多少。
- **數據表格**（協定一、二、四）：

  | 優化器 | relL2_stage1 | 最終 relL2 | 質量誤差 | 第一階段末 pde / ic loss |
  |---|---|---|---|---|
  | Adam lr=1e-3 | ~72.6%* | **2.64%** | 3.67% | 1.6e-3 / 2.3e-6 |
  | SGD lr=1e-3 | 88.0% | 16.1% | 24.1% | 5.7e-3 / 1.1e-4 |
  | SGD lr=1e-2 + m0.9 | 100% | 100% | 100% | **1.8e-20** / 7.6e-2 |

  \* 舊版沒有記錄 stage1，取第 14000 步。

- **簡單結論**：SGD 無 momentum 能收斂但慢，最終誤差是 Adam 的 6 倍，主因是 IC 沒擬合好；SGD + momentum 崩到 C≡0 平凡解，PDE 殘差反而最小。**只測了兩組 SGD 設定**，不能推廣成 SGD 本質上不適合。
  （H6、H9，[exp-optimizer-sgd-vs-adam-and-weight-decay](experiments/exp-optimizer-sgd-vs-adam-and-weight-decay.md)）

### 3. 優化器（反算）：Adam vs SGD + momentum

- **比較內容**：反算模式下，Adam lr=1e-3 vs SGD lr=1e-2 + m0.9。
- **比較點**：有觀測資料「拉」住網路時，SGD + momentum 還會崩潰嗎？
- **數據表格**：

  | 優化器 | 最終 relL2 | K（真值 2.0） | w_s（真值 1e-3） | 第一階段末 pde / obs loss |
  |---|---|---|---|---|
  | Adam | 6.17% | 1.913 | 0.992e-3 | — |
  | SGD + m0.9 | 100% | 0.500（=初值） | 4.99e-3（≈初值） | 5.9e-24 / 8.6e-2 |

- **簡單結論**：觀測資料也拉不回來。softplus 飽和使梯度消失，K、w_s 完全停在初值。**參數停在初值不一定是「找不到」，也可能是梯度消失**，要搭配 loss 分項判斷。
  （H6，[exp-optimizer-sgd-vs-adam-and-weight-decay](experiments/exp-optimizer-sgd-vs-adam-and-weight-decay.md)）

### 4. Weight decay：0 vs 1e-4

- **比較內容**：Adam（wd=0）vs AdamW（解耦式 wd=1e-4，只作用於網路權重），正算，seed 0。
- **比較點**：使用者問是否有 weight decay。PINN 一般不加，擔心會抹平陡峭的濃度鋒面。
- **數據表格**：

  | 設定 | relL2_stage1 | 最終 relL2 | 質量誤差 |
  |---|---|---|---|
  | wd = 0 | ~72.6%* | 2.64% | 3.67% |
  | wd = 1e-4 | 70.1% | 2.52% | 3.34% |

- **簡單結論**：沒有可辨識的差異（單 seed）。不必要，但也無害。P0 的高斯泥砂團很平滑，「抹平鋒面」的擔心要到 P1 才測得到。
  （H10，[exp-optimizer-sgd-vs-adam-and-weight-decay](experiments/exp-optimizer-sgd-vs-adam-and-weight-decay.md)）

### 5. 第一階段 vs 接 L-BFGS 之後

- **比較內容**：各設定第一階段結束時 vs 接 L-BFGS 500 次迭代之後的 relL2。
- **比較點**：L-BFGS 的貢獻有多大？是否依賴起點？（使用者的問題：L-BFGS 是不是解決了抽樣造成的 data imbalance？）
- **數據表格**（協定一的兩個版本）：

  | 第一階段 | 模式 | 第一階段後 | L-BFGS 後 | 變化 |
  |---|---|---|---|---|
  | Adam | 正算 | ~72.6% | 2.64% | 大幅改善 |
  | AdamW wd=1e-4 | 正算 | 70.1% | 2.52% | 大幅改善 |
  | SGD lr=1e-3 | 正算 | 88.0% | 16.1% | 改善但不夠 |
  | SGD + m0.9 | 正算 | 100% | 100% | 無效 |
  | Adam | 反算 | ~5.87% | 6.17% | **略變差** |

- **簡單結論**：L-BFGS 修正病態地形的曲率，效果取決於起點：好起點能大幅改善，差起點只能部分改善，平凡解完全救不了。反算時略變差的原因不明（可能是固定配點下對觀測雜訊過擬合）。
  （H8，[idea 004](ideas/004-lbfgs-curvature-not-sampling.md)）

---

## 三、方法論檢核

### 6. Checkpoint 續訓 vs 一次跑完

- **比較內容**：500 步一次跑完 vs 跑到 300 步停、再 `--resume` 到 500 步（含 L-BFGS 10 次）。
- **比較點**：續訓會不會改變結果？多 seed、延長訓練的實驗能不能安全使用續訓？
- **數據表格**：

  | 模式 | ckpt_stage1 權重最大差 | final 權重最大差 |
  |---|---|---|
  | forward | 0 | 0 |
  | inverse | 0 | 0 |

- **簡單結論**：完全一致（bitwise）。注意：延長 `--iters` 時學習率排程會改變，「延長訓練」和「一開始就設更多步」不等價。
  （[exp-checkpoint-resume-equivalence](experiments/exp-checkpoint-resume-equivalence.md)）

---

## 四、訓練改進與 loss 權重

### 7. 五項訓練改進消融（協定 v2，3 seed）

- **比較內容**：base（Adam → L-BFGS，固定權重）vs 因果訓練 ε 10／100、gradnorm、Fourier σ=1、SOAP、第二階段 BFGS／SS-BFGS。
- **比較點**：哪一項讓正算與反算穩定？
- **數據表格**（最終 relL2 %；反算括號內為 K，真值 2.0）：

  | 組別 | 正算 s0／s1／s2 | 反算 s0／s1／s2 |
  |---|---|---|
  | base | 2.40／4.98／83.6 | 4.68 (1.85)／4.29 (1.64)／7.87 (1.46) |
  | gradnorm | 0.55／0.68／0.35 | 0.75 (1.94)／0.59 (2.03)／2.54 (2.06) |
  | SOAP | 1.05／1.17／1.01 | 9.58 (0.10)／10.4 (0.05)／10.1 (0.04) |
  | Fourier σ=1 | 75.5／71.9／75.1 | 47.5 (0.025)／42.3 (0.027)／47.1 (0.024) |
  | 因果 ε=100 | 2.75／6.04／11.5 | 4.99 (1.86)／4.24 (1.66)／7.97 (1.39) |

- **簡單結論**：gradnorm 最穩定。**注意**：固定預算下的數字；因果訓練實作偏離原文；反算 base 的第二階段實際沒跑（見比較 8）。
  （[exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md)）

### 8. 反算第二階段的權重：固定 vs 只換第二階段 vs 完整 gradnorm

- **比較內容**：同一 base 第一階段起點，第二階段用固定權重 vs gradnorm 重算權重；另與完整 gradnorm 比較。第二階段加 patience（300、相對 1e-4、上限 5000）。
- **比較點**：L-BFGS 停住是不是權重造成的？
- **數據表格**（K；relL2 %）：

  | 配方 | s0 | s1 | s2 |
  |---|---|---|---|
  | 固定權重（L-BFGS 2–5 步即線搜尋失敗） | 1.850；4.68 | 1.636；4.29 | 1.464；7.87 |
  | 只換第二階段權重（patience） | 1.901；1.33 | 1.959；1.59（卡住） | **0.162；8.42**（5000 步未收斂） |
  | 完整 gradnorm（patience） | 1.936；0.75 | 2.032；0.59 | 1.973；2.48 |

- **簡單結論**：換權重就能讓 L-BFGS 運作；完整 gradnorm 3/3 回收 K。兩組第二階段權重值不同，「起點是否影響」未分離。
  （[exp-p0-training-improvements-ablation](experiments/exp-p0-training-improvements-ablation.md)）

---

## 索引：依變因種類查找

- **有無觀測資料（forward vs inverse）**：比較 1
- **優化器（Adam / SGD / SGD + momentum）**：比較 2、3
- **Weight decay**：比較 4
- **L-BFGS 第二階段**：比較 5、8
- **loss 權重（固定 vs gradnorm）**：比較 7、8
- **訓練改進方法（因果、Fourier、SOAP、BFGS 變體）**：比較 7
- **平凡解（C≡0）**：比較 2、3、5
- **方法論（續訓、可重現性）**：比較 6
