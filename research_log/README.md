# Research Log — 想法演變 → 文獻 → 實驗 → 新假設

這個目錄記錄 SSC-PINNs 研究的思考鏈路，讓「為什麼做這個實驗」和「這篇論文為什麼相關」不會隨時間遺忘。檔案之間用相對連結互相引用：

```
research_log/
├── README.md                  本檔：使用說明
├── hypotheses.md              中樞索引：所有假設的狀態（open/confirmed/refuted）
├── methods.md                 評估方法登記表：每個數字是用哪種協定量出來的、常見陷阱
├── research_tree_overview.md  研究樹：假設 → 實驗設計 → 結果 → 推論 ⟹ 下一個假設
├── comparison_catalog.md      比較實驗總目錄：每組「A vs B」用統一格式列出
├── ideas/NNN-slug.md          想法演變：依時間序編號，每篇是一次「思考轉折」
├── papers/slug.md             文獻筆記：一篇論文一個檔案
└── experiments/exp-slug.md    實驗記錄：一組實驗一個檔案
```

引用或比較任何 relL2、質量守恆誤差、K/w_s 估計值之前，先看 [methods.md](methods.md) 確認是用哪個協定量的。**不同協定的數字不能放進同一張表比較**（例如「第一階段後 relL2」和「L-BFGS 後 relL2」）。

## ⚠️ 最重要的使用原則：不要混淆兩條因果線

這個研究目前有**兩條獨立的想法線**。寫新內容前，先想清楚它屬於哪一條：

- **主線一（研究的原始動機）**：[ideas/001](ideas/001-origin-ssc-pinn-on-srh2d-hydraulics.md)。以 SRH-2D 二維水理場驅動 SSC-PINNs，融合稀疏 SSC 觀測與泥砂守恆，推估 C(x,y,t)、斷面 Qs 和事件累積量 Ms。這是專案一開始就設定的研究問題，相關文獻見 [papers/niu2023-1d-coupled-flow-transport](papers/niu2023-1d-coupled-flow-transport.md)、[papers/haddadchi2026-pinn-sed](papers/haddadchi2026-pinn-sed.md)。
- **主線二（實作後衍生的方法論問題）**：[ideas/002](ideas/002-p0-analytic-verification-design.md) → [003](ideas/003-pde-loss-small-not-correct.md) → [004](ideas/004-lbfgs-curvature-not-sampling.md) → [006](ideas/006-training-improvements-five-directions.md)。在 P0 解析解驗證中，**實際跑過才發現**的 PINN 訓練可靠性問題：傳播失敗、平凡解、優化器選擇。相關文獻見 [papers/rathore2024-loss-landscape](papers/rathore2024-loss-landscape.md)、[papers/wang2024-causal-training](papers/wang2024-causal-training.md)。

**兩條線不要混在一起寫進論文。** 主線二是「讓主線一可行的工具與必要檢核」，不是研究的原始目的。如果把「優化器 X 讓 P0 誤差從 2.6% 降到 0.1%」包裝成本研究的主要貢獻，會偏離原始的研究問題；而且真實資料的觀測誤差（10–20%）很可能蓋過這種精度差異，詳見 [ideas/006](ideas/006-training-improvements-five-directions.md) 最後一段。

另一個常見混淆：**P0 是合成資料，真實結構已知**。P0 的反算能找回 K、w_s，不代表真實河川也能找到「正確」參數，詳見 [ideas/005](ideas/005-inverse-as-calibration-and-statistics.md)。

## 使用流程

1. **想法演變**（`ideas/`）：每次思考出現轉折就新增一篇，檔名遞增編號 `NNN-slug.md`。內容包含：這個想法從哪個假設或實驗而來、屬於主線一還是主線二（或開啟新的主線）、接下來想驗證什麼。
2. **文獻**（`papers/`）：讀到相關論文就新增筆記，記錄：問題設定（PDE、維度、資料）、跟我們的可比性、關鍵數字、跟哪條線或哪個假設有關。**務必記錄「不可比之處」**，並註明資訊來源（全文、摘要或二手摘要）。
3. **實驗**（`experiments/`）：每次產生新數據就新增一篇，記錄：對應哪個想法、用了什麼腳本和設定（含完整指令與結果路徑）、結果摘要、支持或推翻了哪個假設、限制。
4. **假設索引**（`hypotheses.md`）：所有假設的中樞列表，依主線分開。最上面永遠是「當前最前沿的待分析問題」。想知道「我們現在站在哪」，先看這個。
5. **總覽**：新的比較結果同步加進 `comparison_catalog.md`；假設狀態改變時，同步更新 `research_tree_overview.md`。

## 連結慣例

使用相對 markdown 連結（`[標題](../papers/xxx.md)`），每篇檔案開頭放 frontmatter：

```markdown
---
type: idea | paper | experiment
status: open | confirmed | refuted | superseded | done | planned   # idea 用前四種；experiment 用 done/planned
date: YYYY-MM-DD
related: [連到其他檔案的相對路徑列表]
---
```

實驗檔案另外記錄 `results:`（結果資料夾路徑）和 `seeds:`。

舊的想法即使被推翻也保留（append-only），標記 `status: refuted` 即可，在文末加「更新」段落說明。這樣才看得出想法演變的軌跡，**不要回頭改寫舊內容**。

## 與程式碼、結果的對應

- 實驗腳本：`../experiments/*.py`
- 結果：`../results/<設定標籤>/seed<k>/`（`config.json`、`summary.json`、`ckpt_stage1.pt`、`final.pt`、圖）
- 每篇實驗記錄都要寫出**可重現的完整指令**和對應的結果路徑。

## 給審查者的指引（人或 agent 都適用）

這份紀錄遵循「知識來源追溯（epistemic provenance）」的原則：每個主張都要能追溯它從哪裡來、憑什麼成立、怎麼被改變。審查時，不需要任何額外工具，照下列順序進行即可。

**從哪裡開始讀**：`hypotheses.md`（現況）→ `research_tree_overview.md`（推論鏈）→ 個別 `experiments/` 與 `ideas/`。引用數字前先查 `methods.md`。

**核心原則**（審查時逐項對照）：
1. **因果線分離**：每篇 idea 標明屬於哪條線；事後的發現不能寫成原始動機。
2. **只追加**：被推翻的 idea 保留並標 `refuted`，新證據寫在文末「更新」段落，不改原文。
3. **先寫預測**：實驗記錄的預測要在執行前寫下，並經研究者確認。
4. **協定登記**：每個數字都能對應到 `methods.md` 的某個協定與版本；不同協定的數字不放在同一張表比較。
5. **來源強度**：文獻的 `source` 標明讀過全文、摘要或憑記憶；被引用、比較或依其實作之前必須讀完全文。實驗寫明限制。
6. **可重現**：實驗記錄有完整指令、程式版本、結果路徑、seed。
7. **狀態詞彙**：open → proposed → planned → supported / confirmed / refuted / superseded。confirmed 的條件：實作類需通過有已知答案的驗證測試；實驗類需多 seed 或多條件；依賴文獻者維持 supported，除非我們自己也獨立驗證。
8. **決策來源**：設計決策記錄決定者；「未經討論」的預設值要標明。

**審查檢查清單**：
- [ ] 假設狀態和實驗結果一致（confirmed 是否名副其實、supported 的限制是否寫清楚）
- [ ] hypotheses.md 與 comparison_catalog.md 的結論沒有比實驗記錄更強
- [ ] 沒有因果線混淆
- [ ] 比較表中的數字協定一致
- [ ] 被推翻的想法有保留，沒有被改寫（可用 `git log -p` 查看）
- [ ] 未經討論的決策中，有哪些會影響目前的結論
- [ ] 被引用、比較或依其實作的文獻，都已讀過全文

如果有安裝 epistemic-provenance skill（https://github.com/roger-chang1999/epistemic-provenance），可以用它的 `scripts/log_status.py` 產生狀態總表作為起點。
