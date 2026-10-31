# Database Seed Assets

These scripts initialize the source application before data generation.

- `seed_catalog.py`: Product categories, products/variants, opening inventory, welcome coupon and the bootstrap admin configured by `API_BOOTSTRAP_ADMIN_*`.
- `0010_multi_city_stores.py`: Idempotent initialization of the city/store reference data when needed.
- `__init__.py`: Python package marker.

MySQL initializes its tables from `database/schema.sql` when its data volume is empty. The API container then runs `seed_catalog` during startup. To repeat it inside the configured API container, run `docker compose exec -T ecommerce-api python -m database.seeds.seed_catalog`. `make seed` runs on the host and needs host-reachable API_DATABASE_URL and valid API_SECRET_KEY settings. Seeds insert source reference data, not table definitions.

Use the [generator](../../generator/README.md) for transactional history and access-log data. Other staff accounts and store assignments are created through the application.

Removing repository scripts does not delete records already present in an existing database.
