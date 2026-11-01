#!/usr/bin/env bash
# Experiment 2, part 1: find the file size where fetching stops working at 0% loss.
# One Locust user fetches each file for SECS seconds, so the only thing that changes is the size.
# usage: experiments/sweep_exp2.sh http://<alb> [SECS per size, default 180]
# Output: shots/exp2/sweep/<size>_stats.csv (and history), windows.txt (UTC start/end of each
# size, for the CloudWatch time range) and summary.txt.
set -u
HOST=${1:?usage: sweep_exp2.sh http://<alb> [seconds per size]}
SECS=${2:-180}
SIZES=(f4k f64k f96k f128k f256k f512k f1m)
OUT=shots/exp2/sweep
mkdir -p "$OUT"
: >"$OUT/windows.txt"
for size in "${SIZES[@]}"; do
	start=$(date -u +%H:%M:%S)
	echo "$(date -u +%H:%M:%S) UTC: $size for ${SECS}s"
	FILE_NAME=$size.bin locust -f experiments/locustfile_files.py --host "$HOST" \
		--headless -u 1 -r 1 -t "${SECS}s" --csv "$OUT/$size" >"$OUT/$size.log" 2>&1
	echo "$size start=$start end=$(date -u +%H:%M:%S) UTC" >>"$OUT/windows.txt"
	sleep 20 # let the backend finish any retry burst before the next size
done
python3 -I - "$OUT" "${SIZES[@]}" >"$OUT/summary.txt" <<'PY'
import csv, sys
out, sizes = sys.argv[1], sys.argv[2:]
print("size,requests,failures,success_pct,p50_ms,p95_ms,max_ms")
for size in sizes:
    for row in csv.DictReader(open(f"{out}/{size}_stats.csv")):
        if row["Name"] == "GET /files":
            n, f = int(row["Request Count"]), int(row["Failure Count"])
            ok = 100 * (n - f) / n if n else 0
            print(f'{size},{n},{f},{ok:.0f},{row["50%"]},{row["95%"]},{row["Max Response Time"]}')
PY
cat "$OUT/summary.txt"
