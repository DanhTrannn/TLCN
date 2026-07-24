# Runbook

Runbook phải bao phủ clean setup, service health, seed/generator, scheduled run, manual run, rerun, replay, backfill, partial failure, fallback dataset và teardown.

Base commands hiện tại:

```bash
cp .env.example .env
make core-up
make batch-up
make bi-up
make validate
make down
```

