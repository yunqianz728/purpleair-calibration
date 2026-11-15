#!/bin/bash
# The 28 configurations of Table 2 under the widened XGBoost search (PA_SEARCH=wide), one array task each.
# Submit from the repository root:  sbatch --array=1-28 paper/analysis/cluster/rerun_wide.sbatch
# Every task tunes and scores one configuration and writes models/<name>.json; tasks are independent and
# a finished configuration is skipped on resubmission.
#SBATCH --job-name=pa_wide
#SBATCH --partition=mit_normal
#SBATCH --cpus-per-task=16   # mit_normal allows 96 cores per user, so six tasks run at once
#SBATCH --mem=60G
#SBATCH --time=12:00:00
#SBATCH --output=logs/pa_wide_%A_%a.out
set -euo pipefail
source "$HOME/pa_env/bin/activate"
A="$PWD/paper/analysis"
export PA_PARQUET="$A/train.parquet" PA_OUT="$A/results_wide" PA_SEARCH=wide PA_N_TRIALS=50 PA_N_JOBS=$SLURM_CPUS_PER_TASK
export PA_ONLY=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$A/cluster/configs.txt")
echo "task $SLURM_ARRAY_TASK_ID: $PA_ONLY on $(hostname)"
python3 "$A/rerun_models.py" main
