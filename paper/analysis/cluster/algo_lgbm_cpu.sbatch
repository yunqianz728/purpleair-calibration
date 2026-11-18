#!/bin/bash
# LightGBM for SI Table S5 under the protocol and widened search of the main results (algo_comparison.py):
# the 4 unstratified configuration x target runs, one array task each. From the repository root:
#   sbatch --array=1-4 paper/analysis/cluster/algo_lgbm_cpu.sbatch
#SBATCH --job-name=pa_lgbm
#SBATCH --partition=mit_normal
#SBATCH --cpus-per-task=16
#SBATCH --mem=60G
#SBATCH --time=12:00:00
#SBATCH --output=logs/pa_lgbm_%A_%a.out
set -euo pipefail
source "$HOME/pa_env/bin/activate"
A="$PWD/paper/analysis"
export PA_PARQUET="$A/train.parquet" PA_OUT="$A/results_wide" PA_SEARCH=wide PA_N_TRIALS=50 PA_N_JOBS=$SLURM_CPUS_PER_TASK
export PA_ONLY=$(python3 "$A/algo_comparison.py" --list | grep LightGBM | sed -n "${SLURM_ARRAY_TASK_ID}p")
echo "task $SLURM_ARRAY_TASK_ID: $PA_ONLY on $(hostname)"
python3 "$A/algo_comparison.py"
