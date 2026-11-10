"""6A：不均勻流場下的殘差實作驗證（不需要訓練）

測試 1：manufactured solution 逐點比對
    h、u、v、τb、C 都是 (x, y, t) 的解析函數（隨空間與時間變化）。
    把精確的 C 當成「網路」丟進 sscpinn.physics.ssc_residual（autograd），
    與 sympy 依保守形式獨立推導的解析殘差逐點比對。
    負對照：流場函數對輸入座標 detach（h、u、v、τb 被當成常數特徵，
    即漏掉鏈鎖律項的常見實作錯誤），應明顯不符。

測試 2：守恆一致性
    滿足連續方程的流場（h(x,y) 變化、hu = q(y)、v = 0）＋ 常數 C、ws = 0、M = 0，
    殘差理論上處處為零。負對照一併報告。

用法：python experiments/check_6a_residual.py [--n 10000] [--out results/6a_residual_check]
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import sympy as sp
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sscpinn.physics import Hydro, ssc_residual  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LX, LY, LT = 1000.0, 400.0, 500.0
KX, KY, WS, ALPHA, M, TAU_CE = 2.0, 1.5, 1e-3, 1.2, 1e-4, 1.0

X, Y, T = sp.symbols("x y t", real=True)
PI = sp.pi


def fields_test1():
    h = 2 + sp.Rational(1, 2) * sp.sin(2 * PI * X / LX) * sp.cos(PI * Y / LY) + sp.Rational(1, 5) * sp.sin(2 * PI * T / LT)
    u = 1 + sp.Rational(3, 10) * sp.cos(2 * PI * X / LX) * sp.sin(PI * Y / LY) + sp.Rational(1, 10) * T / LT
    v = sp.Rational(1, 10) + sp.Rational(1, 20) * sp.sin(PI * X / LX) * sp.cos(2 * PI * Y / LY)
    tau = 2 + sp.Rational(1, 2) * sp.sin(PI * X / LX) * sp.cos(PI * Y / LY) + sp.Rational(3, 10) * T / LT  # ≥ 1.5 > τce
    C = sp.exp(-((X - 250 - sp.Rational(4, 5) * T) ** 2 + (Y - 180 - sp.Rational(1, 20) * T) ** 2) / (2 * 60 ** 2)) \
        * (1 + sp.Rational(1, 5) * sp.sin(2 * PI * T / LT))
    return dict(h=h, u=u, v=v, tau=tau, C=C), dict(ws=WS, M=M)


def fields_test2():
    h = 2 + sp.Rational(1, 2) * sp.sin(2 * PI * X / LX) * sp.cos(PI * Y / LY)
    q = 2 * (1 + sp.Rational(1, 5) * sp.sin(PI * Y / LY))
    return dict(h=h, u=q / h, v=sp.Integer(0), tau=None, C=sp.Rational(7, 10) + 0 * X), dict(ws=0.0, M=0.0)


def sympy_terms(f, ws, M):
    h, u, v, C = f["h"], f["u"], f["v"], f["C"]
    storage = sp.diff(h * C, T)
    adv = sp.diff(h * u * C, X) + sp.diff(h * v * C, Y)
    diff = sp.diff(h * KX * sp.diff(C, X), X) + sp.diff(h * KY * sp.diff(C, Y), Y)
    E = M * (f["tau"] / TAU_CE - 1) if (f["tau"] is not None and M > 0) else sp.Integer(0)
    D = ALPHA * ws * C
    # 「把 h、u、v 當常數」時的鏈鎖律項差額（只作為尺度參考）
    hs, us, vs = sp.symbols("hs us vs")
    const = (hs * sp.diff(C, T) + hs * us * sp.diff(C, X) + hs * vs * sp.diff(C, Y)
             - hs * KX * sp.diff(C, X, 2) - hs * KY * sp.diff(C, Y, 2))
    const = const.subs({hs: h, us: u, vs: v})
    chain = (storage + adv - diff) - const
    return {"storage": storage, "advection": adv, "diffusion": diff, "source": -E + D,
            "R": storage + adv - diff - E + D, "chain_rule_part": chain}


def to_torch_fn(expr, detach=False):
    f = sp.lambdify((X, Y, T), expr, modules=[{"exp": torch.exp, "sin": torch.sin, "cos": torch.cos}, "math"])

    def g(x, y, t):
        if detach:
            x, y, t = x.detach(), y.detach(), t.detach()
        out = f(x, y, t)
        out = out if torch.is_tensor(out) else float(out)
        return out + 0 * (x * x + y * y + t * t)  # 保留到二階導數的計算圖（不隨某座標變化的場也能被 autograd 微分）
    return g


def run(name, fields, params, n, dtype, seed=0):
    f = fields
    terms = sympy_terms(f, **params)
    gen = torch.Generator().manual_seed(seed)
    x = (torch.rand(n, generator=gen, dtype=torch.float64) * LX)
    y = (torch.rand(n, generator=gen, dtype=torch.float64) * LY)
    t = (torch.rand(n, generator=gen, dtype=torch.float64) * LT)
    num = {k: sp.lambdify((X, Y, T), e, "numpy") for k, e in terms.items()}
    ref = {k: np.broadcast_to(np.asarray(num[k](x.numpy(), y.numpy(), t.numpy()), dtype=np.float64), (n,))
           for k in terms}

    def autograd_R(detach):
        xx, yy, tt = (z.to(dtype).clone().requires_grad_(True) for z in (x, y, t))
        hyd = Hydro(h=to_torch_fn(f["h"], detach), u=to_torch_fn(f["u"], detach), v=to_torch_fn(f["v"], detach),
                    tau_b=to_torch_fn(f["tau"], detach) if f["tau"] is not None else None)
        net = to_torch_fn(f["C"])  # 精確解當成網路（不 detach：C 的導數本來就要算）
        R, _ = ssc_residual(net, hyd, xx, yy, tt, KX, KY, params["ws"], ALPHA, M=params["M"], tau_ce=TAU_CE)
        return R.detach().double().numpy()

    out = {"test": name, "dtype": str(dtype).replace("torch.", ""), "n_points": n,
           "term_scale_maxabs": {k: float(np.abs(v).max()) for k, v in ref.items()}}
    scale = float(np.abs(ref["R"]).max())
    rms_scale = float(np.sqrt((ref["R"] ** 2).mean()))
    for label, det in (("correct", False), ("negative_control", True)):
        Ra = autograd_R(det)
        err = np.abs(Ra - ref["R"])
        out[label] = {"max_abs_err": float(err.max()), "rms_abs_err": float(np.sqrt((err ** 2).mean())),
                      "max_rel_err": float(err.max() / scale) if scale > 0 else None,
                      "rms_rel_err": float(np.sqrt((err ** 2).mean()) / rms_scale) if rms_scale > 0 else None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "results", "6a_residual_check"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    res = []
    for name, fn in (("test1_manufactured", fields_test1), ("test2_conservation", fields_test2)):
        fields, params = fn()
        for dt in (torch.float64, torch.float32):
            r = run(name, fields, params, a.n, dt)
            res.append(r)
            c, nc = r["correct"], r["negative_control"]
            print(f"{name:20s} {r['dtype']:8s} 正確實作 max_abs={c['max_abs_err']:.3e} max_rel={c['max_rel_err']}  "
                  f"負對照 max_abs={nc['max_abs_err']:.3e} max_rel={nc['max_rel_err']}")
        print("   各項尺度（sympy max|·|）：", {k: f"{v:.3e}" for k, v in res[-1]["term_scale_maxabs"].items()})
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump({"params": dict(LX=LX, LY=LY, LT=LT, KX=KX, KY=KY, WS=WS, ALPHA=ALPHA, M=M, TAU_CE=TAU_CE),
                   "results": res}, fh, indent=2, ensure_ascii=False)
    print("結果輸出至", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
