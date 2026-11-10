---
type: paper
status: done
date: 2026-11-08
source: 檢索紀錄（不是單篇文獻）
related: [../../ideas/009-contribution-positioning-literature.md]
---

# 文獻檢索紀錄（2026-11-08）

觸發：[idea 009](../../ideas/009-contribution-positioning-literature.md)（貢獻定位）。使用者：「透過這個領域的常用學術搜尋引擎找找看吧，我們要發論文的。」

## 資料庫與方法

| 資料庫 | 方式 | 狀態 |
|---|---|---|
| OpenAlex | REST API：關鍵字搜尋（每組 25 筆）＋ `title_and_abstract.search` 過濾（每組 50 筆，依引用數排序）＋ 7 篇種子論文的**被引用追蹤**（`cites:`，每篇 100 筆） | 成功 |
| arXiv | export API（每組 15 筆） | 成功 |
| Semantic Scholar | Graph API | **全部被限流（HTTP 429）**，沒有結果 |
| Google Scholar | 不支援程式化查詢 | 未查 |
| Web of Science、Scopus | 需要機構登入 | 未查 |
| 華藝、臺灣博碩士論文知識加值系統 | 需要瀏覽器 | **未查（台灣本地研究的缺口）** |

腳本：`tools/literature_search/lit_search.py`（第一輪）、`lit_search2.py`（第二輪）。原始結果：本資料夾的兩個 JSON。

### 關鍵字
- 第一輪（10 組）：PINN × {suspended sediment concentration；sediment transport river；sediment transport 2D shallow water；advection diffusion inverse parameter river；settling velocity sediment；reservoir sedimentation；turbidity；water quality transport river inverse；depth-averaged transport numerical model velocity field；dispersion coefficient estimation river field data}
- 第二輪過濾（7 組）：physics-informed sediment／suspended／turbidity；PINN sediment／suspended；physics-informed advection-dispersion river；PINN sediment concentration inverse
- 被引用追蹤的種子：PINN-Sed、Delcey 2024、He & Tartakovsky 2021、Ohara 2024、Niu 2023、Bertels & Willems 2023、Fanous 2025

### 篩選
1. 去重後共 165（第一輪）＋ 426（第二輪）篇。
2. 標題需同時包含「physic／PINN／neural／machine learning」與「sediment／suspend／turbid／settl／silt／floc／reservoir／river／dispersion／advection／pollut／estuar／morpho／solute／contaminant／water quality／shallow water／Saint」，年份 ≥ 2019：剩 **122 篇**。
3. Claude 依標題挑出 15 篇抓 OpenAlex 摘要（`shortlist_abstracts.txt`），其中 7 篇 OpenAlex 沒有摘要。

## 結果：和我們的定位相關的文獻

| 文獻 | 類型 | 與我們的關係 | 讀到的程度 |
|---|---|---|---|
| [PINN-Sed](../haddadchi2026-pinn-sed.md)（J. Hydraul. Eng. 2026） | 1D、給定水理、實測 SSC | 最接近；H2 在一維已做過 | 全文 |
| [Fanous 2025](../fanous2025-sundarbans-pinn.md)（Ecol. Inform.） | 2D、全耦合、濃度無資料 | 唯一的 2D 泥砂 PINN | 方法與結果 |
| [Lu 預印本](../lu-reservoir-flow-sediment-bed-pinn.md)（SSRN 2026） | 1D 水庫、全耦合 | 水庫題目 | 方法與資料 |
| [Delcey 2024](../delcey2024-settling-velocity-pinn.md)（CMAME） | 反算沉速、合成 | 泥砂參數反算 | Sec. 1–3 |
| [Radfar 2026](../radfar2026-sparse-noisy-inverse-pinn-manning.md)（Phys. Fluids） | SWE 反算 Manning，系統性測試稀疏度與雜訊 | **6B 的方法學範本** | 摘要 |
| [Zhao 2026](../zhao2026-pinn-river-pollutant-source-tracing.md)（WRR） | 河道污染源反算（強度、位置） | 河川輸送反算 | 摘要 |
| He & Tartakovsky 2021（WRR，引用 153） | 地下水 ADE 正、反問題 | 輸送反問題的經典 | 摘要 |
| Panahi 2026（arXiv） | 貝氏 PINN 量化參數不可辨識性 | 對應 [idea 005](../../ideas/005-inverse-as-calibration-and-statistics.md) 的統計推論 | 摘要 |
| Qiu et al. 2026（SSRN）「Dual-Network PINNs … Marine Suspended Sediment Concentration」 | 海洋 SSC | **可能很相關，但沒有摘要** | 只有標題 |
| Zhang X. et al. 2026（SSRN）「PINN modeling of coupled 1D water–sediment systems」 | 1D 水–泥砂耦合 | 可能相關 | 只有標題 |
| Zhang J. et al. 2026（J. Hydrol.）「vegetated channels … longitudinal dispersion coefficient … PINN」 | 反算縱向擴散係數 | 擴散係數反算 | 只有標題 |
| Wu et al. 2025（Water Research）「suspended floc size … parameterized PINNs」 | 河口絮凝 | 參數化 PINN | 只有標題 |

其他（相關性較低，未細看）：PINN 解垂直一維泥砂混合方程（Zhang S. 2024 PoF）、Navier–Stokes 型 PINN 河道淤積（Omarova 2023、Urmashev 2024）、2D SWE PINN（多篇）、SSC 預報的物理資訊 ML（非 PDE 型，如 rating-curve 約束）。

## 結論（待使用者確認）
- 仍**沒有找到**「二維水深平均 × 給定二維水動力模式流場 × 實測稀疏 SSC × 泥砂參數反算與可辨識性」的研究。
- 6B 的設計可以參考 Radfar 2026 的系統性做法（稀疏度 × 雜訊 × 觀測變數類型），但他們是水理參數（Manning），不是泥砂。
- 缺口：Semantic Scholar 被限流；Google Scholar、WoS、Scopus、台灣本地資料庫未查；4 篇只有標題的 2026 年文獻需要讀。
