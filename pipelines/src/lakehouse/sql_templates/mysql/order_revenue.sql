SELECT COALESCE(SUM(total_vnd), 0) AS value FROM `orders` WHERE status != 'cancelled'
