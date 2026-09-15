-- Tồn kho test cho POS

-- Store Sài Gòn (store_id = 7)
INSERT INTO store_inventory (store_id, variant_id, on_hand, opening_on_hand, version)
SELECT 7, variant_id, 10, 10, 1
FROM product_variants
WHERE is_active = 1
ON DUPLICATE KEY UPDATE on_hand = VALUES(on_hand);

-- Store Thủ Đức (store_id = 8)
INSERT INTO store_inventory (store_id, variant_id, on_hand, opening_on_hand, version)
SELECT 8, variant_id, 8, 8, 1
FROM product_variants
WHERE is_active = 1
ON DUPLICATE KEY UPDATE on_hand = VALUES(on_hand);

-- Store Hoàn Kiếm (store_id = 9)
INSERT INTO store_inventory (store_id, variant_id, on_hand, opening_on_hand, version)
SELECT 9, variant_id, 5, 5, 1
FROM product_variants
WHERE is_active = 1
ON DUPLICATE KEY UPDATE on_hand = VALUES(on_hand);
