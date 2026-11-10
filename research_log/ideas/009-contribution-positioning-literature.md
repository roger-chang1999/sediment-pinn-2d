---
type: idea
status: open
date: 2026-11-08
related: [001-origin-ssc-pinn-on-srh2d-hydraulics.md, 006-training-improvements-five-directions.md, 008-method-reverification-branches.md, ../papers/delcey2024-settling-velocity-pinn.md, ../papers/fanous2025-sundarbans-pinn.md, ../papers/lu-reservoir-flow-sediment-bed-pinn.md, ../papers/haddadchi2026-pinn-sed.md]
---

# 貢獻定位：目前的工作是不是我們自己的貢獻？（文獻搜尋，2026-11-08）

## 從哪裡來
使用者準備向他人說明進度時問：「這部分的研究有我們自己的貢獻嗎？還是這就是目前其他人論文的 method？」

## Claude 的回答（使用者未反駁，結論待使用者確認）
- **主線二目前的內容，方法都是別人的**：PINN 解平流擴散（Raissi 2019）、Adam → L-BFGS（標準做法）、gradnorm（[wang2023](../papers/wang2023-expert-guide.md)）、權重失衡（[wang2021](../papers/wang2021-gradient-pathologies.md) 已討論）、manufactured solution（數值驗證標準流程）。我們的部分是「在這個問題上的套用與誠實驗證」，適合寫成論文的方法與驗證章節，**不是研究貢獻**。這和 [idea 006](006-training-improvements-five-directions.md) 的提醒一致。
- 可能的貢獻在**主線一**（原始的研究問題），但需要文獻確認。

## 文獻搜尋（使用者同意）
三個問題與結論：

| 問題 | 找到的最接近文獻 | 結論 |
|---|---|---|
| 1. 有沒有 PINN 做二維水深平均懸浮泥砂，水理場來自數值模式？ | [fanous2025](../papers/fanous2025-sundarbans-pinn.md)（海岸，淺水＋泥砂全耦合，CFD 資料訓練，代理模型定位）；[lu 預印本](../papers/lu-reservoir-flow-sediment-bed-pinn.md)（水庫，水流–泥砂–河床耦合） | **沒有找到**「固定 SRH-2D／HEC-RAS／Delft3D 水理場、單向耦合、只學 C」的 PINN。現有的都是全耦合或代理模型 |
| 2. 有沒有在真實 SSC 觀測下做 PINN 參數反算並討論可辨識性？ | [delcey2024](../papers/delcey2024-settling-velocity-pinn.md)（合成資料、只反算沉速、觀測極密、無正式可辨識性分析）；[haddadchi2026](../papers/haddadchi2026-pinn-sed.md)（一維河網、Manawatu 河 3 站實測，全文未讀到） | **沒有找到**在實測 SSC、稀疏測站下同時反算 K、ws 並分析可辨識性的研究 |
| 3. 上述文獻的做法與限制 | 見各文獻筆記 | 兩篇最關鍵的（PINN-Sed、水庫預印本）被付費牆擋住，只有摘要或資料集頁面 |

**搜尋的限制**：只用一般網路搜尋（5 組查詢）；沒有查 Google Scholar、Web of Science；台灣本地的研究（中文期刊、學位論文）沒有搜尋。「沒找到」可能是研究缺口，也可能是搜尋方式不夠。

## 推論（推測，待讀全文確認）
可能的貢獻位置：
1. **單向耦合 SSC-PINN**：以檢定過的二維數值模式水理場驅動，正確處理不均勻流場的鏈鎖律項（6A 的基礎），而不是重學水理場。
2. **實測稀疏、高雜訊 SSC 下的參數反算與可辨識性**（6B 的延伸，對應原始構想的不確定度分析）：現有文獻多用密集合成資料。
3. **事件尺度輸砂量與跨事件驗證**（H2）：PINN-Sed 可能已在一維河網做到，需要讀全文比對。

## 下一步
- 請使用者提供（或從學校網路下載）：PINN-Sed（ASCE）、水庫預印本（SSRN）、Fanous 2025（Elsevier）的 PDF。
- 讀全文後再決定主線一的定位，以及論文要宣稱的貢獻。

## 更新（2026-11-08）：讀過三篇關鍵文獻後
使用者透過學校 VPN 用瀏覽器下載 PDF（命令列被出版社的反機器人驗證擋下），存於 `data/papers/`（不進版控）。Claude 讀了方法與結果章節。

| | 維度 | 水理場 | SSC 資料 | 反算參數 | 定位 |
|---|---|---|---|---|---|
| [PINN-Sed](../papers/haddadchi2026-pinn-sed.md) | 1D 河網 | **給定**（水文模式 TopNet） | **實測**，3 站、12 場洪水、依事件切分 | 否（係數固定為 1） | 推估河網 SSC 與事件輸砂量 |
| [Fanous 2025](../papers/fanous2025-sundarbans-pinn.md) | **2D 水深平均** | 網路學（全耦合），Thetis 輸出監督 | 無（濃度只由方程推得） | 否 | 代理模型 |
| [Lu 預印本](../papers/lu-reservoir-flow-sediment-bed-pinn.md) | 1D 水庫 | 網路學（全耦合＋河床） | 數值模式輸出（邊界為實測） | 否（經驗公式） | 代理模型、稀疏觀測外推 |
| [Delcey 2024](../papers/delcey2024-settling-velocity-pinn.md) | 2D 垂直剖面 NS | 網路學 | 合成、極密 | 只有沉速 | 方法驗證 |
| **我們（方案 A）** | **2D 水深平均** | **給定（SRH-2D）** | **實測，稀疏** | **K、ws 等** | 推估＋率定 |

**修正先前的推論**：
- 「單向耦合、給定水理場」**不是新的範式**：PINN-Sed 在一維就是這樣做，而且已有實測、依事件切分、事件輸砂量、和物理模式與 LSTM 對照。H2 在一維已被做過。
- 目前看起來仍未被做過的組合：**二維水深平均 × 給定二維水動力模式流場 × 實測稀疏 SSC × 參數反算與可辨識性**。三個關鍵文獻都沒有反算泥砂參數，也都沒有討論權重對反算的影響（PINN-Sed 權重全為 1，並列為未來工作）。
- 我們在主線二的觀察（H17：固定權重讓反算中的 PDE 失去作用）雖然機制已知，但在泥砂反算的情境下，可能成為論文中有用的方法學討論。

**仍有的限制**：搜尋範圍有限（5 組一般網路搜尋，沒查 Scholar、WoS、台灣本地研究）；Fanous 的結論、Lu 的雜訊實驗未讀。

## 更新（2026-11-08）：學術資料庫檢索
使用者：「透過這個領域的常用學術搜尋引擎找找看吧，我們要發論文的。」檢索方法、關鍵字、篩選與結果見 [search_log](../papers/search-2026-11-08/search_log.md)（OpenAlex、arXiv；Semantic Scholar 被限流；Scholar、WoS、台灣本地資料庫未查）。

- 去重後 122 篇物理資訊 ML × 輸送／泥砂相關文獻，**仍沒有找到**「二維水深平均 × 給定二維水動力模式流場 × 實測稀疏 SSC × 泥砂參數反算與可辨識性」。
- 新增兩篇相關文獻：[Radfar 2026](../papers/radfar2026-sparse-noisy-inverse-pinn-manning.md)（SWE 反算 Manning 的稀疏度 × 雜訊系統性測試，6B 的方法學範本）、[Zhao 2026](../papers/zhao2026-pinn-river-pollutant-source-tracing.md)（WRR，河道污染源反算）。
- 4 篇 2026 年文獻只有標題（海洋 SSC 雙網路 PINN、一維水–泥砂耦合 PINN、植生渠道擴散係數反算、河口絮凝參數化 PINN），需要讀才能確認不重疊。
