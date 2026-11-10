---
type: idea
status: open
date: 2026-11-08
related: [006-training-improvements-five-directions.md, 007-mainline1-decisions-plan-a-method-first.md, ../experiments/exp-p0-training-improvements-ablation.md, ../research_tree_overview.md]
---

# 方法結論的重新驗證：三個分枝掛在 P0 方法確認 node 底下（主線二，服務主線一）

## 從哪裡來
P0 訓練改進 node 結束（[實驗紀錄](../experiments/exp-p0-training-improvements-ablation.md)，結論 2026-11-08 經使用者確認）後，Claude 依流程提出三個下一步選項 A、B、C，並建議先 A 後 B。

## 使用者的決定（2026-11-08）
「ABC 都定為第一個 node 的 tree 分枝，因為基本上都屬於方法結論的多項重新驗證。」

Claude 的理解（已在對話中說明）：A、B、C 不另開成獨立的新研究問題，而是**掛在「P0 方法確認」底下的三個分枝**。它們的目的都是確認方法可用，對應 [idea 007](007-mainline1-decisions-plan-a-method-first.md) 的「先確認模型方法」；不是新的研究方向。

| 分枝 | 重新驗證的對象 | 對應假設 | 主張類型 |
|---|---|---|---|
| **6A 不均勻流場的實作驗證** | H4 的限制：h、u 隨空間變化時的鏈鎖律項 | H4 | 實作類（需有已知答案的驗證測試） |
| **6B 雜訊觀測下的反算** | 新基準（H18）在雜訊 5／10／20% × 測站數下能否回收 K；H19「loss 越低 K 越錯」；不依賴正確答案的判斷方式 | H11、H18、H19 | 實驗類 |
| **6C 未決項目** | 依原文重做因果訓練；SOAP + gradnorm；起點 vs 權重 | H12、H15、H16、H20 | 實驗類 |

- 原本的分支 4（H11 可識別性）併入 6B。
- 每個分枝仍各自經過關卡一（設計討論）、關卡二（多輪分析）。
- 執行順序：待使用者決定（Claude 建議 6A → 6B → 6C：6A 便宜且是正確性問題，鏈鎖律若有錯會影響 6B 的所有結論；6C 對主線一的價值最低）。
