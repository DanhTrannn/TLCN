-- Tồn kho test cho POS

-- Store HCM (store_id = 1)
INSERT INTO store_inventory (store_id, variant_id, on_hand, opening_on_hand, version)
SELECT 1, variant_id, 10, 10, 1
FROM product_variants
WHERE is_active = 1
ON DUPLICATE KEY UPDATE on_hand = VALUES(on_hand);

-- Store HN (store_id = 2)
INSERT INTO store_inventory (store_id, variant_id, on_hand, opening_on_hand, version)
SELECT 2, variant_id, 8, 8, 1
FROM product_variants
WHERE is_active = 1
ON DUPLICATE KEY UPDATE on_hand = VALUES(on_hand);

-- Store DN (store_id = 3)
INSERT INTO store_inventory (store_id, variant_id, on_hand, opening_on_hand, version)
SELECT 3, variant_id, 5, 5, 1
FROM product_variants
WHERE is_active = 1
ON DUPLICATE KEY UPDATE on_hand = VALUES(on_hand);
