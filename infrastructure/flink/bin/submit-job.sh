#!/usr/bin/env bash
# Submit the PyFlink Pure Streaming kafka_to_lakehouse job to the running Flink cluster.
# Called by the flink-submit one-shot service after the cluster is healthy.
set -euo pipefail

JOB_MANAGER_ADDRESS="${JOB_MANAGER_ADDRESS:-flink-jobmanager:8081}"
JOB_SCRIPT="${JOB_SCRIPT:-/opt/project/flink/jobs/kafka_to_lakehouse.py}"

# Source Polaris credentials (sets POLARIS_FLINK_CLIENT_ID / SECRET / REALM)
CRED_FILE="${POLARIS_CREDENTIAL_FILE:-/run/polaris/clients.env}"
if [[ -f "$CRED_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CRED_FILE"
    export POLARIS_FLINK_CLIENT_ID POLARIS_FLINK_CLIENT_SECRET POLARIS_REALM
fi

# Flink CLI tries to write to $FLINK_CONF_DIR/flink-conf.yaml during startup.
# Since /opt/flink/conf is owned by root (read-only for flink user), we copy
# the config to a writable temp directory and point FLINK_CONF_DIR there.
FLINK_CONF_DIR_RW="$(mktemp -d)"
cp /opt/flink/conf/flink-conf.yaml "${FLINK_CONF_DIR_RW}/flink-conf.yaml" 2>/dev/null || true
export FLINK_CONF_DIR="${FLINK_CONF_DIR_RW}"

echo "[submit-job] Waiting for JobManager at ${JOB_MANAGER_ADDRESS} ..."
until curl -sf "http://${JOB_MANAGER_ADDRESS}/overview" > /dev/null 2>&1; do
    sleep 2
done
echo "[submit-job] JobManager is ready."

# Idempotency check: skip submission if job is already RUNNING
RUNNING_JOBS="$(curl -sf "http://${JOB_MANAGER_ADDRESS}/jobs/overview" 2>/dev/null || echo "{}")"
if echo "$RUNNING_JOBS" | grep -qE '"name":"(kafka_to_lakehouse_pure_streaming|insert-into_lakehouse)".*"state":"RUNNING"'; then
    echo "[submit-job] Streaming Lakehouse job is already RUNNING. Skipping."
    exit 0
fi

echo "[submit-job] Submitting PyFlink job: ${JOB_SCRIPT}"
exec /opt/flink/bin/flink run \
    -d \
    -m "${JOB_MANAGER_ADDRESS}" \
    --python "${JOB_SCRIPT}" \
    --pyFiles /opt/project/flink/jobs \
    "$@"
