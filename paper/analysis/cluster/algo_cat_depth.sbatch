#!/bin/bash
# CatBoost beyond its tuned depth of 12 (algo_comparison.py --depth-check): depths 14 and 16 with the
# other tuned parameters kept, one array task per configuration x target. From the repository root:
#   sbatch --array=1-4 paper/analysis/cluster/algo_cat_depth.sbatch
#SBATCH --job-name=pa_catdepth
#SBATCH --partition=mit_normal_gpu
#SBATCH --account=mit_amf_standard_gpu
#SBATCH --qos=mit_amf_standard_gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=60G
#SBATCH --time=6:00:00
#SBATCH --output=logs/pa_catdepth_%A_%a.out
set -euo pipefail
source "$HOME/pa_env/bin/activate"
A="$PWD/paper/analysis"
export PA_PARQUET="$A/train.parquet" PA_OUT="$A/results_wide" PA_SEARCH=wide PA_N_TRIALS=50 PA_N_JOBS=$SLURM_CPUS_PER_TASK PA_DEVICE=cuda
export PA_ONLY=$(python3 "$A/algo_comparison.py" --list | grep CatBoost | sed -n "${SLURM_ARRAY_TASK_ID}p")
echo "task $SLURM_ARRAY_TASK_ID: $PA_ONLY on $(hostname)"
python3 "$A/algo_comparison.py" --depth-check
