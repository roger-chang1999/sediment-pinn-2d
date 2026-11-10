#!/usr/bin/env bash
# P0 訓練改進五項消融（research_log/ideas/006）
# 每組設定 × seed 0,1,2 × forward/inverse。已有 summary.json 的組合自動跳過，可隨時中斷重跑。
# 用法：bash experiments/run_p0_ablation.sh [組別...]   （不給參數 = 全部）
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
LOG=results/logs; mkdir -p "$LOG"
SEEDS="0 1 2"; MODES="forward inverse"

tag_of() { python -c "
import sys; sys.argv=['x']+sys.argv[1:]
sys.path.insert(0,'experiments'); import p0_analytic as p
print(p.make_tag(p.parse()))" "$@"; }

run() {  # run <組名> <參數...>
  local name=$1; shift
  for m in $MODES; do for s in $SEEDS; do
    local tag; tag=$(tag_of --mode "$m" --seed "$s" "$@")
    local dir="results/$tag/seed$s"
    if [ -f "$dir/summary.json" ]; then echo "skip $tag seed$s"; continue; fi
    local extra=()
    [ -f "$dir/ckpt_stage1.pt" ] && extra=(--resume)
    echo "$(date '+%F %T') start $name $tag seed$s"
    python experiments/p0_analytic.py --mode "$m" --seed "$s" "$@" "${extra[@]}" \
      > "$LOG/${tag}_seed$s.log" 2>&1
    echo "$(date '+%F %T') done  $name $tag seed$s :: $(grep -E '後 relL2|結束 relL2' "$LOG/${tag}_seed$s.log" | tr '\n' ' ')"
  done; done
}

stage2() {  # 第二階段替換：共用基準的第一階段 checkpoint
  local s2=$1
  for m in $MODES; do for s in $SEEDS; do
    local base; base="results/$(tag_of --mode "$m" --seed "$s")/seed$s"
    run_one=(--mode "$m" --seed "$s" --stage2 "$s2" --stage1-from "$base")
    local tag; tag=$(tag_of "${run_one[@]}")
    local dir="results/$tag/seed$s"
    if [ -f "$dir/summary.json" ]; then echo "skip $tag seed$s"; continue; fi
    if [ ! -f "$base/ckpt_stage1.pt" ]; then echo "缺少基準 $base/ckpt_stage1.pt，跳過"; continue; fi
    echo "$(date '+%F %T') start stage2-$s2 $tag seed$s"
    python experiments/p0_analytic.py "${run_one[@]}" > "$LOG/${tag}_seed$s.log" 2>&1
    echo "$(date '+%F %T') done  stage2-$s2 $tag seed$s :: $(grep -E '後 relL2' "$LOG/${tag}_seed$s.log" | tr '\n' ' ')"
  done; done
}

SEL=("$@"); [ ${#SEL[@]} -eq 0 ] && SEL=(base soap causal100 gradnorm fourier causal10 lbfgs2)
for g in "${SEL[@]}"; do
  case $g in
    base)      run base ;;
    soap)      run soap --opt soap ;;
    causal100) run causal100 --causal-eps 100 ;;
    causal10)  run causal10 --causal-eps 10 ;;
    gradnorm)  run gradnorm --weighting gradnorm ;;
    fourier)   run fourier --fourier-sigma 1 ;;
    lbfgs2)    stage2 bfgs; stage2 ssbfgs ;;
    *) echo "未知組別 $g" ;;
  esac
done
echo "$(date '+%F %T') ALL DONE"
