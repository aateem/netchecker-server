#!/bin/bash
set -o pipefail
NODE_PORT=${NODE_PORT:-31081}
echo "Waiting for agents..."
while true; do
  out=$(timeout --signal=KILL 5 curl -s -X GET "http://localhost:${NODE_PORT}/api/v1/agents/" | python -mjson.tool)
  [ $? -eq 0 -a ! "$out" = "{}" -a ! "$out" = "No JSON object could be decoded" ] && break
  sleep 5
done
# Give agents some time to stabilize
sleep 5
echo $out | python -mjson.tool

echo "Running net check 10 times..."
failed=0
for i in $(seq 1 10); do
  out=$(timeout --signal=KILL 5 curl -s -X GET "http://localhost:${NODE_PORT}/api/v1/connectivity_check")
  rc=$?
  [ $rc -ne 0 ] && failed=1 && break
  echo "Check $i has PASSED"
  sleep 3
done
[ $failed -ne 0 ] && echo "Check FAILED"
exit $failed
