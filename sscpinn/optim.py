"""PINN 用的進階優化器（自行實作，不引入外部程式碼）。

SOAP（Vyas et al. 2024；PINN 應用見 Wang et al. 2025, arXiv 2502.00604）
    對每個 2D 權重 W (m×n) 維護 Shampoo 預條件矩陣
        L ← β₂L + (1−β₂) G Gᵀ,   R ← β₂R + (1−β₂) Gᵀ G
    其特徵向量 Q_L、Q_R 每 precond_freq 步以 eigh 重算；在 Q_L、Q_R 旋轉後的座標系中跑 Adam：
        m ← β₁m + (1−β₁)G（原座標）；  v ← β₂v + (1−β₂)(Q_Lᵀ G Q_R)²（旋轉座標）
        ΔW = Q_L [ (Q_Lᵀ m Q_R)/(1−β₁ᵗ) / (sqrt(v/(1−β₂ᵗ)) + ε) ] Q_Rᵀ
    1D 參數（bias、反算參數）退化為一般 Adam。
    與官方實作的差異（簡化）：特徵基更新時，v 以「平方後的基底轉換矩陣」近似投影到新基底；
    官方實作以 power iteration + QR 更新基底並重排 v。第一步只建立預條件矩陣、不更新參數（同官方）。

SelfScalingBFGS
    完整矩陣的 BFGS 逆 Hessian 近似 H（n×n，GPU 上就地更新），strong-Wolfe line search
    （沿用 torch.optim.lbfgs 的 _strong_wolfe）。self_scaling=True 時每步先把 H 乘以
    τ = min(1, sᵀy / yᵀHy)（Oren–Luenberger 式自我縮放），再做標準 BFGS 更新：
        H ← τH;  H ← H − (s(Hy)ᵀ + (Hy)sᵀ)/sᵀy + (1 + yᵀHy/sᵀy) s sᵀ/sᵀy
    這是自我縮放 BFGS 的一種常見形式，**不等同** Urbán et al. (2025) 的 SSBroyden 完整公式。
"""
import math

import torch
from torch.optim.lbfgs import _strong_wolfe


class SOAP(torch.optim.Optimizer):
    def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0,
                 precond_freq=10):
        super().__init__(params, dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay,
                                      precond_freq=precond_freq))

    @staticmethod
    def _eigvecs(M):
        # 特徵值由大到小排序；加極小對角項避免完全退化
        _, Q = torch.linalg.eigh(M + 1e-30 * torch.eye(M.shape[0], device=M.device, dtype=M.dtype))
        return Q.flip(-1)

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for group in self.param_groups:
            b1, b2 = group["betas"]
            lr, eps, wd, freq = group["lr"], group["eps"], group["weight_decay"], group["precond_freq"]
            for p in group["params"]:
                if p.grad is None:
                    continue
                g = p.grad
                st = self.state[p]
                if not st:
                    st["step"] = 0
                    st["m"] = torch.zeros_like(p)
                    st["v"] = torch.zeros_like(p)
                    if p.dim() == 2:
                        st["L"] = g @ g.T
                        st["R"] = g.T @ g
                        st["QL"] = self._eigvecs(st["L"])
                        st["QR"] = self._eigvecs(st["R"])
                        continue  # 第一步只建立預條件矩陣
                st["step"] += 1
                t = st["step"]
                m, v = st["m"], st["v"]
                m.mul_(b1).add_(g, alpha=1 - b1)
                if p.dim() == 2:
                    QL, QR = st["QL"], st["QR"]
                    g_rot = QL.T @ g @ QR
                    m_rot = QL.T @ m @ QR
                    v.mul_(b2).addcmul_(g_rot, g_rot, value=1 - b2)
                    upd = QL @ ((m_rot / (1 - b1 ** t)) / ((v / (1 - b2 ** t)).sqrt() + eps)) @ QR.T
                    st["L"].mul_(b2).add_(g @ g.T, alpha=1 - b2)
                    st["R"].mul_(b2).add_(g.T @ g, alpha=1 - b2)
                    if t % freq == 0:
                        QLn, QRn = self._eigvecs(st["L"]), self._eigvecs(st["R"])
                        PL, PR = (QLn.T @ QL) ** 2, (QRn.T @ QR) ** 2
                        v.copy_(PL @ v @ PR.T)
                        st["QL"], st["QR"] = QLn, QRn
                else:
                    v.mul_(b2).addcmul_(g, g, value=1 - b2)
                    upd = (m / (1 - b1 ** t)) / ((v / (1 - b2 ** t)).sqrt() + eps)
                if wd:
                    p.mul_(1 - lr * wd)
                p.add_(upd, alpha=-lr)
        return loss


class SelfScalingBFGS:
    """完整矩陣（自我縮放）BFGS。closure() 需清零梯度、計算 loss 並 backward，回傳 loss。"""

    def __init__(self, params, max_iter=500, self_scaling=True, tol_grad=1e-9, tol_change=1e-12):
        self.params = [p for p in params if p.requires_grad]
        self.n = sum(p.numel() for p in self.params)
        self.max_iter, self.self_scaling = max_iter, self_scaling
        self.tol_grad, self.tol_change = tol_grad, tol_change
        self.n_resets = 0
        self.n_iters = 0
        self.n_evals = 0

    def _get(self):
        return torch.cat([p.detach().reshape(-1) for p in self.params])

    def _set(self, x):
        i = 0
        with torch.no_grad():
            for p in self.params:
                k = p.numel()
                p.copy_(x[i:i + k].view_as(p))
                i += k

    def _grad(self):
        return torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).reshape(-1)
                          for p in self.params])

    def _eval(self, closure, x):
        self._set(x)
        with torch.enable_grad():
            f = float(closure())
        self.n_evals += 1
        return f, self._grad()

    def step(self, closure):
        x = self._get()
        f, g = self._eval(closure, x)
        H = None  # 第一次更新前以縮放單位矩陣初始化
        dev = x.device
        for k in range(self.max_iter):
            if g.abs().max() <= self.tol_grad:
                break
            d = -g if H is None else -(H @ g)
            gtd = float(g @ d)
            if gtd > -1e-20:  # 非下降方向：重設
                H, d, gtd = None, -g, float(-(g @ g))
                self.n_resets += 1
            t0 = min(1.0, 1.0 / float(g.abs().sum())) if H is None else 1.0
            f_new, g_new, t, _ = _strong_wolfe(lambda x_, t_, d_: self._eval(closure, x_ + t_ * d_),
                                               x, t0, d, f, g, gtd)
            s = t * d
            y = g_new - g
            sy = float(s @ y)
            x = x + s
            df = abs(f_new - f)
            f, g = f_new, g_new
            self.n_iters = k + 1
            if sy > 1e-12:
                if H is None:
                    H = torch.eye(self.n, device=dev) * (sy / float(y @ y))
                Hy = H @ y
                yHy = float(y @ Hy)
                tau = min(1.0, sy / yHy) if self.self_scaling else 1.0
                if tau != 1.0:
                    H.mul_(tau); Hy.mul_(tau); yHy *= tau
                H.addr_(s, Hy, alpha=-1.0 / sy)
                H.addr_(Hy, s, alpha=-1.0 / sy)
                H.addr_(s, s, alpha=(1.0 + yHy / sy) / sy)
            if df < self.tol_change:
                break
        self._set(x)
        del H
        torch.cuda.empty_cache()
        return f
