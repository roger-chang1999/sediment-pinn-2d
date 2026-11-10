"""二維水深平均懸浮載守恆方程殘差

    ∂(hC)/∂t + ∂(huC)/∂x + ∂(hvC)/∂y
        = ∂(h Kx ∂C/∂x)/∂x + ∂(h Ky ∂C/∂y)/∂y + E − D + S_ext

    D = α_d · w_s · C
    E = M · max(τ_b/τ_ce − 1, 0)     （黏性泥砂示例，可關閉）

h、u、v（以及 τ_b）是 (x, y, t) 的「可微函數」，殘差直接以保守形式
對 hC、huC 做自動微分，所以 ∂h/∂x、∂u/∂x 等項會自動透過鏈鎖律進入，
避免「把 h、u 當常數特徵」而漏掉鏈鎖律項的錯誤。
"""
from dataclasses import dataclass
from typing import Callable, Optional

import torch


def grad(f, x):
    return torch.autograd.grad(f, x, torch.ones_like(f), create_graph=True)[0]


@dataclass
class Hydro:
    """已知水理場：每個欄位都是 (x, y, t) -> tensor 的可微函數。"""
    h: Callable
    u: Callable
    v: Callable
    tau_b: Optional[Callable] = None  # Pa，侵蝕用


def ssc_residual(net, hyd: Hydro, x, y, t, Kx, Ky, ws, alpha_d=1.0,
                 M=0.0, tau_ce=1.0, S_ext=None):
    """回傳殘差 R_C 與 C（單位：kg/(m²·s) 與 kg/m³）。x, y, t 需 requires_grad。"""
    C = net(x, y, t)
    h, u, v = hyd.h(x, y, t), hyd.u(x, y, t), hyd.v(x, y, t)

    hC = h * C
    storage = grad(hC, t)
    adv = grad(hC * u, x) + grad(hC * v, y)

    Cx, Cy = grad(C, x), grad(C, y)
    diff = grad(h * Kx * Cx, x) + grad(h * Ky * Cy, y)

    D = alpha_d * ws * C
    if hyd.tau_b is not None and M > 0:
        E = M * torch.relu(hyd.tau_b(x, y, t) / tau_ce - 1.0)
    else:
        E = torch.zeros_like(C)
    S = S_ext(x, y, t) if S_ext is not None else 0.0

    R = storage + adv - diff - E + D - S
    return R, C


def total_mass(net, hyd: Hydro, t, xb, yb, n=200):
    """M(t) = ∫Ω h C dA（矩形域中點積分），單位 kg。"""
    xs = torch.linspace(xb[0], xb[1], n + 1, device=t.device)
    ys = torch.linspace(yb[0], yb[1], n + 1, device=t.device)
    xc, yc = 0.5 * (xs[1:] + xs[:-1]), 0.5 * (ys[1:] + ys[:-1])
    dA = (xs[1] - xs[0]) * (ys[1] - ys[0])
    X, Y = torch.meshgrid(xc, yc, indexing="ij")
    X, Y = X.reshape(-1), Y.reshape(-1)
    out = []
    for ti in t:
        T = torch.full_like(X, float(ti))
        out.append((hyd.h(X, Y, T) * net(X, Y, T)).sum() * dA)
    return torch.stack(out)
