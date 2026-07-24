# Airflow config

Airflow dùng LocalExecutor và PostgreSQL metadata. Core DAG commit cursor độc lập; ML DAG chỉ nhận Gold publication đã thành công và không chặn core publication.

