-- Seed Data for Lakehouse Gold Marts

-- Clean existing seed data if any
DELETE FROM lakehouse.gold.mart_sales_daily WHERE order_date >= current_date() - INTERVAL 30 DAYS;
DELETE FROM lakehouse.gold.mart_logistics_performance WHERE shipment_date >= current_date() - INTERVAL 30 DAYS;
DELETE FROM lakehouse.gold.mart_inventory_health WHERE snapshot_date >= current_date() - INTERVAL 30 DAYS;
DELETE FROM lakehouse.gold.mart_product_returns WHERE return_date >= current_date() - INTERVAL 30 DAYS;
DELETE FROM lakehouse.gold.dim_product WHERE product_key > 0;
DELETE FROM lakehouse.gold.fact_order_item WHERE order_item_id > 0;

-- 1. Seed mart_sales_daily (14 days time-series across online and POS)
INSERT INTO lakehouse.gold.mart_sales_daily VALUES
(date_sub(current_date(), 13), 'online', 0, 1, 'Áo Thun & Polo', 18, 16, 2, 28, 9800000, 4900000, 4900000, 50.0),
(date_sub(current_date(), 13), 'pos', 1, 2, 'Quần Jeans & Kaki', 8, 8, 0, 12, 6200000, 3100000, 3100000, 50.0),
(date_sub(current_date(), 12), 'online', 0, 3, 'Áo Khoác & Blazer', 14, 12, 2, 19, 12500000, 6800000, 5700000, 45.6),
(date_sub(current_date(), 11), 'online', 0, 1, 'Áo Thun & Polo', 22, 20, 2, 35, 11900000, 5800000, 6100000, 51.3),
(date_sub(current_date(), 11), 'pos', 1, 1, 'Áo Thun & Polo', 10, 10, 0, 15, 5200000, 2600000, 2600000, 50.0),
(date_sub(current_date(), 10), 'online', 0, 2, 'Quần Jeans & Kaki', 16, 14, 2, 22, 9400000, 4700000, 4700000, 50.0),
(date_sub(current_date(), 9), 'online', 0, 4, 'Phụ Kiện Thời Trang', 25, 23, 2, 40, 7800000, 3500000, 4300000, 55.1),
(date_sub(current_date(), 9), 'pos', 1, 3, 'Áo Khoác & Blazer', 6, 6, 0, 8, 5600000, 3000000, 2600000, 46.4),
(date_sub(current_date(), 8), 'online', 0, 1, 'Áo Thun & Polo', 20, 19, 1, 30, 10500000, 5200000, 5300000, 50.5),
(date_sub(current_date(), 7), 'online', 0, 3, 'Áo Khoác & Blazer', 18, 17, 1, 24, 14200000, 7500000, 6700000, 47.2),
(date_sub(current_date(), 7), 'pos', 1, 2, 'Quần Jeans & Kaki', 12, 12, 0, 16, 8400000, 4200000, 4200000, 50.0),
(date_sub(current_date(), 6), 'online', 0, 1, 'Áo Thun & Polo', 26, 24, 2, 38, 13300000, 6500000, 6800000, 51.1),
(date_sub(current_date(), 5), 'online', 0, 2, 'Quần Jeans & Kaki', 21, 19, 2, 29, 11800000, 5900000, 5900000, 50.0),
(date_sub(current_date(), 5), 'pos', 1, 1, 'Áo Thun & Polo', 14, 14, 0, 20, 7000000, 3500000, 3500000, 50.0),
(date_sub(current_date(), 4), 'online', 0, 3, 'Áo Khoác & Blazer', 23, 21, 2, 31, 16500000, 8800000, 7700000, 46.7),
(date_sub(current_date(), 3), 'online', 0, 1, 'Áo Thun & Polo', 28, 26, 2, 42, 15400000, 7600000, 7800000, 50.6),
(date_sub(current_date(), 3), 'pos', 1, 4, 'Phụ Kiện Thời Trang', 15, 15, 0, 25, 4800000, 2100000, 2700000, 56.3),
(date_sub(current_date(), 2), 'online', 0, 2, 'Quần Jeans & Kaki', 24, 22, 2, 34, 13800000, 6900000, 6900000, 50.0),
(date_sub(current_date(), 1), 'online', 0, 1, 'Áo Thun & Polo', 32, 30, 2, 48, 17200000, 8400000, 8800000, 51.2),
(date_sub(current_date(), 1), 'pos', 1, 3, 'Áo Khoác & Blazer', 11, 11, 0, 14, 9800000, 5200000, 4600000, 46.9),
(current_date(), 'online', 0, 1, 'Áo Thun & Polo', 19, 18, 1, 27, 9500000, 4700000, 4800000, 50.5),
(current_date(), 'pos', 1, 2, 'Quần Jeans & Kaki', 9, 9, 0, 13, 6300000, 3150000, 3150000, 50.0);

-- 2. Seed mart_logistics_performance
INSERT INTO lakehouse.gold.mart_logistics_performance VALUES
(date_sub(current_date(), 6), 1, 'SHIP01', 1, 'Hồ Chí Minh', 25, 23, 2, 8.0, 22, 88.0, 45.0, 8400000),
(date_sub(current_date(), 5), 1, 'SHIP01', 1, 'Hồ Chí Minh', 28, 26, 2, 7.1, 25, 89.3, 42.0, 9200000),
(date_sub(current_date(), 4), 2, 'SHIP02', 1, 'Hồ Chí Minh', 20, 19, 1, 5.0, 19, 95.0, 38.0, 6800000),
(date_sub(current_date(), 3), 1, 'SHIP01', 1, 'Hồ Chí Minh', 30, 28, 2, 6.7, 27, 90.0, 40.0, 10500000),
(date_sub(current_date(), 2), 2, 'SHIP02', 1, 'Hồ Chí Minh', 26, 24, 2, 7.7, 23, 88.5, 43.0, 8900000),
(date_sub(current_date(), 1), 1, 'SHIP01', 1, 'Hồ Chí Minh', 35, 33, 2, 5.7, 32, 91.4, 39.0, 12400000),
(current_date(), 1, 'SHIP01', 1, 'Hồ Chí Minh', 18, 17, 1, 5.5, 17, 94.4, 35.0, 5800000);

-- 3. Seed mart_inventory_health
INSERT INTO lakehouse.gold.mart_inventory_health VALUES
(current_date(), 'warehouse', 0, 1, 'Áo Thun & Polo', 24, 0, 2, 1450, 290000000),
(current_date(), 'warehouse', 0, 2, 'Quần Jeans & Kaki', 18, 0, 1, 980, 245000000),
(current_date(), 'warehouse', 0, 3, 'Áo Khoác & Blazer', 12, 1, 3, 520, 208000000),
(current_date(), 'warehouse', 0, 4, 'Phụ Kiện Thời Trang', 15, 0, 0, 850, 85000000),
(current_date(), 'store', 1, 1, 'Áo Thun & Polo', 24, 1, 4, 320, 64000000),
(current_date(), 'store', 1, 2, 'Quần Jeans & Kaki', 18, 0, 2, 210, 52500000),
(current_date(), 'store', 1, 3, 'Áo Khoác & Blazer', 12, 0, 2, 110, 44000000);

-- 4. Seed mart_product_returns
INSERT INTO lakehouse.gold.mart_product_returns VALUES
(date_sub(current_date(), 3), 1, 1, 'Áo Thun Cotton Basic 220gsm', 'TSHIRT-BLK-M', 'M', 'Đen', 'refund', 'Khách mặc không vừa size', 2, 2, 700000),
(date_sub(current_date(), 1), 2, 2, 'Quần Jeans Slimfit Co Giãn', 'JEAN-BLU-31', '31', 'Xanh Indigo', 'exchange', 'Khách đổi sang size 32', 1, 1, 0);

-- 5. Seed dim_product
INSERT INTO lakehouse.gold.dim_product VALUES
(1, 1, 'Áo Thun Cotton Basic 220gsm', 1, 'Áo Thun & Polo', 350000, true),
(2, 2, 'Quần Jeans Slimfit Co Giãn', 2, 'Quần Jeans & Kaki', 550000, true),
(3, 3, 'Áo Khoác Bomber Kaki 2 Lớp', 3, 'Áo Khoác & Blazer', 750000, true),
(4, 4, 'Áo Polo Pique Thoáng Khí', 1, 'Áo Thun & Polo', 420000, true),
(5, 5, 'Ví Da Bò Sáp Cầm Tay', 4, 'Phụ Kiện Thời Trang', 380000, true);

-- 6. Seed fact_order_item (for Top Selling Products)
INSERT INTO lakehouse.gold.fact_order_item VALUES
(1, 1, 1, 1, 150, 350000, 52500000, 26250000, 26250000),
(2, 2, 2, 2, 90, 550000, 49500000, 24750000, 24750000),
(3, 3, 3, 3, 60, 750000, 45000000, 24000000, 21000000),
(4, 4, 4, 1, 75, 420000, 31500000, 15750000, 15750000),
(5, 5, 5, 4, 50, 380000, 19000000, 8550000, 10450000);
