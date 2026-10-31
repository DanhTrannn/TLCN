SELECT MIN({{table_pk}}) AS lo, MAX({{table_pk_2}}) AS hi FROM {{table_name}}{{range_pred}}
