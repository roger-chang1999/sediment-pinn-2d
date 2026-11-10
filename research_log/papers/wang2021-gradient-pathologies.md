---
type: paper
title: "Understanding and mitigating gradient flow pathologies in physics-informed neural networks"
authors: S. Wang, Y. Teng, P. Perdikaris
venue: SIAM Journal on Scientific Computing, 43(5) (2021)
source: 部分讀過全文（2026-11-08，子代理讀取 arXiv HTML v1；Sec. 1–2.4 逐字，Algorithm 1 與 Sec. 3–4 只有摘要轉述）
related: [../ideas/006-training-improvements-five-directions.md]
---

# Wang, Teng & Perdikaris (2021)：梯度病理與自動 loss 權重

## 核心
- PINN 的各項 loss 反向傳播的梯度大小差異很大，PDE 殘差項通常主導，邊界/初始條件項被忽略。
- 提出 **learning rate annealing**：依各項 loss 對參數的梯度統計量（原文用 PDE 項梯度的最大值，除以其他項梯度的平均值）動態調整權重，並用移動平均平滑。
- 另外提出 modified MLP 架構。

後續工作（同一團隊）把權重改成用**梯度範數**平衡，並發展出 NTK 權重（Wang, Yu, Perdikaris 2022, JCP）。

## 和我們的關係
- [idea 006](../ideas/006-training-improvements-five-directions.md) 第 2 項的基礎。
- 我們目前的權重（pde 1、ic 100、bc 10、obs 100）是手動設的。換到真實資料（不同的 loss 尺度、觀測數量）時一定要重調，自動權重可以避免這件事。

## 實作要注意
- 每 N 步才更新一次權重（例如每 100 步），因為要多做幾次反向傳播計算各項梯度。
- 權重本身要 stop-gradient。
- 先決定用哪個版本（max/mean 或梯度範數），並在實驗記錄中寫清楚。

## 不可比之處
- 原文測試題是 Helmholtz、Klein–Gordon、NS 頂蓋驅動流等。

## 全文核對（2026-11-08）
- Algorithm 1（摘要轉述，未逐字核對）：λ̂_i = max|∇L_r| / mean|∇L_i|，λ_i = (1−α)λ_i + αλ̂_i（α 乘在**新**估計上），α=0.9；只調整資料／邊界項，殘差權重固定為 1。
- **我們的 gradnorm 公式不是這一篇**，而是 [wang2023-expert-guide](wang2023-expert-guide.md) 的梯度範數版。兩篇的 α 慣例相反。
