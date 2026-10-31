CALL {{catalog}}.system.remove_orphan_files(table => {{full_tbl}}, older_than => TIMESTAMP {{orphan_cutoff_sql}})
