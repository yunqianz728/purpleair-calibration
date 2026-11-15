#!/bin/bash
# The 28 configurations under the widened search on one GPU each, in the order of cluster/local_order.txt
# (station temperature first, as the downstream analyses need). Submit from the repository root:
#   sbatch --array=1-28%2 paper/analysis/cluster/rerun_wide_gpu.sbatch
# (%2: the mit_amf_standard_gpu QoS allows two GPUs at a time.) Finished configurations are skipped.
#SBATCH --job-name=pa_wide_gpu
#SBATCH --partition=mit_normal_gpu
#SBATCH --account=mit_amf_standard_gpu
#SBATCH --qos=mit_amf_standard_gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/pa_wide_gpu_%A_%a.out
set -euo pipefail
source "$HOME/pa_env/bin/activate"
A="$PWD/paper/analysis"
export PA_PARQUET="$A/train.parquet" PA_OUT="$A/results_wide" PA_SEARCH=wide PA_N_TRIALS=50 \
       PA_N_JOBS=$SLURM_CPUS_PER_TASK PA_DEVICE=cuda
export PA_ONLY=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$A/cluster/local_order.txt")
echo "task $SLURM_ARRAY_TASK_ID: $PA_ONLY on $(hostname) $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
python3 "$A/rerun_models.py" main
