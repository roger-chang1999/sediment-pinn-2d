"""P0｜解析解驗證：二維高斯泥砂團的平流–擴散–沉降

均勻水理場 h, u, v 為常數、Kx = Ky = K、D = α_d w_s C、E = 0：
    C(x,y,t) = C0 · σ0²/σ² · exp(−[(x−x0−ut)² + (y−y0−vt)²] / 2σ²) · exp(−α_d w_s t / h)
    σ² = σ0² + 2Kt
全域質量 M(t) = M0 · exp(−α_d w_s t / h)（泥砂團未離開計算域時）。

模式：
  forward : 已知 K、w_s，只用 PDE + IC + BC 求 C（檢查自動微分與守恆式）
  inverse : K、w_s 未知，加入少量測站 SSC（含雜訊），同時反推參數

訓練：第一階段（Adam / SGD / SOAP）→ 第二階段（L-BFGS / BFGS / 自我縮放 BFGS）
訓練改進選項（research_log/ideas/006，一次只開一項做消融）：
  --causal-eps ε        #1 因果訓練（時間分段權重 w_i = exp(−ε[L_ic + Σ_{k<i} L_k])，只用於第一階段）
  --weighting gradnorm  #2 依梯度範數自動平衡各項 loss 權重
  --fourier-sigma σ     #3 輸入 Fourier features
  --opt soap            #4 SOAP 取代 Adam
  --stage2 ssbfgs       #5 完整矩陣自我縮放 BFGS 取代 L-BFGS（可用 --stage1-from 共用基準的第一階段）

用法：
  python experiments/p0_analytic.py --mode forward --seed 0
  python experiments/p0_analytic.py --mode forward --seed 0 --iters 30000 --resume   # 續訓到 30000 步
  python experiments/p0_analytic.py --mode forward --stage2 ssbfgs \
      --stage1-from results/p0_forward_adam_lr0.001/seed0                           # 只換第二階段

輸出：results/<設定標籤>/seed<k>/
  config.json            設定（續訓時檢查一致性）
  ckpt_stage1.pt         第一階段完整狀態，每 --ckpt-every 步覆寫
  final.pt               第二階段後的最終權重
  summary.json、snapshots.png（最終）、snapshots_stage1.png（第一階段結束時）、training.png

資料（IC 取樣點、觀測雜訊）由獨立亂數產生器（seed+1000）產生：同一個 seed 下，所有方法看到的資料完全相同。

學習率：lr(it) = lr0 · 0.1^(it/iters)。續訓時若 iters 加大，lr 會依新的總步數重新計算。
"""
import argparse
import json
import math
import os
import shutil
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sscpinn import SSCNet, Hydro, ssc_residual, total_mass  # noqa: E402
from sscpinn.optim import SOAP, SelfScalingBFGS  # noqa: E402

# ---------------- 問題設定（SI 單位） ----------------
XB, YB, TB = (0.0, 1000.0), (0.0, 400.0), (0.0, 500.0)
H0, U0, V0 = 2.0, 1.0, 0.1          # m, m/s, m/s
K_TRUE, WS_TRUE, ALPHA = 2.0, 1.0e-3, 1.0   # m²/s, m/s, -
C0, SIG0, X0, Y0 = 1.0, 60.0, 250.0, 180.0  # kg/m³ (=1000 mg/L), m

# 決定第一階段結果的設定（續訓、--stage1-from 時須一致）
STAGE1_KEYS = ["mode", "opt", "lr", "momentum", "wd", "nf", "width", "depth", "seed",
               "causal_eps", "causal_bins", "weighting", "gn_every", "gn_alpha",
               "fourier_sigma", "fourier_m", "precond_freq"]


def exact(x, y, t, K=K_TRUE, ws=WS_TRUE):
    s2 = SIG0 ** 2 + 2 * K * t
    r2 = (x - X0 - U0 * t) ** 2 + (y - Y0 - V0 * t) ** 2
    return C0 * SIG0 ** 2 / s2 * torch.exp(-r2 / (2 * s2)) * torch.exp(-ALPHA * ws * t / H0)


def const(val):
    return lambda x, y, t: torch.full_like(x, val)


def U(n, lo, hi, dev, gen=None):
    return lo + (hi - lo) * torch.rand(n, device=dev, generator=gen)


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["forward", "inverse"], default="forward")
    ap.add_argument("--iters", "--adam", dest="iters", type=int, default=15000,
                    help="第一階段迭代數")
    ap.add_argument("--opt", choices=["adam", "sgd", "soap"], default="adam")
    ap.add_argument("--lr", type=float, default=1e-3, help="初始學習率，訓練中指數衰減到 1/10")
    ap.add_argument("--momentum", type=float, default=0.0, help="SGD momentum")
    ap.add_argument("--wd", type=float, default=0.0,
                    help="weight decay（只作用在網路權重，不作用在反算參數 K、w_s）")
    ap.add_argument("--precond-freq", type=int, default=10, help="SOAP 預條件特徵基更新頻率")
    ap.add_argument("--stage2", choices=["lbfgs", "bfgs", "ssbfgs"], default="lbfgs")
    ap.add_argument("--stage2-weights", choices=["same", "gradnorm"], default="same",
                    help="第二階段權重：same=沿用第一階段（預設）；gradnorm=在第二階段起點依梯度範數重算一次後凍結")
    ap.add_argument("--s2-patience", type=int, default=0,
                    help="第二階段 L-BFGS 的 patience（迭代數）；0 = 關閉（預設，跑固定步數）")
    ap.add_argument("--s2-min-delta", type=float, default=1e-4, help="patience 的相對改善門檻")
    ap.add_argument("--s2-chunk", type=int, default=10, help="patience 模式每幾步檢查一次")
    ap.add_argument("--lbfgs", type=int, default=500, help="第二階段最大迭代數（不論哪種第二階段）")
    ap.add_argument("--causal-eps", type=float, default=0.0, help="#1 因果訓練 ε；0 = 關閉")
    ap.add_argument("--causal-bins", type=int, default=32)
    ap.add_argument("--weighting", choices=["fixed", "gradnorm"], default="fixed")
    ap.add_argument("--gn-every", type=int, default=100)
    ap.add_argument("--gn-alpha", type=float, default=0.9, help="梯度範數權重的移動平均係數")
    ap.add_argument("--fourier-sigma", type=float, default=0.0, help="#3 Fourier features σ；0 = 關閉")
    ap.add_argument("--fourier-m", type=int, default=64)
    ap.add_argument("--nf", type=int, default=8192, help="每步 PDE 配點數")
    ap.add_argument("--width", type=int, default=64)
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", action="store_true", help="從 ckpt_stage1.pt 繼續訓練")
    ap.add_argument("--stage1-from", default=None,
                    help="複製另一次執行的 ckpt_stage1.pt（第一階段設定須相同），只跑第二階段")
    ap.add_argument("--ckpt-every", type=int, default=1000)
    ap.add_argument("--stop-at", type=int, default=None,
                    help="依 --iters 的 lr 排程訓練，但到此步先停（存 checkpoint、跳過第二階段與繪圖）")
    ap.add_argument("--out", default=None, help="直接指定輸出資料夾（覆蓋自動命名）")
    return ap.parse_args()


def make_tag(a):
    tag = f"p0_{a.mode}_{a.opt}_lr{a.lr:g}"
    tag += f"_m{a.momentum:g}" if a.momentum else ""
    tag += f"_wd{a.wd:g}" if a.wd else ""
    tag += f"_pf{a.precond_freq}" if a.opt == "soap" and a.precond_freq != 10 else ""
    tag += f"_causal{a.causal_eps:g}" if a.causal_eps > 0 else ""
    tag += f"_b{a.causal_bins}" if a.causal_eps > 0 and a.causal_bins != 32 else ""
    tag += "_gradnorm" if a.weighting == "gradnorm" else ""
    tag += f"_ff{a.fourier_sigma:g}m{a.fourier_m}" if a.fourier_sigma > 0 else ""
    tag += f"_w{a.width}d{a.depth}" if (a.width, a.depth) != (64, 5) else ""
    tag += f"_nf{a.nf}" if a.nf != 8192 else ""
    tag += f"_s2{a.stage2}" if a.stage2 != "lbfgs" else ""
    tag += "_s2wgn" if a.stage2_weights == "gradnorm" else ""
    tag += f"_pat{a.s2_patience}" if a.s2_patience > 0 else ""
    return tag


def main():
    a = parse()
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    out = a.out or os.path.join(os.path.dirname(__file__), "..", "results", make_tag(a), f"seed{a.seed}")
    os.makedirs(out, exist_ok=True)
    ckpt_path = os.path.join(out, "ckpt_stage1.pt")
    cfg = {k: getattr(a, k) for k in STAGE1_KEYS}

    if a.stage1_from:
        src = os.path.join(a.stage1_from, "ckpt_stage1.pt")
        if not os.path.exists(src):
            sys.exit(f"找不到 {src}")
        if not os.path.exists(ckpt_path):
            shutil.copy2(src, ckpt_path)
        a.resume = True
    if os.path.exists(ckpt_path) and not a.resume:
        sys.exit(f"{out} 已有 checkpoint；要續訓請加 --resume，要重新訓練請先刪除該資料夾。")
    with open(os.path.join(out, "config.json"), "w", encoding="utf-8") as f:
        json.dump({**cfg, "iters": a.iters, "stage2": a.stage2, "stage2_iters": a.lbfgs,
                   "stage1_from": a.stage1_from}, f, indent=2)

    hyd = Hydro(h=const(H0), u=const(U0), v=const(V0))
    net = SSCNet([XB, YB, TB], c_ref=C0, width=a.width, depth=a.depth,
                 fourier_sigma=a.fourier_sigma, fourier_m=a.fourier_m, fourier_seed=a.seed).to(dev)

    # 參數：正算固定為真值；反算以 log 參數化（保證為正）並給錯誤初值
    if a.mode == "forward":
        logK = torch.tensor(math.log(K_TRUE), device=dev)
        logws = torch.tensor(math.log(WS_TRUE), device=dev)
        params = list(net.parameters())
    else:
        logK = torch.tensor(math.log(0.5), device=dev, requires_grad=True)
        logws = torch.tensor(math.log(5e-3), device=dev, requires_grad=True)
        params = list(net.parameters()) + [logK, logws]

    R_REF = H0 * C0 * U0 / SIG0  # 殘差參考值 ~ h·C0·U/σ0

    # ---- 固定資料：IC、觀測（獨立亂數產生器，與方法無關）----
    gdat = torch.Generator(device=dev).manual_seed(1000 + a.seed)
    nic = 4096
    xi, yi = U(nic, *XB, dev, gdat), U(nic, *YB, dev, gdat)
    xi[: nic // 2] = X0 + SIG0 * 2.5 * (2 * torch.rand(nic // 2, device=dev, generator=gdat) - 1)
    yi[: nic // 2] = Y0 + SIG0 * 2.5 * (2 * torch.rand(nic // 2, device=dev, generator=gdat) - 1)
    ti = torch.zeros(nic, device=dev)
    Ci = exact(xi, yi, ti)

    obs = None
    if a.mode == "inverse":
        # 6 個測站沿流向布置，每站 40 個時間採樣，5% 相對雜訊
        st = torch.tensor([[400, 190], [500, 220], [600, 200], [700, 230], [550, 160], [650, 260]],
                          dtype=torch.float32, device=dev)
        tt = torch.linspace(0, TB[1], 40, device=dev)
        xo = st[:, 0:1].repeat(1, 40).reshape(-1)
        yo = st[:, 1:2].repeat(1, 40).reshape(-1)
        to = tt.repeat(6)
        Co = exact(xo, yo, to)
        Co = Co * (1 + 0.05 * torch.randn(Co.shape, device=dev, generator=gdat))
        obs = (xo, yo, to, Co.clamp_min(0))

    def sample_bc(n):
        """矩形域四邊 Dirichlet（解析值，幾乎為 0；實務上為入流濃度/出流條件）"""
        k = n // 4
        t = U(4 * k, *TB, dev)
        x = torch.cat([torch.full((k,), XB[0], device=dev), torch.full((k,), XB[1], device=dev),
                       U(k, *XB, dev), U(k, *XB, dev)])
        y = torch.cat([U(k, *YB, dev), U(k, *YB, dev),
                       torch.full((k,), YB[0], device=dev), torch.full((k,), YB[1], device=dev)])
        return x, y, t

    def sample_pde(n):
        # 一半均勻，一半沿泥砂團移動軌跡加密（對應「洪峰/陡梯度區加密配點」的構想）
        n1 = n // 2
        x, y, t = U(n1, *XB, dev), U(n1, *YB, dev), U(n1, *TB, dev)
        t2 = U(n - n1, *TB, dev)
        s = torch.sqrt(SIG0 ** 2 + 2 * 1.0 * t2)  # 只用到「大概寬度」，不偷看真值 K
        x2 = (X0 + U0 * t2 + 3 * s * (2 * torch.rand_like(t2) - 1)).clamp(*XB)
        y2 = (Y0 + V0 * t2 + 3 * s * (2 * torch.rand_like(t2) - 1)).clamp(*YB)
        x, y, t = torch.cat([x, x2]), torch.cat([y, y2]), torch.cat([t, t2])
        return [z.requires_grad_(True) for z in (x, y, t)]

    W_FIXED = dict(pde=1.0, ic=100.0, bc=10.0, obs=100.0)
    lam = dict(W_FIXED)       # 目前使用的權重（gradnorm 時會更新）
    hist = []
    extra = {}                # 每步額外記錄（因果權重最小值等）

    def loss_terms(pts=None, bpts=None, causal=False):
        x, y, t = pts if pts is not None else sample_pde(a.nf)
        K, ws = logK.exp(), logws.exp()
        R, _ = ssc_residual(net, hyd, x, y, t, K, K, ws, ALPHA)
        r2 = (R / R_REF) ** 2
        L = {"ic": ((net(xi, yi, ti) - Ci) / C0).pow(2).mean()}
        if causal and a.causal_eps > 0:
            nb = a.causal_bins
            b = (t.detach() / TB[1] * nb).long().clamp(0, nb - 1)
            cnt = torch.zeros(nb, device=dev).scatter_add_(0, b, torch.ones_like(r2))
            Lb = torch.zeros(nb, device=dev).scatter_add_(0, b, r2) / cnt.clamp_min(1)
            with torch.no_grad():
                cum = L["ic"].detach() + torch.cat([torch.zeros(1, device=dev), Lb.cumsum(0)[:-1]])
                w = torch.exp(-a.causal_eps * cum)
            L["pde"] = (w * Lb).mean()
            extra["causal_wmin"] = w.min().item()
        else:
            L["pde"] = r2.mean()
        xb, yb, tb = bpts if bpts is not None else sample_bc(1024)
        L["bc"] = ((net(xb, yb, tb) - exact(xb, yb, tb)) / C0).pow(2).mean()
        if obs is not None:
            L["obs"] = ((net(*obs[:3]) - obs[3]) / C0).pow(2).mean()
        return L

    def total(L):
        return sum(lam[k] * v for k, v in L.items())

    net_params = list(net.parameters())

    def update_gradnorm(L, first):
        norms = {}
        for k, v in L.items():
            gs = torch.autograd.grad(v, net_params, retain_graph=True, allow_unused=True)
            norms[k] = math.sqrt(sum(float((g ** 2).sum()) for g in gs if g is not None)) + 1e-30
        s = sum(norms.values())
        for k in L:
            new = s / norms[k]
            lam[k] = new if first else a.gn_alpha * lam[k] + (1 - a.gn_alpha) * new

    # ---------------- 評估 ----------------
    gx = torch.linspace(*XB, 201, device=dev)
    gy = torch.linspace(*YB, 81, device=dev)
    GX, GY = torch.meshgrid(gx, gy, indexing="ij")

    @torch.no_grad()
    def rel_l2():
        num = den = 0.0
        for tv in torch.linspace(*TB, 11):
            T = torch.full_like(GX, float(tv))
            ce = exact(GX, GY, T); cp = net(GX, GY, T)
            num += ((cp - ce) ** 2).sum().item(); den += (ce ** 2).sum().item()
        return math.sqrt(num / den)

    @torch.no_grad()
    def rel_l2_per_time():
        res = []
        for tv in torch.linspace(*TB, 11):
            T = torch.full_like(GX, float(tv))
            ce = exact(GX, GY, T); cp = net(GX, GY, T)
            res.append(math.sqrt(((cp - ce) ** 2).sum().item() / (ce ** 2).sum().item()))
        return res

    def log(it, L, t0):
        rec = {"it": it, "total": float(total(L)), **{k: v.item() for k, v in L.items()},
               "K": logK.exp().item(), "ws": logws.exp().item(), **extra}
        if a.weighting == "gradnorm":
            rec.update({f"lam_{k}": lam[k] for k in L})
        hist.append(rec)
        if it % 1000 == 0:
            rec["relL2"] = rel_l2()
            msg = (f"[{it:6d}] {time.time()-t0:6.0f}s tot={rec['total']:.3e} "
                   + " ".join(f"{k}={rec[k]:.2e}" for k in L)
                   + f" relL2={rec['relL2']:.3e} K={rec['K']:.3f} ws={rec['ws']:.2e}")
            if "causal_wmin" in extra:
                msg += f" wmin={extra['causal_wmin']:.2e}"
            if a.weighting == "gradnorm":
                msg += " lam=" + ",".join(f"{k}:{lam[k]:.2g}" for k in L)
            print(msg, flush=True)

    # ---------------- 第一階段 ----------------
    t0 = time.time()
    groups = [{"params": net_params, "weight_decay": a.wd}]
    if a.mode == "inverse":
        groups.append({"params": [logK, logws], "weight_decay": 0.0})
    if a.opt == "adam":
        opt = torch.optim.AdamW(groups, lr=a.lr)  # wd=0 時與 Adam 相同
    elif a.opt == "soap":
        opt = SOAP(groups, lr=a.lr, precond_freq=a.precond_freq)
    else:
        opt = torch.optim.SGD(groups, lr=a.lr, momentum=a.momentum, nesterov=a.momentum > 0)

    def save_ckpt(next_it):
        state = {"it": next_it, "config": cfg, "net": net.state_dict(), "opt": opt.state_dict(),
                 "logK": logK.detach().clone(), "logws": logws.detach().clone(), "hist": hist,
                 "lam": dict(lam), "rng_cpu": torch.get_rng_state(),
                 "rng_cuda": torch.cuda.get_rng_state_all() if dev == "cuda" else None}
        torch.save(state, ckpt_path + ".tmp")
        os.replace(ckpt_path + ".tmp", ckpt_path)  # 原子寫入

    start = 0
    if a.resume:
        if not os.path.exists(ckpt_path):
            sys.exit(f"找不到 {ckpt_path}，無法續訓")
        ck = torch.load(ckpt_path, map_location="cpu")  # RNG 狀態必須是 CPU ByteTensor
        diff = {k: (ck["config"].get(k), cfg[k]) for k in cfg if ck["config"].get(k) != cfg[k]}
        # 舊版 checkpoint 沒有新增的鍵：視為預設值（關閉）
        defaults = dict(causal_eps=0.0, causal_bins=32, weighting="fixed", gn_every=100, gn_alpha=0.9,
                        fourier_sigma=0.0, fourier_m=64, precond_freq=10)
        diff = {k: v for k, v in diff.items() if not (v[0] is None and defaults.get(k) == v[1])}
        if diff:
            sys.exit(f"設定與 checkpoint 不符（checkpoint, 目前）：{diff}")
        net.load_state_dict(ck["net"]); opt.load_state_dict(ck["opt"])
        with torch.no_grad():
            logK.copy_(ck["logK"]); logws.copy_(ck["logws"])
        hist.extend(ck["hist"])
        lam.update(ck.get("lam", {}))
        torch.set_rng_state(ck["rng_cpu"])
        if dev == "cuda" and ck["rng_cuda"] is not None:
            torch.cuda.set_rng_state_all(ck["rng_cuda"])
        start = ck["it"]
        print(f"從 {ckpt_path} 續訓：第 {start} 步 → {a.iters} 步")

    it = start
    end = min(a.iters, a.stop_at) if a.stop_at is not None else a.iters
    try:
        for it in range(start, end):
            for g in opt.param_groups:  # lr 由 it 決定，續訓時不需要還原 scheduler
                g["lr"] = a.lr * 0.1 ** (it / a.iters)
            opt.zero_grad()
            L = loss_terms(causal=True)
            if a.weighting == "gradnorm" and it % a.gn_every == 0:
                update_gradnorm(L, first=(it == 0))
            tot = total(L)
            if not torch.isfinite(tot):
                print(f"[{it}] loss 發散（NaN/Inf），停止第一階段"); break
            tot.backward()
            opt.step()
            log(it, L, t0)
            if (it + 1) % a.ckpt_every == 0:
                save_ckpt(it + 1)
        else:
            it = end
    except KeyboardInterrupt:
        save_ckpt(it)
        sys.exit(f"\n中斷：已存 checkpoint 於第 {it} 步，可用 --resume 繼續")
    if it > start:
        save_ckpt(it)
    if it < a.iters:
        sys.exit(f"第一階段停在第 {it}/{a.iters} 步，已存 checkpoint；用 --resume 繼續")
    t_stage1 = time.time() - t0

    stage1 = {"relL2_stage1": rel_l2(), "relL2_stage1_per_time": rel_l2_per_time(),
              "K_stage1": logK.exp().item(), "ws_stage1": logws.exp().item()}
    print(f"第一階段（{a.opt}）結束 relL2={stage1['relL2_stage1']:.3e}")

    # ---------------- 繪圖工具 ----------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Microsoft YaHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    def plot_snapshots(fname, label):
        fig, ax = plt.subplots(3, 3, figsize=(15, 9), constrained_layout=True)
        for j, tv in enumerate([0.0, 250.0, 500.0]):
            T = torch.full_like(GX, tv)
            with torch.no_grad():
                ce = exact(GX, GY, T).cpu().numpy(); cp = net(GX, GY, T).cpu().numpy()
            X, Y = GX.cpu().numpy(), GY.cpu().numpy()
            for i, (Z, ttl, cm) in enumerate([(ce, "解析解", "viridis"), (cp, f"PINN（{label}）", "viridis"),
                                               (cp - ce, "誤差 PINN-解析", "RdBu_r")]):
                if i < 2:
                    im = ax[i, j].pcolormesh(X, Y, Z, cmap=cm, vmin=0, vmax=C0, shading="auto")
                else:
                    v = max(abs(Z).max(), 1e-6)
                    im = ax[i, j].pcolormesh(X, Y, Z, cmap=cm, vmin=-v, vmax=v, shading="auto")
                ax[i, j].set_title(f"{ttl}  t={tv:.0f}s"); ax[i, j].set_aspect("equal")
                fig.colorbar(im, ax=ax[i, j], shrink=0.8, label="C (kg/m³)")
                if obs is not None and i == 1:
                    ax[i, j].plot(obs[0].cpu()[::40], obs[1].cpu()[::40], "r^", ms=6)
        fig.savefig(os.path.join(out, fname), dpi=110)
        plt.close(fig)

    plot_snapshots("snapshots_stage1.png", f"第一階段 {a.opt}")

    # ---------------- 第二階段 ----------------
    t1 = time.time()
    s2info = {}
    if a.lbfgs > 0:
        fixed = sample_pde(a.nf * 2)   # 固定配點
        fb = sample_bc(2048)

        def closure():
            for p in params:
                p.grad = None
            L = loss_terms(pts=fixed, bpts=fb, causal=False)
            tot = total(L)   # gradnorm 時使用第一階段最後的權重（凍結）
            tot.backward()
            return tot

        # 診斷：第二階段起點的各項 loss（含權重）與參數梯度
        s2info["stage2_weights"] = a.stage2_weights
        if a.stage2_weights == "gradnorm":
            update_gradnorm(loss_terms(pts=fixed, bpts=fb, causal=False), first=True)
            s2info["stage2_lam"] = dict(lam)
        L0 = loss_terms(pts=fixed, bpts=fb, causal=False)
        s2info["stage2_start_terms"] = {k: float(lam[k] * v) for k, v in L0.items()}
        if a.mode == "inverse":
            gK, gw = torch.autograd.grad(total(L0), [logK, logws])
            s2info["stage2_start_grad_logK"] = float(gK)
            s2info["stage2_start_grad_logws"] = float(gw)
        if a.stage2 == "lbfgs" and a.s2_patience > 0:
            # patience 模式：每 a.s2_chunk 步檢查一次；L-BFGS 的歷史保存在 state，分段呼叫不影響優化
            lb = torch.optim.LBFGS(params, lr=1.0, max_iter=a.s2_chunk, max_eval=10**9, history_size=50,
                                   line_search_fn="strong_wolfe")  # 分段時取消每段的評估上限，避免誤判
            st = lb.state[lb._params[0]]
            trace, best, since, status = [], float("inf"), 0, "max_iter"
            while True:
                n0 = st.get("n_iter", 0)
                lb.step(closure)
                n1 = st.get("n_iter", 0)
                lv = float(total(loss_terms(pts=fixed, bpts=fb, causal=False)).detach())  # 殘差需要 autograd，不能用 no_grad
                trace.append({"iter": n1, "loss": lv, "K": logK.exp().item(),
                              "ws": logws.exp().item(), "relL2": rel_l2()})
                if lv < best * (1 - a.s2_min_delta):
                    best, since = lv, 0
                else:
                    since += n1 - n0
                if n1 - n0 < a.s2_chunk:      # 本段提前結束：線搜尋失敗或達 torch 容忍度
                    g = torch.cat([p.grad.reshape(-1) for p in params if p.grad is not None])
                    status = ("converged(tolerance_grad)" if float(g.abs().max()) <= 1e-7 else
                              "stuck(line_search)" if float(st.get("t", 1.0)) == 0.0 else "stopped(tolerance_change)")
                    break
                if since >= a.s2_patience:
                    status = "converged(patience)"
                    break
                if n1 >= a.lbfgs:
                    status = "not_converged(max_iter)"
                    break
            w = [r for r in trace if r["iter"] >= trace[-1]["iter"] - a.s2_patience]
            s2info.update({"stage2_iters": st.get("n_iter"), "stage2_evals": st.get("func_evals"),
                           "stage2_status": status, "stage2_trace": trace,
                           "stage2_K_drift_last_window": max(r["K"] for r in w) - min(r["K"] for r in w)})
        elif a.stage2 == "lbfgs":
            lb = torch.optim.LBFGS(params, lr=1.0, max_iter=a.lbfgs, history_size=50,
                                   line_search_fn="strong_wolfe")
            lb.step(closure)
            st = lb.state[lb._params[0]]
            s2info.update({"stage2_iters": st.get("n_iter"), "stage2_evals": st.get("func_evals")})
            # 依 torch.optim.LBFGS 的停止條件推斷停止原因（tolerance_grad=1e-7, tolerance_change=1e-9）
            g = torch.cat([p.grad.reshape(-1) for p in params if p.grad is not None])
            gmax = float(g.abs().max())
            step = float((st["d"] * st["t"]).abs().max()) if "d" in st else float("nan")
            dloss = abs(float(closure()) - float(st.get("prev_loss", float("nan"))))
            reason = ("max_iter" if st.get("n_iter", 0) >= a.lbfgs else
                      "tolerance_grad" if gmax <= 1e-7 else
                      "tolerance_change(step)" if step <= 1e-9 else
                      "tolerance_change(loss)" if dloss < 1e-9 else "other(line search / max_eval)")
            s2info.update({"stage2_stop_reason": reason, "stage2_end_gradmax": gmax,
                           "stage2_last_step_max": step, "stage2_last_dloss": dloss,
                           "stage2_last_t": float(st.get("t", float("nan")))})
        else:
            bf = SelfScalingBFGS(params, max_iter=a.lbfgs, self_scaling=(a.stage2 == "ssbfgs"))
            bf.step(closure)
            s2info.update({"stage2_iters": bf.n_iters, "stage2_evals": bf.n_evals, "stage2_resets": bf.n_resets})
        L = loss_terms(causal=False)
        log(it, L, t0)
        hist[-1]["relL2"] = rel_l2()
        print(f"{a.stage2} 後 relL2={hist[-1]['relL2']:.3e} K={logK.exp().item():.4f} "
              f"ws={logws.exp().item():.3e} {s2info}")
    t_stage2 = time.time() - t1

    # ---------------- 質量守恆檢核 ----------------
    tm = torch.linspace(*TB, 26, device=dev)
    with torch.no_grad():
        Mp = total_mass(net, hyd, tm, XB, YB).cpu().numpy()
    M0 = H0 * C0 * 2 * math.pi * SIG0 ** 2
    Me = M0 * np.exp(-ALPHA * WS_TRUE * tm.cpu().numpy() / H0)
    mass_err = float(np.max(np.abs(Mp - Me) / Me))

    summary = {**cfg, "iters_done": it, "stage2": a.stage2, "stage2_maxiter": a.lbfgs, **s2info,
               "stage1_from": a.stage1_from,
               **stage1, "relL2": hist[-1].get("relL2", rel_l2()), "relL2_per_time": rel_l2_per_time(),
               "K_est": logK.exp().item(), "K_true": K_TRUE,
               "ws_est": logws.exp().item(), "ws_true": WS_TRUE,
               "max_mass_rel_err": mass_err,
               "time_stage1_s": t_stage1, "time_stage2_s": t_stage2,
               "lam_final": dict(lam) if a.weighting == "gradnorm" else None,
               "device": torch.cuda.get_device_name(0) if dev == "cuda" else "cpu"}
    print(json.dumps({k: v for k, v in summary.items() if "per_time" not in k}, indent=2, ensure_ascii=False))
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    torch.save({"config": cfg, "iters_done": it, "stage2": a.stage2, "net": net.state_dict(),
                "logK": logK.detach().cpu(), "logws": logws.detach().cpu()},
               os.path.join(out, "final.pt"))

    # ---------------- 繪圖 ----------------
    plot_snapshots("snapshots.png", f"最終 {a.stage2}")
    ncol = 3 if a.mode == "inverse" else 2
    if a.weighting == "gradnorm" or a.causal_eps > 0:
        ncol += 1
    fig, ax = plt.subplots(1, ncol, figsize=(5 * ncol, 4), constrained_layout=True)
    its = [h["it"] for h in hist]
    for k in ["total", "pde", "ic", "bc", "obs"]:
        if k in hist[0]:
            ax[0].semilogy(its, [h[k] for h in hist], label=k, lw=0.8)
    ax[0].legend(); ax[0].set_title("Loss 分項（未加權）"); ax[0].set_xlabel("iteration")
    ax[1].plot(tm.cpu(), Me, "k-", label="解析 M(t)")
    ax[1].plot(tm.cpu(), Mp, "o", ms=4, label="PINN ∫hC dA")
    ax[1].set_title(f"全域質量守恆（最大相對誤差 {mass_err:.2%}）"); ax[1].set_xlabel("t (s)")
    ax[1].set_ylabel("M (kg)"); ax[1].legend()
    c = 2
    if a.mode == "inverse":
        ax[c].semilogy(its, [h["K"] / K_TRUE for h in hist], label="K / K_true")
        ax[c].semilogy(its, [h["ws"] / WS_TRUE for h in hist], label="w_s / w_s,true")
        ax[c].axhline(1, color="k", lw=0.8); ax[c].legend(); ax[c].set_title("參數反算收斂")
        c += 1
    if a.weighting == "gradnorm":
        for k in ["pde", "ic", "bc", "obs"]:
            if f"lam_{k}" in hist[0]:
                ax[c].semilogy(its, [h[f"lam_{k}"] for h in hist], label=f"λ_{k}")
        ax[c].legend(); ax[c].set_title("梯度範數權重")
    elif a.causal_eps > 0:
        ax[c].semilogy(its, [h.get("causal_wmin", np.nan) for h in hist])
        ax[c].set_title("因果權重最小值 min w_i"); ax[c].set_xlabel("iteration")
    fig.savefig(os.path.join(out, "training.png"), dpi=110)
    print("結果輸出至", os.path.abspath(out))


if __name__ == "__main__":
    main()
