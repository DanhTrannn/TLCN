import type { IconName } from "@/components/ui/Icon";
import type { RoleMetricsResponse } from "@/lib/api";

export type AnalyticsRole = RoleMetricsResponse["role"];

export const ANALYTICS_ROLES: { id: AnalyticsRole; label: string; icon: IconName; purpose: string; questions: string[]; scope: string }[] = [
  { id: "executive", label: "Tổng quan", icon: "dashboard", purpose: "Theo dõi kết quả tài chính và các khoản cần đối chiếu.", questions: ["Doanh thu và lợi nhuận đang ở mức nào?", "Xu hướng các ngày gần đây thay đổi ra sao?", "Khoản COD và giao thất bại nào cần kiểm tra?"], scope: "KPI: toàn bộ dữ liệu nguồn hiện có; xu hướng: kỳ riêng bên dưới." },
  { id: "sales", label: "Kinh doanh", icon: "bar-chart", purpose: "So sánh đóng góp của điểm bán, sản phẩm và danh mục.", questions: ["Điểm bán/kênh nào đóng góp nhiều doanh thu?", "Sản phẩm và danh mục nào dẫn đầu?", "Doanh thu theo ngày biến động thế nào?"], scope: "Phân nhóm: toàn bộ dữ liệu nguồn hiện có; xu hướng: kỳ riêng bên dưới." },
  { id: "store", label: "Cửa hàng", icon: "store", purpose: "Theo dõi kết quả trong ngày và SKU cần bổ sung tại cửa hàng.", questions: ["Hôm nay cửa hàng ghi nhận bao nhiêu doanh thu và đơn?", "Có bao nhiêu dòng tồn kho thấp?", "SKU nào đã hết để kiểm tra bổ sung?"], scope: "Doanh thu/đơn: hôm nay, Asia/Ho_Chi_Minh. Tồn kho: trạng thái hiện tại." },
  { id: "inventory", label: "Tồn kho", icon: "box", purpose: "Kiểm tra lượng tồn, giá trị tồn và rủi ro thiếu hàng.", questions: ["Hàng đang nằm tại kho hay cửa hàng?", "SKU nào đã hết?", "SKU nào có tốc độ bán cần kiểm tra?"], scope: "Tồn kho và cảnh báo: trạng thái hiện tại. Tốc độ bán: 60 phút gần nhất." },
  { id: "operations", label: "Vận hành", icon: "truck", purpose: "Ưu tiên đơn chờ xử lý, giao vận có vấn đề và đổi trả.", questions: ["Có bao nhiêu đơn chờ xuất?", "Đơn nào chờ quá 2 giờ?", "Khu vực COD nào cần kiểm tra với số mẫu cụ thể?"], scope: "Các trạng thái nghiệp vụ hiện có; chỉ số vùng COD có kỳ riêng trong định nghĩa." },
  { id: "marketing", label: "Marketing", icon: "ticket", purpose: "Đọc lượng tương tác theo bước và rà soát voucher, phản hồi.", questions: ["Các bước tương tác ghi nhận bao nhiêu sự kiện?", "Tỷ lệ mua/xem theo sự kiện là bao nhiêu?", "Voucher hay sản phẩm nào cần kiểm tra?"], scope: "Tương tác: cửa sổ API, thường 30 ngày. Voucher: 15 phút; đánh giá: cửa sổ từng tín hiệu." },
  { id: "system", label: "Chất lượng dữ liệu", icon: "shield", purpose: "Đánh giá độ mới của Gold và sai lệch giữa nguồn với Lakehouse.", questions: ["Gold đã được nạp cách đây bao lâu?", "Chỉ số đối soát nào đang lệch?", "Có đủ dữ liệu Lakehouse để kết luận hay chưa?"], scope: "Gold mới nhất so với MySQL hiện tại. Đây không phải trạng thái trực tiếp của tất cả job." },
];

export const CANONICAL_ROLES: Record<string, AnalyticsRole> = {
  admin: "executive", sales_manager: "sales", store_manager: "store", inventory_manager: "inventory",
  operations_manager: "operations", marketing_manager: "marketing", system_admin: "system",
};

export function isAnalyticsRole(value: string | null): value is AnalyticsRole {
  return ANALYTICS_ROLES.some(role => role.id === value);
}

export function sourceName(source?: string) {
  return source === "lakehouse" ? "Lakehouse · Trino / Iceberg" : source === "oltp" ? "MySQL · vận hành" : source === "oltp_fallback" ? "MySQL · nguồn thay thế" : "Chưa xác định nguồn";
}

export interface MetricDefinition {
  name: string;
  calculation: string;
  unit: string;
  grain: string;
  scope: string;
  caveat: string;
}

const definition = (name: string, calculation: string, unit: string, grain: string, scope: string, caveat: string): MetricDefinition => ({ name, calculation, unit, grain, scope, caveat });

export function metricDefinitions(metrics: RoleMetricsResponse): MetricDefinition[] {
  const fallback = metrics.data_source === "oltp_fallback";
  switch (metrics.role) {
    case "executive": return [
      definition("Doanh thu thuần", fallback ? "Thanh toán succeeded − hoàn tiền succeeded" : "SUM(fact_order.net_revenue_vnd)", "VND", "Đơn / toàn hệ thống", "Toàn bộ nguồn hiện có", fallback ? "Theo dòng tiền; khác công thức Gold." : "Loại failed_delivery/returned/cancelled/payment_failed; có thể gồm đơn chưa giao."),
      definition("Lợi nhuận gộp", fallback ? "Doanh thu thuần − giá vốn đơn delivered/completed" : "SUM(fact_order.net_profit_vnd)", "VND", "Đơn / toàn hệ thống", "Toàn bộ nguồn hiện có", "Chưa trừ đầy đủ vận hành, thuế và quảng cáo; âm cần kiểm tra."),
      definition("Tổng đơn", "COUNT(DISTINCT order_id)", "Đơn", "Đơn duy nhất", "Toàn bộ nguồn hiện có", "Bao gồm mọi trạng thái, không chỉ đơn đã giao."),
      definition("AOV", "Doanh thu thuần / tổng đơn", "VND/đơn", "Toàn hệ thống", "Cùng phạm vi KPI", "UI để trống khi không có đơn; API trả 0 nếu doanh thu không dương."),
      definition("GMV", fallback ? "SUM(orders.total_vnd), bỏ cancelled" : "SUM(fact_order.gross_revenue_vnd)", "VND", "Đơn", "Toàn bộ nguồn hiện có", "Gold gồm mọi trạng thái. Tổng đơn có thể chứa phí vận chuyển."),
      definition("Tỷ lệ giao thất bại", "Số đơn failed_delivery / tổng đơn × 100", "%", "Đơn", "Cùng phạm vi KPI", "Không đồng nghĩa tất cả đều là COD. Không có mẫu số thì UI hiển thị —."),
      definition("Tỷ lệ trả hàng", fallback ? "Đơn returned / tổng đơn × 100" : "SUM(total_return_requests) ở mart / tổng đơn × 100", "%", fallback ? "Đơn" : "Chi tiết trả hàng / đơn", "Cùng phạm vi KPI", "Gold có thể tính nhiều chi tiết trả hàng trên một đơn; không phải một lát cơ cấu đơn."),
      definition("COD đang giao", "SUM(order.total_vnd) của COD có shipment dispatched/in_transit", "VND", "Đơn/shipment", "OLTP hiện tại", "Không phải số dư tiền thực tế đơn vị giao hàng đang giữ."),
    ];
    case "sales": return [
      definition("Đóng góp điểm bán", fallback ? "Tổng order.total_vnd theo bộ lọc trạng thái của OLTP" : "SUM(fact_order.net_revenue_vnd) theo điểm bán/kênh", "VND", "Điểm bán / kênh", "Toàn bộ nguồn hiện có", "Không chịu bộ lọc kỳ của biểu đồ xu hướng."),
      definition("Sản phẩm dẫn đầu", fallback ? "SUM(quantity × unit_price_vnd), trạng thái paid/shipping/delivered/completed" : "SUM(fact_order_item.item_total_vnd), is_delivered = true", "VND / đơn vị", "Sản phẩm; top 10 do API trả", "Toàn bộ nguồn hiện có", "Phạm vi trạng thái khác tổng doanh thu theo điểm bán."),
      definition("Danh mục", "SUM(gross_revenue_vnd) của mart_sales_daily theo danh mục", "VND / %", "Danh mục", "Toàn bộ nguồn hiện có", "OLTP fallback dùng chi tiết đơn. Không cộng số đơn qua danh mục để suy ra đơn duy nhất."),
    ];
    case "store": return [
      definition("Doanh thu hôm nay", "SUM(order.total_vnd), trạng thái paid/shipping/delivered/completed", "VND", "Đơn tại cửa hàng được chọn", "Từ 00:00 Asia/Ho_Chi_Minh", "Không phải doanh thu kế toán; bộ lọc cửa hàng áp dụng toàn bộ góc nhìn này."),
      definition("Đơn hôm nay", "COUNT(orders) với cùng bộ lọc doanh thu", "Đơn", "Đơn tại cửa hàng", "Hôm nay", "Không so sánh với hôm qua vì API chưa cung cấp kỳ trước."),
      definition("Tồn thấp", "COUNT(store_inventory) có on_hand ≤ 5", "Dòng tồn", "SKU × cửa hàng", "Hiện tại", "Bao gồm các dòng đã hết hàng; không cộng với số dòng hết hàng."),
    ];
    case "inventory": return [
      definition("Giá trị tồn", "SUM(on_hand × variant.cost_price_vnd)", "VND", "SKU × địa điểm", "Hiện tại", "Định giá theo giá vốn hiện có, không phải giá bán."),
      definition("Lượng tồn", "SUM(on_hand) theo kho/cửa hàng", "Đơn vị", "SKU × địa điểm", "Hiện tại", "Hai nhóm địa điểm là cơ cấu lượng hàng, không phải cơ cấu SKU."),
      definition("SKU có điểm hết hàng", "COUNT(DISTINCT variant_id) có ít nhất một địa điểm on_hand = 0", "SKU", "SKU duy nhất", "Hiện tại", "Không phải số cặp SKU–địa điểm; bảng chi tiết có thể chỉ là tập con API trả về."),
      definition("Tốc độ bán", "Số lượng bán 60 phút / 60", "Đơn vị/phút", "SKU", "60 phút gần nhất", "Ước tính thời gian hết hàng chỉ theo tốc độ gần đây; không phải dự báo ML."),
    ];
    case "operations": return [
      definition("Chờ xuất", "COUNT(orders) trạng thái paid/confirmed/processing", "Đơn", "Đơn", "Hiện tại", "Không cộng với các chỉ số shipment/return để suy ra tổng đơn."),
      definition("Giao vận cần kiểm tra", "COUNT(shipments) có attempt_count > 1 hoặc status = failed", "Shipment", "Lần giao", "Dữ liệu hiện có", "Tên API shipping_sla_violations_count; không đo vi phạm deadline SLA."),
      definition("Giao thất bại", "COUNT(shipments) có status = failed", "Shipment", "Lần giao", "Dữ liệu hiện có", "Có thể giao với nhóm giao vận cần kiểm tra; không dùng donut cơ cấu."),
      definition("Chờ quá 2 giờ", "Đơn paid/confirmed có created_at trước ngưỡng 2 giờ", "Đơn", "Đơn", "Hiện tại", "Ngưỡng phát hiện của API, không phải SLA cam kết."),
      definition("COD theo vùng", "Shipment COD failed / tổng shipment COD trong vùng × 100", "%", "Nhóm địa chỉ", "Toàn bộ shipment COD hiện có", "Vùng dựa trên từ khóa địa chỉ. Luôn đọc số mẫu; chưa có ngưỡng mẫu tối thiểu."),
    ];
    case "marketing": return [
      definition("Đầu phễu", fallback ? "MAX(cart items + số đơn, khách hàng tạo mới)" : "COUNT(events) có action product_detail/catalog_search hoặc route sản phẩm", fallback ? "Proxy" : "Sự kiện", fallback ? "Tổng hợp OLTP" : "Event", `${metrics.funnel_window_days} ngày`, "Không phải số người truy cập duy nhất hoặc chuỗi session."),
      definition("Bước mua", fallback ? "Số đơn không cancelled trong kỳ" : "COUNT(order_complete/order_confirm_internal hoặc checkout_submit thành công)", fallback ? "Đơn" : "Sự kiện", fallback ? "Đơn" : "Event", `${metrics.funnel_window_days} ngày`, "Các bước có thể chồng lặp; không tự suy ra số người bỏ giỏ."),
      definition("Mua / đầu phễu", "total_purchases / total_visitors × 100", "%", fallback ? "Proxy OLTP" : "Tỷ số event", "Cùng cửa sổ phễu", "Mẫu số 0 → —. Có thể vượt 100%; không phải xác suất chuyển đổi của người dùng."),
      definition("Voucher", "Số lượt dùng trong 15 phút / 15; used_count / usage_limit × 100 nếu có hạn mức", "Lượt/phút / %", "Mã voucher API chọn", "Tốc độ: 15 phút; used_count: tổng lượt dùng", "Không có hạn mức không có nghĩa là đã dùng 0% ngân sách."),
      definition("Đánh giá tiêu cực", "Đếm đánh giá 1–2 sao theo sản phẩm", "Đánh giá", "Sản phẩm", "window_minutes do API trả", "Tín hiệu để kiểm tra; chưa đủ bằng chứng kết luận nguyên nhân chất lượng."),
    ];
    case "system": return [
      definition("Tuổi dữ liệu Gold", "NOW − MAX(fact_order._gold_ingested_at)", "Phút", "Lần nạp fact_order gần nhất", "Snapshot hiện tại", "Không phải tuổi từng bản ghi, độ trễ CDC hay tình trạng trực tiếp Spark/Flink."),
      definition("Sai lệch đối soát", "ABS(MySQL − Lakehouse) / ABS(MySQL) × 100", "%", "Một chỉ số đối soát", "Toàn bộ nguồn và Gold hiện tại", "Nguồn 0/đích khác 0 → 100%. Khi fallback, giá trị Gold thay thế không dùng để kết luận."),
      definition("Trạng thái dữ liệu", "Đánh giá từ freshness và variance", "Trạng thái", "Phản hồi API", "Hiện tại", "UI: degraded nếu >5% hoặc >15 phút; unhealthy nếu >20%, >60 phút hoặc thiếu freshness. Gate pipeline mặc định 0,05%, khác ngưỡng UI."),
    ];
  }
}
