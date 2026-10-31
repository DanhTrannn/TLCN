SELECT COALESCE(SUM(amount_vnd), 0) AS value FROM `payments` WHERE status = 'succeeded'
