SELECT MAX({{table_cursor_field}}) AS at, MAX({{table_pk}}) AS pk_at_max FROM {{table_name}} WHERE {{table_cursor_field_2}} = (SELECT MAX({{table_cursor_field_3}}) FROM {{table_name_2}})
