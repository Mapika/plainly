#!/usr/bin/env bash
# Wait for the detached generate.py to finish, then run score -> judge -> analyze.
# Does NOT relaunch generation. Logs to pipeline.log.
set -uo pipefail
cd /home/mapika/projects/writer/eval/experiment
LOG=pipeline.log
echo "[finish $(date +%H:%M:%S)] waiting for generate.py to complete..." | tee -a "$LOG"
deadline=$((SECONDS + 7200))   # 2h safety
while pgrep -f 'generate\.py' >/dev/null 2>&1; do
  if [ $SECONDS -gt $deadline ]; then
    echo "[finish] TIMEOUT waiting for generate.py" | tee -a "$LOG"; break
  fi
  sleep 30
done
sleep 3
echo "[finish $(date +%H:%M:%S)] generation counts:" | tee -a "$LOG"
for c in baseline human_system fewshot deslop; do
  echo "  $c: $(ls out/$c/*.txt 2>/dev/null | wc -l)" | tee -a "$LOG"
done
echo "[finish] running score.py"   | tee -a "$LOG"; python3 score.py    >>"$LOG" 2>&1; echo "  score rc=$?" | tee -a "$LOG"
echo "[finish] running judge.py"   | tee -a "$LOG"; python3 judge.py    >>"$LOG" 2>&1; echo "  judge rc=$?" | tee -a "$LOG"
echo "[finish] running analyze.py" | tee -a "$LOG"; python3 analyze.py  >>"$LOG" 2>&1; echo "  analyze rc=$?" | tee -a "$LOG"
echo "[finish $(date +%H:%M:%S)] DONE" | tee -a "$LOG"
wc -l scores.csv judgements.csv 2>&1 | tee -a "$LOG"
ls -la ../docs/EXPERIMENT_RESULTS.md 2>&1 | tee -a "$LOG"
