SELECT COALESCE(SUM(amount_vnd), 0) AS value FROM `refunds` WHERE status = 'succeeded'
