#!/usr/bin/env bash
# Submit the PyFlink kafka_to_landing job to the running Flink cluster.
# Called by the flink-submit one-shot service after the cluster is healthy.
set -euo pipefail

JOB_MANAGER_REST="${JOB_MANAGER_REST:-http://flink-jobmanager:8081}"
JOB_SCRIPT="${JOB_SCRIPT:-/opt/project/flink/jobs/kafka_to_landing.py}"

# Source Polaris credentials (sets POLARIS_FLINK_CLIENT_ID / SECRET / REALM)
CRED_FILE="${POLARIS_CREDENTIAL_FILE:-/run/polaris/clients.env}"
if [[ -f "$CRED_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CRED_FILE"
    export POLARIS_FLINK_CLIENT_ID POLARIS_FLINK_CLIENT_SECRET POLARIS_REALM
fi

echo "[submit-job] Waiting for JobManager at ${JOB_MANAGER_REST} ..."
until curl -sf "${JOB_MANAGER_REST}/overview" > /dev/null 2>&1; do
    sleep 2
done
echo "[submit-job] JobManager is ready."

echo "[submit-job] Submitting: ${JOB_SCRIPT}"
exec flink run \
    --target remote \
    -m flink-jobmanager:8081 \
    --python "${JOB_SCRIPT}" \
    --pyFiles /opt/project/flink/jobs \
    "$@"
