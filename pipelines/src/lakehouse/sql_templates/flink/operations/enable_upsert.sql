ALTER TABLE {{tbl}} SET (
    'format-version' = '2',
    'write.upsert.enabled' = 'true',
    'write.delete.mode' = 'merge-on-read',
    'write.update.mode' = 'merge-on-read',
    'write.merge.mode'  = 'merge-on-read'
)
