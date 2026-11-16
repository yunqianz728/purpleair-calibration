#!/bin/bash
# Generalization experiments, QC variants (tasks 11-20: full and reduced features, flagged sensors
# removed from training) on the AMF CPU QoS (256 cores, so all ten run at once).
#   sbatch --array=11-20 paper/analysis/cluster/gen_cpu.sbatch
#SBATCH --job-name=pa_gen_cpu
#SBATCH --partition=mit_normal
#SBATCH --account=mit_amf_standard_cpu
#SBATCH --qos=mit_amf_standard_cpu
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --output=logs/pa_gen_cpu_%A_%a.out
set -euo pipefail
source "$HOME/pa_env/bin/activate"
A="$PWD/paper/analysis"
export PA_PARQUET="$A/train.parquet" PA_OUT="$A/results_wide" PA_SEARCH=wide PA_N_TRIALS=50 \
       PA_N_JOBS=$SLURM_CPUS_PER_TASK PA_JOB=$SLURM_ARRAY_TASK_ID
python3 "$A/generalization_experiments.py"
