#!/bin/bash
# Run the remaining R1 experiments one after another, in a single process.
#
# An earlier attempt chained these as separate background jobs that each waited with
#   while pgrep -f "<previous script>.py"; do sleep 30; done
# which never terminates: the waiting shell's own command line contains the pattern, so pgrep
# always matches itself. All four jobs sat in that loop and none ever ran. Sequential execution
# in one process removes the need to poll at all.
#
# Each step is independent (";" not "&&"), so one failure does not stop the rest. Every script is
# resumable, so re-running this after an interruption picks up where it left off.
#
# Usage:  bash analysis_R1/run_queue.sh
set -u
cd "$(dirname "$0")/.."
A="$PWD/analysis_R1"
export PA_PARQUET="${PA_PARQUET:-$A/train.parquet}"   # build it with: python3 analysis_R1/make_parquet.py
Q="$A/results/queue.log"

step () {                      # step <label> <logfile> <command...>
  local label="$1" log="$2"; shift 2
  echo "$(date '+%F %T') START $label" | tee -a "$Q"
  caffeinate -is "$@" > "$log" 2>&1
  echo "$(date '+%F %T') END   $label (exit $?)" | tee -a "$Q"
}

# 1. deployment-scenario splits: independent of the tuning budget, and the quickest result
step split_protocols "$A/results_split_protocols.stdout" \
  python3 "$A/split_protocols.py"

# 2-3. the 50-trial re-run is the backbone: Table 2, the abstract and most pending numbers come from it
mkdir -p "$A/results50"
step rerun50_main "$A/results50_main.stdout" \
  env PA_OUT="$A/results50" PA_N_TRIALS=50 python3 "$A/rerun_models.py" main
step rerun50_grouped "$A/results50_grouped.stdout" \
  env PA_OUT="$A/results50" PA_N_TRIALS=50 python3 "$A/rerun_models.py" grouped

# 4-5. these read the tuned parameters, so they run against results50 for consistency with Table 2
cp -n "$A/results/feature_clusters_r_ge_0.9.json" "$A/results50/" 2>/dev/null
step correlated_features "$A/results_correlated_features.stdout" \
  env PA_OUT="$A/results50" PA_N_TRIALS=50 python3 "$A/correlated_features.py"
step warmup "$A/results_warmup.stdout" \
  env PA_OUT="$A/results50" python3 "$A/warmup_experiment.py"

echo "$(date '+%F %T') QUEUE COMPLETE" | tee -a "$Q"
