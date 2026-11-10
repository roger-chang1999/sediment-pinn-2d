---
type: idea
status: open
date: 2026-11-07
related: [003-pde-loss-small-not-correct.md, ../experiments/exp-optimizer-sgd-vs-adam-and-weight-decay.md, ../papers/rathore2024-loss-landscape.md, 006-training-improvements-five-directions.md]
---

# L-BFGS 為什麼有效：修正病態的曲率，不是修正抽樣

## 從哪裡來
P0 中 L-BFGS 的效果非常大，但並不一致：
- Adam 第一階段 73% → L-BFGS 後 2.6%
- SGD（lr=1e-3）第一階段 88% → L-BFGS 後 16.1%
- SGD + momentum 崩到 C≡0 → L-BFGS 後仍是 100%
- 反算 Adam：第一階段 5.87%（14000 步）→ L-BFGS 後 6.17%，**略為變差**，K 從 1.901 變成 1.913

## 機制論證
PINN 的 loss 地形是**病態的（ill-conditioned）**：PDE 殘差含二階導數，會把參數的微小變化放大；各項 loss 尺度差異大。地形像「又窄又長的山谷」，一階方法（Adam、SGD）在兩側山壁間來回彈跳，沿谷底前進很慢。

L-BFGS 從最近 m 步（我們用 m = 50）的「位移」和「梯度變化」推估 Hessian 的逆矩陣，在曲率大的方向走小步、在曲率小的方向走大步，所以能沿著谷底前進。網路有 16,961 個參數，完整 Hessian 有約 2.9 億個元素，所以只能近似，不能直接算。

## 由這個論證推出的三個限制（和實驗一致）
1. **需要固定的 loss**：它要比較前後步的梯度差，每步重抽配點會讓推估失準 → 程式在 L-BFGS 階段改用固定配點。
2. **需要好的起點**：它擅長在山谷裡走到底，不擅長找到正確的山谷 → Adam 起點 2.6%、SGD 起點 16.1%。
3. **梯度消失時無能為力** → 救不了 C≡0 的平凡解。

## 尚未解釋的地方
- 反算模式下 L-BFGS 讓 relL2 略為變差（5.87% → 6.17%）。可能的原因：L-BFGS 用固定配點，對觀測雜訊（5%）過擬合；或者 relL2 已經被觀測雜訊限制住。單一 seed，無法判斷是否只是雜訊。
- 「Adam 卡在 73% 是因為病態」和「卡在 73% 是因為傳播失敗（[003](003-pde-loss-small-not-correct.md)）」**兩者不互斥**，目前無法區分各自貢獻多少。因果訓練實驗（[006](006-training-improvements-five-directions.md)）可以部分回答：如果加了因果權重，Adam 第一階段就大幅改善，代表傳播失敗是主因。

## 文獻
[rathore2024](../papers/rathore2024-loss-landscape.md)（ICML 2024）用 loss 地形分析得到同樣的結論：Adam + L-BFGS 優於任一單獨使用，原因是微分算子造成的病態性。
