import math

import torch
import torch.nn as nn


class SSCNet(nn.Module):
    """Cθ(x,y,t) = C_ref · softplus(Nθ(x*, y*, t*))

    輸入為「物理座標」(m, m, s)，網路內部做正規化到 [-1,1]，
    因此對輸入做自動微分得到的就是物理單位的導數 ∂C/∂x、∂C/∂t。

    fourier_sigma > 0 時，正規化後的輸入先經隨機 Fourier 映射
        γ(z) = [cos(2π zB), sin(2π zB)],  B ~ N(0, σ²)，形狀 (d_in, fourier_m)
    （Tancik et al. 2020）。B 由獨立的亂數產生器產生，不影響其餘權重的初始化。
    """

    def __init__(self, bounds, c_ref=1.0, width=64, depth=5, act=nn.Tanh,
                 fourier_sigma=0.0, fourier_m=64, fourier_seed=0):
        super().__init__()
        lo = torch.tensor([b[0] for b in bounds], dtype=torch.float32)
        hi = torch.tensor([b[1] for b in bounds], dtype=torch.float32)
        self.register_buffer("lo", lo)
        self.register_buffer("hi", hi)
        self.c_ref = c_ref
        d_in = len(bounds)
        layers = []
        for _ in range(depth):
            layers += [nn.Linear(d_in if not layers else width, width), act()]
        layers.append(nn.Linear(width, 1))
        self.net = nn.Sequential(*layers)
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)

        self.fourier = fourier_sigma > 0
        if self.fourier:
            g = torch.Generator().manual_seed(10_000 + fourier_seed)
            B = torch.randn(d_in, fourier_m, generator=g) * fourier_sigma
            self.register_buffer("B", B)
            # 第一層輸入維度改為 2m（權重仍用上面的全域亂數初始化流程，之後重設形狀）
            first = nn.Linear(2 * fourier_m, width)
            nn.init.xavier_normal_(first.weight)
            nn.init.zeros_(first.bias)
            self.net[0] = first

    def forward(self, x, y, t):
        X = torch.stack([x, y, t], dim=-1)
        Xn = 2.0 * (X - self.lo) / (self.hi - self.lo) - 1.0
        if self.fourier:
            z = 2 * math.pi * Xn @ self.B
            Xn = torch.cat([torch.cos(z), torch.sin(z)], dim=-1)
        return self.c_ref * nn.functional.softplus(self.net(Xn)).squeeze(-1)
