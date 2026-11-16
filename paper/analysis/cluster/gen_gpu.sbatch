#!/bin/bash
# Generalization experiments (4 variants x 5 sensor folds, each tuned) under the widened search, one
# variant-fold per array task, on the general-account GPU QoS (two GPUs, separate from the AMF limit).
# Tasks 1-10 are the two variants on all sensors (full and reduced features), so the comparison between
# them stays on one device; tasks 11-20 (the QC variants) run on CPU with gen_cpu.sbatch.
#   sbatch --array=1-10%2 paper/analysis/cluster/gen_gpu.sbatch
# Afterwards, one run without PA_JOB assembles generalization/summary.json from the saved folds.
#SBATCH --job-name=pa_gen_gpu
#SBATCH --partition=mit_normal_gpu
#SBATCH --account=mit_general
#SBATCH --qos=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=6:00:00
#SBATCH --output=logs/pa_gen_gpu_%A_%a.out
set -euo pipefail
source "$HOME/pa_env/bin/activate"
A="$PWD/paper/analysis"
export PA_PARQUET="$A/train.parquet" PA_OUT="$A/results_wide" PA_SEARCH=wide PA_N_TRIALS=50 \
       PA_N_JOBS=$SLURM_CPUS_PER_TASK PA_DEVICE=cuda PA_JOB=$SLURM_ARRAY_TASK_ID
python3 "$A/generalization_experiments.py"
