#!/bin/bash
# Downstream refits that reuse the tuned parameters of the wide run, on the AMF GPU QoS, after the 28
# configurations finish. Two tasks so both GPUs are used:
#   1: leave-sensors-out (national and stratified), feature-removal sensitivity, warm-up
#   2: five-seed robustness, correlated features
#   sbatch --array=1-2 --dependency=afterok:<wide array job> paper/analysis/cluster/stage2_gpu.sbatch
#SBATCH --job-name=pa_stage2
#SBATCH --partition=mit_normal_gpu
#SBATCH --account=mit_amf_standard_gpu
#SBATCH --qos=mit_amf_standard_gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=23:00:00
#SBATCH --output=logs/pa_stage2_%A_%a.out
set -uo pipefail
source "$HOME/pa_env/bin/activate"
A="$PWD/paper/analysis"
export PA_PARQUET="$A/train.parquet" PA_OUT="$A/results_wide" PA_SEARCH=wide PA_N_TRIALS=50 \
       PA_N_JOBS=$SLURM_CPUS_PER_TASK PA_DEVICE=cuda
run () { echo "$(date '+%F %T') START $*"; python3 "$@"; echo "$(date '+%F %T') END $* (exit $?)"; }
if [ "$SLURM_ARRAY_TASK_ID" = 1 ]; then
  run "$A/rerun_models.py" grouped
  run "$A/rerun_models.py" grouped_strat
  run "$A/grouped_sensitivity.py"
  run "$A/warmup_experiment.py"
else
  run "$A/seed_robustness.py"
  cp -n "$A/../results_50trials/feature_clusters_r_ge_0.9.json" "$PA_OUT/"
  run "$A/correlated_features.py"
fi
