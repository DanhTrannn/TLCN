CALL {{catalog}}.system.rewrite_data_files(table => {{full_tbl}}, options => map('target-file-size-bytes', {{args_target_file_size_bytes}}))
