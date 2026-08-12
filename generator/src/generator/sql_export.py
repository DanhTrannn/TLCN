from __future__ import annotations

import hashlib
from bisect import bisect_left, bisect_right
import random
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TextIO, TypeAlias
from zoneinfo import ZoneInfo

from argon2.low_level import Type, hash_secret

from generator import __version__
from generator.config import (
    CATEGORY_NAMES,
    CustomerClass,
    DistributionConfig,
    GeneratorConfig,
    PriceBand,
    SaleEvent,
    TetWindow,
)


DEMO_PASSWORD = "Demo@12345"
PRODUCT_IMAGE_URL = "https://sixdo.vn/modules/uniform/assets/image/aotruoc.webp"
FEMALE_CUSTOMER_SHARE = 0.80
STREET_NAMES = (
    "Nguyễn Huệ", "Lê Lợi", "Trần Hưng Đạo", "Cách Mạng Tháng Tám", "Hai Bà Trưng",
    "Nguyễn Trãi", "Nguyễn Thị Minh Khai", "Phạm Ngọc Thạch", "Võ Thị Sáu",
    "Xô Viết Nghệ Tĩnh", "Cao Thắng", "Nguyễn Công Trứ", "Lê Thánh Tôn",
    "Phan Đăng Lưu", "Ngô Văn Năm", "Trần Phú", "Lê Văn Sỹ",
    "Phạm Văn Đồng", "Tô Hiệu", "Võ Văn Tần", "Trương Định", "Ngô Gia Tự",
    "Bạch Đằng", "Điện Biên Phủ", "Nguyễn Thái Học", "Quang Trung",
    "Nguyễn Văn Cừ", "An Dương Vương", "Hồng Bàng", "Phan Đăng Phúc",
    "Tôn Đức Thắng", "Trần Quốc Toản", "Nguyễn Tri Phương", "Lý Thường Kiệt",
    "Trần Quang Khải", "Phan Bội Châu", "Lý Tự Trọng", "Châu Văn Liêm",
    "Lê Lai", "Ngô Quyền", "Đề Thám", "Nguyễn Thượng Hiền", "Yết Kiêu",
    "Trần Khánh Dư", "Nguyễn Oanh", "Huỳnh Tấn Phát", "Lê Đức Thọ",
    "Hoàng Văn Hoan", "Nguyễn Khánh Biểu",
)
WARD_NAMES = (
    "Thảo Điền", "Bình Khánh", "An Phú", "Cát Lái", "Thủ Thiêm",
    "Bến Nghé", "Bến Thành", "Cầu Ông Lãnh", "Nguyễn Cư Trinh", "Cầu Giấy",
    "Đa Cao", "Tân Định", "Võ Thị Sáu", "Tân Sơn Nhất", "Phú Thọ",
    "Linh Tây", "An Hòa", "Linh Xuân", "Bình Trưng Tây", "Thạnh Mỹ Lợi",
    "Vĩnh Lộc B", "An Lạc",
)
DISTRICT_NAMES = (
    "Quận 1", "Quận 3", "Quận 5", "Quận 10", "Bình Thạnh", "Gò Vấp",
    "Tân Bình", "Tân Phú", "Phú Nhuận", "Thủ Đức", "Hóc Môn", "Bình Chánh",
)
INSERT_BATCH_SIZE = 1_000
SYNTHETIC_ARCHIVED_PRODUCT_DIVISOR = 20
SYNTHETIC_PRODUCT_ARCHIVE_REASON = "Ngừng kinh doanh theo kịch bản synthetic"
SYNTHETIC_COUPON_ARCHIVE_REASON = "Kết thúc chiến dịch synthetic"
FAMILY_NAMES = (
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đinh", "Mai", "Tô",
    "Đoàn", "Hà", "Trịnh", "Lâm", "Tăng", "Châu", "Lương", "Phùng", "Quách",
    "Hứa", "Triệu", "Thạch", "Giang", "Khương", "Bạch", "Tạ", "Đồng",
    "Cao", "Đàm", "Kiều",
)
FEMALE_MIDDLE_NAMES = (
    "Thị", "Thu", "Thuỳ", "Hồng", "Ngọc", "Kim", "Thanh", "Minh",
    "Anh", "Diệu", "Khánh", "Lan", "Huệ", "Cẩm", "Mỹ", "Trúc", "Ánh",
)
FEMALE_GIVEN_NAMES = (
    "Lan", "Hoa", "Hồng", "Mai", "Ngọc", "Thảo", "Trang", "Linh", "Hương",
    "Ngân", "Anh", "Hà", "Vy", "Uyên", "Phương", "Quỳnh", "Thu", "Hiền",
    "Yến", "Như", "Xuân", "Hạnh", "Dung", "Diễm", "Châu", "Thanh", "Khánh",
    "Tuyết", "Hiếu", "Huyền", "Vân", "Thư", "Nhi", "Bích", "Cúc",
    "Đào", "Trâm", "Quyên", "Hằng", "Sen", "Trúc", "Oanh",
)
MALE_MIDDLE_NAMES = (
    "Văn", "Quốc", "Minh", "Đức", "Công", "Hữu", "Anh", "Tuấn", "Huy",
    "Quang", "Mạnh", "Nhật", "Hồng", "Kim", "Trung", "Duy", "Chí", "Gia",
)
MALE_GIVEN_NAMES = (
    "Minh", "Hùng", "Đức", "Nam", "Huy", "Tuấn", "Long", "Sơn", "Dũng",
    "An", "Bình", "Cường", "Dương", "Hải", "Khánh", "Kiên", "Lâm", "Mạnh",
    "Nghĩa", "Phúc", "Quang", "Thắng", "Thọ", "Tiến", "Trung", "Việt",
    "Bảo", "Chí", "Giang", "Hiếu", "Hoàng", "Khoa", "Luân",
)
SIZES = ("XS", "S", "M", "L", "XL")
COLORS = ("BLACK", "WHITE", "RED", "GREEN", "BLUE", "YELLOW", "PINK", "PURPLE", "ORANGE", "BROWN", "GRAY", "BEIGE")
LEAF_CATEGORIES = tuple((code, name) for code, name in CATEGORY_NAMES.items())

PRODUCT_NAME_TEMPLATES: dict[str, tuple[str, ...]] = {
    "ao": (
        "Áo thun nữ cổ tròn form rộng",
        "Áo sơ mi nữ tay dài form suông",
        "Áo kiểu nữ cổ vuông tay phồng",
        "Áo croptop nữ dáng ôm",
        "Áo polo nữ dệt kim",
        "Áo blouse nữ tay bồng",
        "Áo len nữ cổ lọ dệt gân",
        "Áo cardigan nữ dáng ngắn",
        "Áo hai dây nữ chất satin",
        "Áo peplum nữ chiết eo",
        "Áo hoodie nữ form rộng",
        "Áo thun nữ cổ tim dáng ôm",
    ),
    "quan": (
        "Quần jeans nữ ống rộng lưng cao",
        "Quần tây nữ ống suông công sở",
        "Quần culottes nữ cạp cao",
        "Quần short nữ lưng cao",
        "Quần jogger nữ form thoải mái",
        "Quần legging nữ co giãn",
        "Quần kaki nữ ống đứng",
        "Quần jeans nữ ống loe",
        "Quần linen nữ ống rộng",
        "Quần baggy nữ lưng cao",
    ),
    "vay": (
        "Chân váy chữ A lưng cao",
        "Chân váy xếp ly dáng midi",
        "Chân váy satin dáng dài",
        "Chân váy jeans chữ A",
        "Chân váy tennis xếp ly",
        "Chân váy bút chì công sở",
        "Chân váy maxi hoa nhí",
        "Chân váy đuôi cá nữ",
        "Chân váy cargo túi hộp",
        "Chân váy midi xẻ tà",
    ),
    "dam": (
        "Đầm midi hoa nhí cổ vuông",
        "Đầm suông nữ cổ tròn",
        "Đầm body nữ tay dài",
        "Đầm dự tiệc nữ chiết eo",
        "Đầm sơ mi nữ dáng midi",
        "Đầm babydoll nữ tay phồng",
        "Đầm hai dây nữ chất satin",
        "Đầm wrap nữ cổ chữ V",
        "Đầm maxi nữ dáng xòe",
        "Đầm công sở nữ cổ vest",
    ),
    "khoac": (
        "Áo blazer nữ dáng suông",
        "Áo khoác denim nữ form rộng",
        "Áo bomber nữ dáng ngắn",
        "Áo trench coat nữ thắt eo",
        "Áo khoác dạ nữ dáng dài",
        "Áo khoác chống nắng nữ",
        "Áo phao nữ dáng ngắn",
        "Áo khoác tweed nữ cổ tròn",
        "Áo gile nữ phong cách công sở",
        "Áo khoác kaki nữ túi hộp",
    ),
    "phu-kien": (
        "Thắt lưng nữ bản nhỏ",
        "Mũ bucket nữ vành mềm",
        "Khăn lụa nữ họa tiết thanh lịch",
        "Kính mát nữ gọng vuông",
        "Bông tai nữ dáng tròn",
        "Vòng cổ nữ dây mảnh",
        "Kẹp tóc nữ bản lớn",
        "Tất nữ cổ cao phong cách Hàn Quốc",
        "Mũ lưỡi trai nữ tối giản",
        "Khăn choàng nữ chất mềm",
    ),
    "giay": (
        "Giày sneaker nữ đế nhẹ",
        "Sandal nữ quai mảnh",
        "Giày cao gót nữ mũi nhọn",
        "Giày loafer nữ đế thấp",
        "Giày búp bê nữ đính nơ",
        "Giày mule nữ mũi vuông",
        "Boot nữ cổ thấp",
        "Dép nữ quai ngang đế mềm",
        "Giày thể thao nữ đế tăng chiều cao",
        "Sandal nữ đế xuồng",
    ),
    "tui-xach": (
        "Túi đeo vai nữ dáng hộp",
        "Túi tote nữ cỡ lớn",
        "Túi baguette nữ dáng dài",
        "Túi đeo chéo nữ mini",
        "Túi xách nữ khóa kim loại",
        "Túi bucket nữ dây rút",
        "Ví cầm tay nữ dáng mỏng",
        "Túi laptop nữ chống sốc",
        "Túi hobo nữ dáng mềm",
        "Túi hộp nữ quai xách",
    ),
}

PRODUCT_MODEL_CODES = {
    "ao": "AO",
    "quan": "QU",
    "vay": "CV",
    "dam": "DM",
    "khoac": "AK",
    "phu-kien": "PK",
    "giay": "GI",
    "tui-xach": "TX",
}

PRODUCT_COLLECTIONS = (
    "Everyday",
    "Modern Office",
    "Weekend",
    "Minimal",
    "Urban Muse",
    "Soft Feminine",
    "Holiday",
    "Essential",
)

PRODUCT_DESCRIPTION_BY_CATEGORY = {
    "ao": "Thiết kế dễ phối cùng quần hoặc chân váy cho nhiều hoàn cảnh.",
    "quan": "Phom quần cân đối, phù hợp phong cách đi làm và dạo phố.",
    "vay": "Dáng váy tôn tỷ lệ cơ thể và dễ kết hợp với nhiều kiểu áo.",
    "dam": "Thiết kế nữ tính, phù hợp đi làm, đi chơi hoặc dự tiệc tùy kiểu dáng.",
    "khoac": "Lớp khoác hoàn thiện trang phục và phù hợp nhiều điều kiện thời tiết.",
    "phu-kien": "Phụ kiện tạo điểm nhấn và hoàn thiện phong cách hằng ngày.",
    "giay": "Thiết kế cân bằng giữa thẩm mỹ và sự thoải mái khi di chuyển.",
    "tui-xach": "Kiểu túi tiện dụng, phù hợp mang theo các vật dụng cá nhân thiết yếu.",
}


@dataclass(frozen=True)
class SqlExpression:
    value: str


SqlValue: TypeAlias = str | int | bool | datetime | None | SqlExpression


@dataclass(frozen=True)
class CategoryRecord:
    category_id: int
    code: str
    name: str


@dataclass(frozen=True)
class ProductRecord:
    product_id: int
    public_id: uuid.UUID
    category: CategoryRecord
    slug: str
    name: str


@dataclass(frozen=True)
class VariantRecord:
    variant_id: int
    product: ProductRecord
    public_id: uuid.UUID
    sku: str
    size_code: str
    color_code: str
    price_vnd: int


@dataclass(frozen=True)
class CouponRecord:
    coupon_id: int
    code: str
    discount_type: str
    discount_value: int
    minimum_subtotal_vnd: int
    starts_at: datetime
    ends_at: datetime
    kind: str
    campaign_day: date | None = None


REVIEW_CONTENT_BY_RATING: dict[int, tuple[str, ...]] = {
    1: (
        "Sản phẩm khác mô tả, chất liệu không như mong đợi.",
        "Form không phù hợp và màu thực tế lệch khá nhiều.",
    ),
    2: (
        "Đóng gói ổn nhưng form hơi khó mặc, cần cải thiện chất liệu.",
        "Giao đúng mẫu nhưng đường may chưa tốt như kỳ vọng.",
    ),
    3: (
        "Sản phẩm dùng ổn trong tầm giá, form hơi rộng một chút.",
        "Màu đẹp, chất liệu ở mức khá và giao hàng đúng hẹn.",
    ),
    4: (
        "Form đẹp, màu giống ảnh và chất vải khá thoải mái.",
        "Đóng gói cẩn thận, mặc vừa và sẽ cân nhắc mua thêm màu khác.",
    ),
    5: (
        "Rất ưng form và chất liệu, màu lên đẹp như hình.",
        "Sản phẩm đẹp, giao nhanh, đóng gói kỹ và đúng size đã chọn.",
    ),
}

REVIEW_REJECTION_REASONS = (
    "Nội dung không liên quan đến sản phẩm",
    "Nội dung lặp hoặc không cung cấp thông tin hữu ích",
    "Ngôn từ không phù hợp quy định cộng đồng",
)


@dataclass(frozen=True)
class DatasetSummary:
    sql_path: Path
    generation_run_id: str
    demo_email: str
    demo_password: str
    customers: int
    products: int
    variants: int
    orders: int


def _sql_literal(value: SqlValue) -> str:
    if isinstance(value, SqlExpression):
        return value.value
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC).replace(tzinfo=None)
        return f"'{normalized.strftime('%Y-%m-%d %H:%M:%S.%f')}'"
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def _binary_uuid(value: uuid.UUID) -> SqlExpression:
    return SqlExpression(f"UUID_TO_BIN('{value}')")


def _vietnamese_name(name_randomizer: random.Random) -> str:
    is_female = name_randomizer.random() < FEMALE_CUSTOMER_SHARE
    family_name = name_randomizer.choice(FAMILY_NAMES)
    if is_female:
        middle_name = name_randomizer.choice(FEMALE_MIDDLE_NAMES)
        given_name = name_randomizer.choice(FEMALE_GIVEN_NAMES)
    else:
        middle_name = name_randomizer.choice(MALE_MIDDLE_NAMES)
        given_name = name_randomizer.choice(MALE_GIVEN_NAMES)
    return f"{family_name} {middle_name} {given_name}"


def _vietnamese_address(address_randomizer: random.Random) -> str:
    house_number = address_randomizer.randint(1, 999)
    street_name = address_randomizer.choice(STREET_NAMES)
    ward_name = address_randomizer.choice(WARD_NAMES)
    district_name = address_randomizer.choice(DISTRICT_NAMES)
    return (
        f"Số {house_number}, đường {street_name}, phường {ward_name}, "
        f"{district_name}, TP. Hồ Chí Minh"
    )


def _write_insert(
    stream: TextIO,
    table: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[SqlValue]],
) -> None:
    if not rows:
        return
    column_sql = ", ".join(f"`{column}`" for column in columns)
    stream.write(f"INSERT INTO `{table}` ({column_sql}) VALUES\n")
    for index, row in enumerate(rows):
        suffix = ";\n\n" if index == len(rows) - 1 else ",\n"
        stream.write("  (" + ", ".join(_sql_literal(value) for value in row) + ")" + suffix)


def _chunks(values: Sequence[Sequence[SqlValue]], size: int = INSERT_BATCH_SIZE) -> Iterable[Sequence[Sequence[SqlValue]]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _write_batched(
    stream: TextIO,
    table: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[SqlValue]],
) -> None:
    for batch in _chunks(rows):
        _write_insert(stream, table, columns, batch)


def _entity_uuid(namespace: uuid.UUID, entity: str, index: int) -> uuid.UUID:
    return uuid.uuid5(namespace, f"{entity}:{index}")


def _identifier_uuid(namespace: uuid.UUID, identifier: str, index: int = 0) -> str:
    return str(_entity_uuid(namespace, identifier, index))


def _deterministic_password_hash(logical_identity: str) -> str:
    salt = hashlib.sha256(f"{logical_identity}:demo-password".encode()).digest()[:16]
    return hash_secret(
        secret=DEMO_PASSWORD.encode(),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID,
    ).decode()


def _validate_scale(config: GeneratorConfig) -> tuple[int, int, int, int]:
    required = ("customers", "products", "variants", "orders")
    missing = [key for key in required if key not in config.scale]
    if missing:
        raise ValueError(f"missing scale keys: {missing}")

    customer_count = config.scale["customers"]
    product_count = config.scale["products"]
    variant_count = config.scale["variants"]
    order_count = config.scale["orders"]
    if customer_count < 1 or product_count < 1 or order_count < 0:
        raise ValueError("customers/products must be positive and orders must be non-negative")
    if variant_count < product_count:
        raise ValueError("variants must be greater than or equal to products")
    if variant_count > product_count * len(SIZES) * len(COLORS):
        raise ValueError("variant scale exceeds unique size/color combinations")
    return customer_count, product_count, variant_count, order_count


def _timestamp_between(randomizer: random.Random, start: datetime, end: datetime) -> datetime:
    span_seconds = max(1, int((end - start).total_seconds()))
    return start + timedelta(seconds=randomizer.randrange(span_seconds))


def _weighted_index(randomizer: random.Random, weights: Sequence[int | float]) -> int:
    total = sum(weights)
    target = randomizer.random() * total
    cumulative = 0.0
    for index, weight in enumerate(weights):
        cumulative += weight
        if target < cumulative:
            return index
    return len(weights) - 1


def _largest_remainder(values: Sequence[float], total: int) -> list[int]:
    floors = [int(value) for value in values]
    remainder = total - sum(floors)
    ordered = sorted(range(len(values)), key=lambda i: values[i] - floors[i], reverse=True)
    for position in range(remainder):
        floors[ordered[position % len(ordered)]] += 1
    return floors


def _class_assignment(
    customer_count: int,
    classes: Sequence[CustomerClass],
    randomizer: random.Random,
) -> list[str]:
    counts = _largest_remainder(
        [class_.share * customer_count for class_ in classes], customer_count
    )
    assignment: list[str] = []
    for class_, count in zip(classes, counts):
        assignment.extend([class_.name] * count)
    randomizer.shuffle(assignment)
    if "loyal" in assignment and assignment[0] != "loyal":
        loyal_index = assignment.index("loyal")
        assignment[0], assignment[loyal_index] = assignment[loyal_index], assignment[0]
    return assignment


def _order_targets(
    assignment: Sequence[str],
    class_by_name: dict[str, CustomerClass],
    demo_target: int,
    total_orders: int,
    randomizer: random.Random,
) -> list[int]:
    if len(assignment) == 1:
        return [total_orders]
    demo = min(demo_target, total_orders)
    remaining = total_orders - demo
    raw = []
    for name in assignment[1:]:
        class_ = class_by_name[name]
        raw.append(randomizer.randint(class_.orders_min, class_.orders_max))
    if remaining == 0:
        return [demo] + [0] * len(raw)
    raw_sum = sum(raw)
    scaled = [value * remaining / raw_sum for value in raw]
    return [demo] + _largest_remainder(scaled, remaining)


def _nth_weekday(year: int, month: int, weekday: int, week_index: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (week_index - 1))


def _event_day(event: SaleEvent, year: int) -> date | None:
    if event.day is not None:
        try:
            return date(year, event.month, event.day)
        except ValueError:
            return None
    if event.weekday is not None and event.week_index is not None:
        return _nth_weekday(year, event.month, event.weekday, event.week_index)
    return None


def _tet_factor(day: date, tet: TetWindow) -> float:
    start = date(day.year, tet.month_start, tet.day_start)
    end = (
        date(day.year + 1, tet.month_end, tet.day_end)
        if tet.month_end < tet.month_start
        else date(day.year, tet.month_end, tet.day_end)
    )
    if not (start <= day <= end):
        return 1.0
    center = start + (end - start) / 2
    half_span = max(1, (end - start).days // 2)
    distance = abs((day - center).days) / half_span
    return 1.0 + (tet.peak - 1.0) * max(0.0, 1.0 - distance)


def _sale_boost(day: date, distributions: DistributionConfig) -> float:
    boost = 1.0
    for event in distributions.sales:
        event_day = _event_day(event, day.year)
        if event_day is None:
            continue
        if event_day <= day <= event_day + timedelta(days=event.after_days):
            boost *= event.boost
    return boost


def _build_day_weights(
    history_start: date,
    history_end: date,
    distributions: DistributionConfig,
) -> tuple[list[date], list[float]]:
    days: list[date] = []
    weights: list[float] = []
    current = history_start
    while current <= history_end:
        days.append(current)
        weight = distributions.day_of_week[current.weekday()]
        weight *= _tet_factor(current, distributions.tet)
        weight *= _sale_boost(current, distributions)
        weights.append(weight)
        current += timedelta(days=1)
    return days, weights


def _hour_weights_for_day(
    day: date,
    distributions: DistributionConfig,
) -> Sequence[float]:
    if _sale_boost(day, distributions) > 1:
        return distributions.campaign_hour_of_day
    return distributions.hour_of_day


def _pick_base_datetime(
    randomizer: random.Random,
    history_start: datetime,
    history_end: datetime,
    days: Sequence[date],
    day_weights: Sequence[float],
    distributions: DistributionConfig,
) -> datetime:
    day = days[_weighted_index(randomizer, day_weights)]
    hour = _weighted_index(randomizer, _hour_weights_for_day(day, distributions))
    minute = randomizer.randrange(60)
    business_zone = ZoneInfo(distributions.business_timezone)
    local_candidate = datetime(
        day.year,
        day.month,
        day.day,
        hour,
        minute,
        tzinfo=business_zone,
    )
    return min(max(local_candidate.astimezone(UTC), history_start), history_end)


def _shape_hour(
    randomizer: random.Random,
    moment: datetime,
    distributions: DistributionConfig,
) -> datetime:
    business_zone = ZoneInfo(distributions.business_timezone)
    local_moment = moment.astimezone(business_zone)
    weights = _hour_weights_for_day(local_moment.date(), distributions)
    hour = _weighted_index(randomizer, weights)
    return local_moment.replace(
        hour=hour,
        minute=randomizer.randrange(60),
        second=0,
        microsecond=0,
    ).astimezone(UTC)


def _campaign_instances(
    history_start: datetime,
    history_end: datetime,
    distributions: DistributionConfig,
) -> list[tuple[SaleEvent, datetime]]:
    business_zone = ZoneInfo(distributions.business_timezone)
    local_start = history_start.astimezone(business_zone)
    local_end = history_end.astimezone(business_zone)
    instances: list[tuple[SaleEvent, datetime]] = []
    for year in range(local_start.year, local_end.year + 1):
        for event in distributions.sales:
            event_date = _event_day(event, year)
            if event_date is None:
                continue
            moment = datetime(
                event_date.year,
                event_date.month,
                event_date.day,
                tzinfo=business_zone,
            ).astimezone(UTC)
            if history_start <= moment < history_end:
                instances.append((event, moment))
    return sorted(instances, key=lambda item: (item[1], item[0].name))


def _snap_to_campaign(
    randomizer: random.Random,
    tentative: datetime,
    previous: datetime,
    history_end: datetime,
    campaign_days: Sequence[date],
    affinity: float,
    distributions: DistributionConfig,
) -> datetime:
    if randomizer.random() >= affinity or not campaign_days:
        return _shape_hour(randomizer, tentative, distributions)
    business_zone = ZoneInfo(distributions.business_timezone)
    local_previous = previous.astimezone(business_zone)
    local_tentative = tentative.astimezone(business_zone)
    local_history_end = history_end.astimezone(business_zone)
    window_start = max(local_previous.date(), local_tentative.date() - timedelta(days=7))
    window_end = min(local_history_end.date(), local_tentative.date() + timedelta(days=7))
    left = bisect_left(campaign_days, window_start)
    right = bisect_right(campaign_days, window_end)
    if left >= right:
        return _shape_hour(randomizer, tentative, distributions)
    selected_day = campaign_days[randomizer.randrange(left, right)]
    snapped = local_tentative.replace(
        year=selected_day.year,
        month=selected_day.month,
        day=selected_day.day,
    ).astimezone(UTC)
    if snapped < previous:
        return _shape_hour(randomizer, tentative, distributions)
    return _shape_hour(randomizer, min(snapped, history_end), distributions)


def _mapping_value(values: Sequence[tuple[str, float]], key: str) -> float:
    return dict(values)[key]


def _weighted_pair(
    randomizer: random.Random,
    values: Sequence[tuple[str, int | float]],
) -> str:
    return values[_weighted_index(randomizer, [weight for _, weight in values])][0]


def _coupon_discount(coupon: CouponRecord, subtotal_vnd: int) -> int:
    if coupon.discount_type == "percentage":
        return subtotal_vnd * coupon.discount_value // 100
    return min(coupon.discount_value, subtotal_vnd)


def _select_coupon(
    randomizer: random.Random,
    coupons: Sequence[CouponRecord],
    order_time: datetime,
    subtotal_vnd: int,
    customer_class: str,
    is_first_order: bool,
    distributions: DistributionConfig,
) -> CouponRecord | None:
    eligible = [
        coupon
        for coupon in coupons
        if coupon.starts_at <= order_time < coupon.ends_at
        and subtotal_vnd >= coupon.minimum_subtotal_vnd
    ]
    if not eligible:
        return None

    behavior = distributions.coupons
    multiplier = _mapping_value(behavior.customer_multipliers, customer_class)
    midnight = [coupon for coupon in eligible if coupon.kind == "midnight"]
    campaign = [coupon for coupon in eligible if coupon.kind == "campaign"]
    welcome = [coupon for coupon in eligible if coupon.kind == "welcome"]
    everyday = [coupon for coupon in eligible if coupon.kind == "everyday"]

    candidates: Sequence[CouponRecord]
    rate: float
    local_hour = order_time.astimezone(
        ZoneInfo(distributions.business_timezone)
    ).hour
    if midnight and local_hour in (0, 1):
        candidates = midnight
        rate = behavior.midnight_usage_rate
    elif campaign:
        candidates = campaign
        rate = behavior.campaign_usage_rate
    elif is_first_order and welcome:
        candidates = welcome
        rate = behavior.first_order_usage_rate
    else:
        candidates = everyday
        rate = behavior.base_usage_rate
    if not candidates or randomizer.random() >= min(1.0, rate * multiplier):
        return None
    return candidates[randomizer.randrange(len(candidates))]


def _review_content(
    randomizer: random.Random,
    rating: int,
    product_name: str,
    coupon_code: str | None,
) -> str:
    message = randomizer.choice(REVIEW_CONTENT_BY_RATING[rating])
    prefix = f"Mua {product_name}"
    if coupon_code:
        prefix += f" trong đợt dùng mã {coupon_code}"
    return f"{prefix}. {message}"


def _product_copy(category_code: str, category_sequence: int) -> tuple[str, str]:
    templates = PRODUCT_NAME_TEMPLATES[category_code]
    base_name = templates[category_sequence % len(templates)]
    collection_index = (category_sequence // len(templates)) % len(
        PRODUCT_COLLECTIONS
    )
    collection = PRODUCT_COLLECTIONS[collection_index]
    model_code = (
        f"DK-{PRODUCT_MODEL_CODES[category_code]}-{category_sequence + 1:05d}"
    )
    name = f"{base_name} - {model_code}"
    description = (
        f"{base_name} thuộc bộ sưu tập {collection} của D&K. "
        f"{PRODUCT_DESCRIPTION_BY_CATEGORY[category_code]} "
        "Size và màu sắc được quản lý theo từng phiên bản sản phẩm."
    )
    return name, description


def _pick_product_price(randomizer: random.Random, bands: Sequence[PriceBand]) -> int:
    band = bands[_weighted_index(randomizer, [band.weight for band in bands])]
    return randomizer.randrange(band.min_vnd, band.max_vnd + 1, 1000)


def _pick_category(randomizer: random.Random, categories: Sequence[tuple[str, float]]) -> str:
    return categories[_weighted_index(randomizer, [weight for _, weight in categories])][0]


def _write_header(
    stream: TextIO, config: GeneratorConfig, generation_run_id: str, demo_email: str
) -> None:
    stream.write(
        "-- TLCN deterministic MySQL dataset\n"
        f"-- generator_version: {__version__}\n"
        f"-- scenario_id: {config.scenario_id}\n"
        f"-- logical_identity: {config.logical_identity}\n"
        f"-- generation_run_id: {generation_run_id}\n"
        "-- identifier_strategy: uuid5-deterministic-v1\n"
        f"-- seed: {config.seed}\n"
        f"-- anchor_time: {config.anchor_time.isoformat()}\n"
        "-- synthetic_archive_policy: every 20th sampled product at anchor time; "
        "expired campaign/midnight coupons at ends_at.\n"
        f"-- demo_login: {demo_email} / {DEMO_PASSWORD}\n"
        "-- Prerequisite: run all Alembic migrations with alembic upgrade head.\n"
        "-- Import is fail-fast; importing the same dataset twice is rejected by unique keys.\n\n"
        "SET NAMES utf8mb4;\n"
        "SET time_zone = '+00:00';\n"
        "SET autocommit = 0;\n"
        "START TRANSACTION;\n\n"
    )


def export_sql(config: GeneratorConfig, output_path: Path) -> DatasetSummary:
    customer_count, product_count, variant_count, order_count = _validate_scale(config)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    randomizer = random.Random(config.seed)
    name_randomizer = random.Random(f"{config.seed}-names")
    address_randomizer = random.Random(f"{config.seed}-addresses")
    archive_randomizer = random.Random(f"{config.seed}-catalog-archive")
    review_randomizer = random.Random(f"{config.seed}-reviews")
    namespace = uuid.UUID(config.logical_identity)
    generation_run_id = config.generation_run_id
    demo_email = f"demo.{config.logical_identity[:8]}@web.local"
    history_end = config.anchor_time.astimezone(UTC)
    history_start = history_end - timedelta(days=max(1, config.history_months) * 30)
    distribution = config.distributions
    max_price_vnd = max(band.max_vnd for band in distribution.price_bands)
    master_created_at = history_start - timedelta(days=30)

    block = 10_000_000 + (int(config.logical_identity[:8], 16) % 10_000) * 10_000_000
    customer_base = block
    category_base = block
    product_base = block
    variant_base = block
    cart_base = block
    cart_item_base = block
    wishlist_base = block
    order_base = block
    order_item_base = block
    coupon_base = block
    redemption_base = block
    payment_base = block
    refund_base = block
    history_base = block
    review_base = block

    customer_ids = [customer_base + index + 1 for index in range(customer_count)]
    active_customer_indices: list[int] = []
    customer_names: list[str] = []
    customer_addresses: list[str] = []
    customer_rows: list[Sequence[SqlValue]] = []
    for customer_index, customer_id in enumerate(customer_ids):
        display_name = _vietnamese_name(name_randomizer)
        customer_names.append(display_name)
        customer_addresses.append(_vietnamese_address(address_randomizer))
        created_at = history_start - timedelta(days=randomizer.randrange(1, 181))
        is_active = customer_index == 0 or randomizer.random() >= 0.04
        if is_active:
            active_customer_indices.append(customer_index)
        updated_at = created_at if is_active else history_end - timedelta(days=randomizer.randrange(1, 61))
        customer_rows.append(
            (
                customer_id,
                _binary_uuid(_entity_uuid(namespace, "customer", customer_index)),
                "customer",
                display_name,
                "active" if is_active else "inactive",
                "synthetic",
                generation_run_id,
                None,
                created_at,
                updated_at,
            )
        )

    moderator_customer_id = customer_base + customer_count + 1
    customer_rows.append(
        (
            moderator_customer_id,
            _binary_uuid(_entity_uuid(namespace, "review-moderator", 0)),
            "admin",
            "Kiểm duyệt viên dữ liệu tổng hợp",
            "active",
            "synthetic",
            None,
            None,
            master_created_at,
            master_created_at,
        )
    )

    credential_rows: list[Sequence[SqlValue]] = [
        (
            customer_ids[0],
            demo_email,
            _deterministic_password_hash(config.logical_identity),
            True,
            history_start,
            history_start,
            history_start,
        )
    ]

    root_category = CategoryRecord(category_base + 1, f"syn-{config.logical_identity[:8]}", "Thời trang tổng hợp")
    category_records = [
        CategoryRecord(category_base + index + 2, f"{root_category.code}-{code}", name)
        for index, (code, name) in enumerate(LEAF_CATEGORIES)
    ]
    category_rows: list[Sequence[SqlValue]] = [
        (
            root_category.category_id,
            _binary_uuid(_entity_uuid(namespace, "category", 0)),
            None,
            root_category.code,
            root_category.name,
            True,
            master_created_at,
            master_created_at,
        )
    ]
    category_rows.extend(
        (
            category.category_id,
            _binary_uuid(_entity_uuid(namespace, "category", index + 1)),
            root_category.category_id,
            category.code,
            category.name,
            True,
            master_created_at,
            master_created_at,
        )
        for index, category in enumerate(category_records)
    )

    category_by_code = {
        category.code.removeprefix(f"{root_category.code}-"): category for category in category_records
    }
    archived_product_count = product_count // SYNTHETIC_ARCHIVED_PRODUCT_DIVISOR
    archived_product_indices = frozenset(
        archive_randomizer.sample(range(product_count), archived_product_count)
    )
    product_records: list[ProductRecord] = []
    product_rows: list[Sequence[SqlValue]] = []
    base_variants_per_product, extra_variants = divmod(variant_count, product_count)
    variant_records: list[VariantRecord] = []
    variant_rows: list[Sequence[SqlValue]] = []
    variant_index = 0
    combinations = [(size, color) for size in SIZES for color in COLORS]
    category_sequences = {code: 0 for code in CATEGORY_NAMES}
    for product_index in range(product_count):
        category_code = _pick_category(randomizer, distribution.categories)
        category = category_by_code[category_code]
        category_sequence = category_sequences[category_code]
        category_sequences[category_code] += 1
        product_name, product_description = _product_copy(
            category_code, category_sequence
        )
        product_price_vnd = _pick_product_price(randomizer, distribution.price_bands)
        product = ProductRecord(
            product_id=product_base + product_index + 1,
            public_id=_entity_uuid(namespace, "product", product_index),
            category=category,
            slug=(
                f"syn-{config.logical_identity[:8]}-{category_code}-"
                f"{category_sequence + 1:05d}"
            ),
            name=product_name,
        )
        product_records.append(product)
        is_archived = product_index in archived_product_indices
        product_rows.append(
            (
                product.product_id,
                _binary_uuid(product.public_id),
                category.category_id,
                product.slug,
                product.name,
                product_description,
                PRODUCT_IMAGE_URL,
                not is_archived,
                history_end if is_archived else None,
                moderator_customer_id if is_archived else None,
                SYNTHETIC_PRODUCT_ARCHIVE_REASON if is_archived else None,
                master_created_at,
                history_end if is_archived else master_created_at,
            )
        )
        product_variant_count = base_variants_per_product + (1 if product_index < extra_variants else 0)
        for combination_index in range(product_variant_count):
            size_code, color_code = combinations[combination_index]
            variant = VariantRecord(
                variant_id=variant_base + variant_index + 1,
                product=product,
                public_id=_entity_uuid(namespace, "variant", variant_index),
                sku=f"SYN-{config.logical_identity[:8].upper()}-{product_index + 1:05d}-{combination_index + 1:02d}",
                size_code=size_code,
                color_code=color_code,
                price_vnd=min(product_price_vnd + combination_index * 5_000, max_price_vnd),
            )
            variant_records.append(variant)
            variant_rows.append(
                (
                    variant.variant_id,
                    _binary_uuid(variant.public_id),
                    product.product_id,
                    variant.sku,
                    size_code,
                    color_code,
                    variant.price_vnd,
                    True,
                    master_created_at,
                    master_created_at,
                )
            )
            variant_index += 1

    purchased_products_by_customer: dict[int, dict[int, datetime]] = {
        customer_id: {} for customer_id in customer_ids
    }
    sold_quantities = {variant.variant_id: 0 for variant in variant_records}
    inventory_versions = {variant.variant_id: 0 for variant in variant_records}
    class_by_name = {class_.name: class_ for class_ in distribution.customer_classes}
    assignment = _class_assignment(customer_count, distribution.customer_classes, randomizer)
    business_zone = ZoneInfo(distribution.business_timezone)
    days, day_weights = _build_day_weights(
        history_start.astimezone(business_zone).date(),
        history_end.astimezone(business_zone).date(),
        distribution,
    )
    campaign_days = tuple(
        day for day in days if _sale_boost(day, distribution) > 1
    )

    coupon_records: list[CouponRecord] = [
        CouponRecord(
            coupon_id=coupon_base + 1,
            code=f"EVERYDAY{distribution.coupons.everyday_percentage}-{config.logical_identity[:4].upper()}",
            discount_type="percentage",
            discount_value=distribution.coupons.everyday_percentage,
            minimum_subtotal_vnd=distribution.coupons.everyday_minimum_subtotal_vnd,
            starts_at=history_start - timedelta(days=1),
            ends_at=history_end + timedelta(days=365),
            kind="everyday",
        ),
        CouponRecord(
            coupon_id=coupon_base + 2,
            code=f"WELCOME{distribution.coupons.welcome_fixed_vnd // 1000}K-{config.logical_identity[:4].upper()}",
            discount_type="fixed_amount",
            discount_value=distribution.coupons.welcome_fixed_vnd,
            minimum_subtotal_vnd=distribution.coupons.campaign_minimum_subtotal_vnd,
            starts_at=history_start - timedelta(days=1),
            ends_at=history_end + timedelta(days=365),
            kind="welcome",
        ),
    ]
    for campaign_index, (event, event_time) in enumerate(
        _campaign_instances(history_start, history_end, distribution)
    ):
        token = "".join(character for character in event.name.upper() if character.isalnum())[:16]
        percentage_values = distribution.coupons.campaign_percentage_values
        fixed_values = distribution.coupons.midnight_fixed_values_vnd
        campaign_code = (
            f"SALE{token}{event_time.year % 100:02d}-{config.logical_identity[:4].upper()}"
        )
        coupon_records.append(
            CouponRecord(
                coupon_id=coupon_base + len(coupon_records) + 1,
                code=campaign_code,
                discount_type="percentage",
                discount_value=percentage_values[campaign_index % len(percentage_values)],
                minimum_subtotal_vnd=distribution.coupons.campaign_minimum_subtotal_vnd,
                starts_at=event_time,
                ends_at=event_time + timedelta(days=event.after_days + 1),
                kind="campaign",
                campaign_day=event_time.date(),
            )
        )
        coupon_records.append(
            CouponRecord(
                coupon_id=coupon_base + len(coupon_records) + 1,
                code=f"0H{token}{event_time.year % 100:02d}-{config.logical_identity[:4].upper()}",
                discount_type="fixed_amount",
                discount_value=fixed_values[campaign_index % len(fixed_values)],
                minimum_subtotal_vnd=distribution.coupons.campaign_minimum_subtotal_vnd,
                starts_at=event_time,
                ends_at=event_time + timedelta(hours=2),
                kind="midnight",
                campaign_day=event_time.date(),
            )
        )

    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
        _write_header(stream, config, generation_run_id, demo_email)
        _write_batched(
            stream,
            "customers",
            (
                "customer_id",
                "public_id",
                "role",
                "display_name",
                "status",
                "data_origin",
                "generation_run_id",
                "anonymized_at",
                "created_at",
                "updated_at",
            ),
            customer_rows,
        )
        _write_batched(
            stream,
            "customer_credentials",
            (
                "customer_id",
                "email_normalized",
                "password_hash",
                "is_enabled",
                "password_changed_at",
                "created_at",
                "updated_at",
            ),
            credential_rows,
        )
        _write_batched(
            stream,
            "categories",
            ("category_id", "public_id", "parent_category_id", "code", "name", "is_active", "created_at", "updated_at"),
            category_rows,
        )
        _write_batched(
            stream,
            "products",
            (
                "product_id",
                "public_id",
                "category_id",
                "slug",
                "name",
                "description",
                "image_url",
                "is_active",
                "archived_at",
                "archived_by_customer_id",
                "archive_reason",
                "created_at",
                "updated_at",
            ),
            product_rows,
        )
        _write_batched(
            stream,
            "product_variants",
            ("variant_id", "public_id", "product_id", "sku", "size_code", "color_code", "price_vnd", "is_active", "created_at", "updated_at"),
            variant_rows,
        )
        coupon_rows: list[Sequence[SqlValue]] = []
        for coupon_index, coupon in enumerate(coupon_records):
            is_archived = (
                coupon.kind in ("campaign", "midnight")
                and coupon.ends_at <= history_end
            )
            coupon_rows.append(
                (
                    coupon.coupon_id,
                    _binary_uuid(_entity_uuid(namespace, "coupon", coupon_index)),
                    coupon.code,
                    coupon.discount_type,
                    coupon.discount_value,
                    coupon.minimum_subtotal_vnd,
                    coupon.starts_at,
                    coupon.ends_at,
                    not is_archived,
                    max(100, order_count + 100),
                    1 if coupon.kind in ("welcome", "campaign", "midnight") else 10,
                    0,
                    coupon.ends_at if is_archived else None,
                    moderator_customer_id if is_archived else None,
                    SYNTHETIC_COUPON_ARCHIVE_REASON if is_archived else None,
                    master_created_at,
                    coupon.ends_at if is_archived else master_created_at,
                )
            )
        _write_batched(
            stream,
            "coupons",
            (
                "coupon_id",
                "public_id",
                "code_normalized",
                "discount_type",
                "discount_value",
                "minimum_subtotal_vnd",
                "starts_at",
                "ends_at",
                "is_active",
                "total_usage_limit",
                "per_customer_usage_limit",
                "used_count",
                "archived_at",
                "archived_by_customer_id",
                "archive_reason",
                "created_at",
                "updated_at",
            ),
            coupon_rows,
        )
        cart_item_index = 0
        order_item_index = 0
        history_index = 0
        review_index = 0
        demo_order_target = min(24, order_count)

        cart_rows: list[Sequence[SqlValue]] = []
        cart_item_rows: list[Sequence[SqlValue]] = []
        order_rows: list[Sequence[SqlValue]] = []
        order_item_rows: list[Sequence[SqlValue]] = []
        payment_rows: list[Sequence[SqlValue]] = []
        history_rows: list[Sequence[SqlValue]] = []
        redemption_rows: list[Sequence[SqlValue]] = []
        refund_rows: list[Sequence[SqlValue]] = []
        review_rows: list[Sequence[SqlValue]] = []

        def flush_orders() -> None:
            _write_insert(stream, "carts", ("cart_id", "public_id", "customer_id", "status", "created_at", "updated_at", "checked_out_at"), cart_rows)
            _write_insert(stream, "cart_items", ("cart_item_id", "cart_id", "variant_id", "quantity", "is_present", "first_added_at", "removed_at", "updated_at"), cart_item_rows)
            _write_insert(
                stream,
                "orders",
                (
                    "order_id", "order_number", "cart_id", "customer_id", "checkout_idempotency_key", "status",
                    "currency_code", "subtotal_vnd", "shipping_fee_vnd", "total_vnd", "receiver_name",
                    "receiver_phone", "shipping_address_text", "data_origin", "generation_run_id", "created_at",
                    "updated_at", "paid_at", "completed_at", "coupon_id", "coupon_code_snapshot",
                    "coupon_type_snapshot", "coupon_value_snapshot", "discount_amount_vnd",
                    "confirmed_at", "cancelled_at",
                ),
                order_rows,
            )
            _write_insert(
                stream,
                "order_items",
                (
                    "order_item_id", "public_id", "order_id", "variant_id", "product_public_id_snapshot",
                    "category_code_snapshot", "category_name_snapshot", "product_name_snapshot", "sku_snapshot",
                    "size_code_snapshot", "color_code_snapshot", "unit_price_vnd", "quantity", "line_total_vnd", "created_at",
                ),
                order_item_rows,
            )
            _write_insert(
                stream,
                "payments",
                ("payment_id", "payment_reference", "order_id", "payment_idempotency_key", "status", "currency_code", "amount_vnd", "failure_code", "attempted_at", "created_at"),
                payment_rows,
            )
            _write_insert(
                stream,
                "order_status_history",
                ("order_status_history_id", "order_id", "from_status", "to_status", "transition_source", "reason", "transition_idempotency_key", "transitioned_at", "created_at"),
                history_rows,
            )
            _write_insert(
                stream,
                "coupon_redemptions",
                (
                    "coupon_redemption_id", "coupon_id", "order_id", "customer_id", "status",
                    "redeemed_at", "released_at", "created_at", "updated_at",
                ),
                redemption_rows,
            )
            _write_insert(
                stream,
                "refunds",
                (
                    "refund_id", "public_id", "payment_id", "refund_idempotency_key", "status",
                    "currency_code", "amount_vnd", "reason", "requested_by_customer_id",
                    "created_at", "completed_at",
                ),
                refund_rows,
            )
            _write_insert(
                stream,
                "product_reviews",
                (
                    "review_id", "public_id", "order_item_id", "customer_id", "product_id",
                    "rating", "content", "status", "moderation_reason", "moderated_by_customer_id",
                    "moderated_at", "created_at", "updated_at",
                ),
                review_rows,
            )
            cart_rows.clear()
            cart_item_rows.clear()
            order_rows.clear()
            order_item_rows.clear()
            payment_rows.clear()
            history_rows.clear()
            redemption_rows.clear()
            refund_rows.clear()
            review_rows.clear()

        targets = _order_targets(
            assignment,
            class_by_name,
            demo_order_target,
            order_count,
            randomizer,
        )
        order_index = 0
        for customer_index, order_target in enumerate(targets):
            if order_target <= 0:
                continue
            customer_id = customer_ids[customer_index]
            customer_class = assignment[customer_index]
            class_ = class_by_name[customer_class]
            if customer_index == 0:
                span_seconds = max(
                    1, int((history_end - history_start).total_seconds())
                )
                base_times = [
                    _shape_hour(
                        randomizer,
                        history_start
                        + timedelta(
                            seconds=span_seconds
                            * (position + 1)
                            // (order_target + 1)
                        ),
                        distribution,
                    )
                    for position in range(order_target)
                ]
            else:
                base_times = [
                    _pick_base_datetime(
                        randomizer,
                        history_start,
                        history_end,
                        days,
                        day_weights,
                        distribution,
                    )
                ]
                for position in range(1, order_target):
                    remaining_orders = order_target - position
                    available_days = max(0, (history_end - base_times[-1]).days)
                    interval_cap = available_days // max(1, remaining_orders)
                    interval = randomizer.randint(
                        class_.interval_min or 1,
                        class_.interval_max or 1,
                    )
                    next_base = min(
                        base_times[-1]
                        + timedelta(days=min(interval, interval_cap)),
                        history_end,
                    )
                    base_times.append(
                        min(
                            _snap_to_campaign(
                                randomizer,
                                next_base,
                                base_times[-1],
                                history_end,
                                campaign_days,
                                class_.campaign_affinity,
                                distribution,
                            ),
                            history_end,
                        )
                    )

            for customer_order_position, base_time in enumerate(base_times):
                order_time = base_time
                cart_id = cart_base + order_index + 1
                order_id = order_base + order_index + 1
                cart_created_at = order_time - timedelta(
                    minutes=randomizer.randint(5, 10_080)
                )
                item_count = 1 + _weighted_index(
                    randomizer, distribution.order_size
                )
                selected_variants = randomizer.sample(
                    variant_records, min(item_count, variant_count)
                )
                selected_variants.sort(key=lambda variant: variant.variant_id)

                item_details: list[tuple[VariantRecord, int, int]] = []
                subtotal_vnd = 0
                for variant in selected_variants:
                    quantity = 1 + _weighted_index(
                        randomizer, distribution.quantity_per_item
                    )
                    line_total_vnd = variant.price_vnd * quantity
                    subtotal_vnd += line_total_vnd
                    item_details.append((variant, quantity, line_total_vnd))

                selected_coupon = _select_coupon(
                    randomizer,
                    coupon_records,
                    order_time,
                    subtotal_vnd,
                    customer_class,
                    customer_order_position == 0,
                    distribution,
                )
                discount_amount_vnd = (
                    _coupon_discount(selected_coupon, subtotal_vnd)
                    if selected_coupon
                    else 0
                )
                shipping_fee_vnd = 0 if subtotal_vnd >= 500_000 else 30_000
                total_vnd = (
                    subtotal_vnd - discount_amount_vnd + shipping_fee_vnd
                )

                is_campaign_order = _sale_boost(
                    order_time.astimezone(business_zone).date(), distribution
                ) > 1
                cancellation = distribution.cancellations
                cancellation_rate = (
                    cancellation.campaign_rate
                    if is_campaign_order
                    else cancellation.base_rate
                )
                cancellation_rate += _mapping_value(
                    cancellation.customer_addons, customer_class
                )
                if selected_coupon is not None:
                    cancellation_rate += cancellation.coupon_addon
                order_age = history_end - order_time
                cancelled = (
                    order_age >= timedelta(hours=2)
                    and randomizer.random()
                    < max(0.0, min(1.0, cancellation_rate))
                )
                completed = (
                    not cancelled
                    and order_age >= timedelta(days=5)
                    and randomizer.random() < 0.97
                )
                confirmed = (
                    not cancelled
                    and not completed
                    and order_age >= timedelta(hours=8)
                )
                status = (
                    "cancelled"
                    if cancelled
                    else "completed"
                    if completed
                    else "confirmed"
                    if confirmed
                    else "paid"
                )
                cancellation_reason = (
                    _weighted_pair(randomizer, cancellation.reasons)
                    if cancelled
                    else None
                )
                paid_at = order_time
                confirmed_at = None
                completed_at = None
                cancelled_at = None
                if completed or confirmed:
                    confirmed_at = min(
                        history_end - timedelta(minutes=2),
                        order_time
                        + timedelta(hours=randomizer.randint(2, 18)),
                    )
                if completed and confirmed_at is not None:
                    completed_at = min(
                        history_end - timedelta(minutes=1),
                        confirmed_at
                        + timedelta(hours=randomizer.randint(24, 96)),
                    )
                if cancelled:
                    cancelled_at = min(
                        history_end - timedelta(minutes=1),
                        order_time
                        + timedelta(minutes=randomizer.randint(15, 480)),
                    )
                updated_at = (
                    cancelled_at or completed_at or confirmed_at or order_time
                )
                checkout_key = _identifier_uuid(
                    namespace, "checkout-idempotency", order_index
                )

                cart_rows.append(
                    (
                        cart_id,
                        _binary_uuid(_entity_uuid(namespace, "cart", order_index)),
                        customer_id,
                        "checked_out",
                        cart_created_at,
                        order_time,
                        order_time,
                    )
                )
                for variant, quantity, line_total_vnd in item_details:
                    cart_item_index += 1
                    cart_item_rows.append(
                        (
                            cart_item_base + cart_item_index,
                            cart_id,
                            variant.variant_id,
                            quantity,
                            True,
                            cart_created_at,
                            None,
                            order_time,
                        )
                    )
                    order_item_index += 1
                    order_item_rows.append(
                        (
                            order_item_base + order_item_index,
                            _binary_uuid(
                                _entity_uuid(
                                    namespace,
                                    "order-item",
                                    order_item_index,
                                )
                            ),
                            order_id,
                            variant.variant_id,
                            _binary_uuid(variant.product.public_id),
                            variant.product.category.code,
                            variant.product.category.name,
                            variant.product.name,
                            variant.sku,
                            variant.size_code,
                            variant.color_code,
                            variant.price_vnd,
                            quantity,
                            line_total_vnd,
                            order_time,
                        )
                    )
                    if not cancelled:
                        sold_quantities[variant.variant_id] += quantity
                        inventory_versions[variant.variant_id] += 1
                        first_purchase = purchased_products_by_customer[customer_id].get(
                            variant.product.product_id
                        )
                        if first_purchase is None or order_time < first_purchase:
                            purchased_products_by_customer[customer_id][
                                variant.product.product_id
                            ] = order_time
                    else:
                        inventory_versions[variant.variant_id] += 2

                    review_rate = _mapping_value(
                        distribution.reviews.completed_order_rates,
                        customer_class,
                    )
                    if completed and review_randomizer.random() < review_rate:
                        review_time = (completed_at or order_time) + timedelta(
                            days=review_randomizer.randint(
                                distribution.reviews.delay_days_min,
                                distribution.reviews.delay_days_max,
                            ),
                            hours=review_randomizer.randint(0, 23),
                        )
                        if review_time <= history_end:
                            review_index += 1
                            rating = 1 + _weighted_index(
                                review_randomizer,
                                distribution.reviews.rating_weights,
                            )
                            review_status = _weighted_pair(
                                review_randomizer,
                                distribution.reviews.status_weights,
                            )
                            moderated_at = None
                            moderated_by_customer_id = None
                            moderation_reason = None
                            if review_status == "rejected":
                                moderated_at = min(
                                    history_end,
                                    review_time
                                    + timedelta(
                                        hours=review_randomizer.randint(1, 48)
                                    ),
                                )
                                moderated_by_customer_id = (
                                    moderator_customer_id
                                )
                                moderation_reason = review_randomizer.choice(
                                    REVIEW_REJECTION_REASONS
                                )
                            review_rows.append(
                                (
                                    review_base + review_index,
                                    _binary_uuid(
                                        _entity_uuid(
                                            namespace,
                                            "review",
                                            review_index,
                                        )
                                    ),
                                    order_item_base + order_item_index,
                                    customer_id,
                                    variant.product.product_id,
                                    rating,
                                    _review_content(
                                        review_randomizer,
                                        rating,
                                        variant.product.name,
                                        (
                                            selected_coupon.code
                                            if selected_coupon
                                            else None
                                        ),
                                    ),
                                    review_status,
                                    moderation_reason,
                                    moderated_by_customer_id,
                                    moderated_at,
                                    review_time,
                                    moderated_at or review_time,
                                )
                            )

                order_rows.append(
                    (
                        order_id,
                        f"SYN{config.logical_identity[:8].upper()}{order_index + 1:08d}",
                        cart_id,
                        customer_id,
                        checkout_key,
                        status,
                        "VND",
                        subtotal_vnd,
                        shipping_fee_vnd,
                        total_vnd,
                        customer_names[customer_index],
                        f"09{(customer_index + 1) % 100_000_000:08d}",
                        customer_addresses[customer_index],
                        "synthetic",
                        generation_run_id,
                        order_time,
                        updated_at,
                        paid_at,
                        completed_at,
                        selected_coupon.coupon_id if selected_coupon else None,
                        selected_coupon.code if selected_coupon else None,
                        (
                            selected_coupon.discount_type
                            if selected_coupon
                            else None
                        ),
                        (
                            selected_coupon.discount_value
                            if selected_coupon
                            else None
                        ),
                        discount_amount_vnd,
                        confirmed_at,
                        cancelled_at,
                    )
                )
                payment_rows.append(
                    (
                        payment_base + order_index + 1,
                        _identifier_uuid(
                            namespace, "payment-reference", order_index
                        ),
                        order_id,
                        _identifier_uuid(
                            namespace, "payment-idempotency", order_index
                        ),
                        "succeeded",
                        "VND",
                        total_vnd,
                        None,
                        order_time,
                        order_time,
                    )
                )
                history_index += 1
                history_rows.append(
                    (
                        history_base + history_index,
                        order_id,
                        None,
                        "paid",
                        "generator",
                        None,
                        _identifier_uuid(
                            namespace, "order-transition-paid", order_index
                        ),
                        order_time,
                        order_time,
                    )
                )
                if confirmed_at is not None:
                    history_index += 1
                    history_rows.append(
                        (
                            history_base + history_index,
                            order_id,
                            "paid",
                            "confirmed",
                            "generator",
                            None,
                            _identifier_uuid(
                                namespace, "order-transition-confirmed", order_index
                            ),
                            confirmed_at,
                            confirmed_at,
                        )
                    )
                if completed and completed_at is not None:
                    history_index += 1
                    history_rows.append(
                        (
                            history_base + history_index,
                            order_id,
                            "confirmed",
                            "completed",
                            "generator",
                            None,
                            _identifier_uuid(
                                namespace, "order-transition-completed", order_index
                            ),
                            completed_at,
                            completed_at,
                        )
                    )
                if cancelled and cancelled_at is not None:
                    history_index += 1
                    history_rows.append(
                        (
                            history_base + history_index,
                            order_id,
                            "paid",
                            "cancelled",
                            "generator",
                            cancellation_reason,
                            _identifier_uuid(
                                namespace, "order-transition-cancelled", order_index
                            ),
                            cancelled_at,
                            cancelled_at,
                        )
                    )
                    refund_rows.append(
                        (
                            refund_base + order_index + 1,
                            _binary_uuid(
                                _entity_uuid(
                                    namespace,
                                    "refund",
                                    order_index,
                                )
                            ),
                            payment_base + order_index + 1,
                            _identifier_uuid(
                                namespace, "refund-idempotency", order_index
                            ),
                            "succeeded",
                            "VND",
                            total_vnd,
                            cancellation_reason,
                            customer_id,
                            cancelled_at,
                            cancelled_at,
                        )
                    )
                if selected_coupon is not None:
                    redemption_rows.append(
                        (
                            redemption_base + order_index + 1,
                            selected_coupon.coupon_id,
                            order_id,
                            customer_id,
                            "released" if cancelled else "redeemed",
                            order_time,
                            cancelled_at if cancelled else None,
                            order_time,
                            cancelled_at or order_time,
                        )
                    )

                order_index += 1
                if len(order_rows) >= INSERT_BATCH_SIZE:
                    flush_orders()

        flush_orders()
        for coupon in coupon_records:
            stream.write(
                "UPDATE `coupons` SET `used_count` = "
                "(SELECT COUNT(*) FROM `coupon_redemptions` "
                f"WHERE `coupon_id` = {coupon.coupon_id} "
                "AND `status` = 'redeemed'), "
                f"`updated_at` = {_sql_literal(history_end)} "
                f"WHERE `coupon_id` = {coupon.coupon_id};\n"
            )
        stream.write("\n")

        wishlist_rows: list[Sequence[SqlValue]] = []
        wishlist_index = 0
        product_by_id = {product.product_id: product for product in product_records}
        for customer_id in customer_ids:
            if randomizer.random() >= 0.55:
                continue
            wishlist_count = randomizer.randint(1, min(5, product_count))
            purchased = purchased_products_by_customer[customer_id]
            converted_count = min(
                len(purchased),
                max(1, round(wishlist_count * 0.4)) if purchased else 0,
            )
            converted_ids = (
                randomizer.sample(sorted(purchased), converted_count)
                if converted_count
                else []
            )
            remaining_candidates = [
                product.product_id
                for product in product_records
                if product.product_id not in converted_ids
            ]
            other_ids = randomizer.sample(
                remaining_candidates,
                wishlist_count - converted_count,
            )
            for product_id in converted_ids + other_ids:
                converted_at = purchased.get(product_id)
                if converted_at is not None:
                    first_added_at = max(
                        history_start,
                        converted_at
                        - timedelta(
                            days=randomizer.randint(1, 30),
                            hours=randomizer.randint(0, 23),
                        ),
                    )
                    last_added_at = min(
                        converted_at,
                        first_added_at + timedelta(days=randomizer.randint(0, 7)),
                    )
                    is_present = False
                    removed_at = converted_at
                else:
                    first_added_at = _timestamp_between(
                        randomizer, history_start, history_end
                    )
                    last_added_at = min(
                        history_end,
                        first_added_at
                        + timedelta(days=randomizer.randrange(0, 30)),
                    )
                    is_present = randomizer.random() >= 0.18
                    removed_at = (
                        None
                        if is_present
                        else min(
                            history_end,
                            last_added_at
                            + timedelta(days=randomizer.randrange(0, 15)),
                        )
                    )
                wishlist_rows.append(
                    (
                        wishlist_base + wishlist_index + 1,
                        customer_id,
                        product_by_id[product_id].product_id,
                        is_present,
                        first_added_at,
                        last_added_at,
                        removed_at,
                        removed_at or last_added_at,
                    )
                )
                wishlist_index += 1
        _write_batched(
            stream,
            "wishlist_items",
            (
                "wishlist_item_id",
                "customer_id",
                "product_id",
                "is_present",
                "first_added_at",
                "last_added_at",
                "removed_at",
                "updated_at",
            ),
            wishlist_rows,
        )

        active_cart_rows: list[Sequence[SqlValue]] = []
        active_cart_item_rows: list[Sequence[SqlValue]] = []
        active_cart_count = max(1, len(active_customer_indices) * 3 // 10)
        selected_active_customers = randomizer.sample(active_customer_indices, min(active_cart_count, len(active_customer_indices)))
        for active_cart_index, customer_index in enumerate(selected_active_customers):
            cart_id = cart_base + order_count + active_cart_index + 1
            is_abandoned = randomizer.random() < 0.65
            updated_at = history_end - (
                timedelta(days=randomizer.randint(2, 20))
                if is_abandoned
                else timedelta(hours=randomizer.randint(1, 12))
            )
            created_at = updated_at - timedelta(hours=randomizer.randint(1, 72))
            active_cart_rows.append(
                (
                    cart_id,
                    _binary_uuid(_entity_uuid(namespace, "active-cart", active_cart_index)),
                    customer_ids[customer_index],
                    "active",
                    created_at,
                    updated_at,
                    None,
                )
            )
            selected_variants = randomizer.sample(variant_records, randomizer.randint(1, min(3, variant_count)))
            for variant in sorted(selected_variants, key=lambda value: value.variant_id):
                cart_item_index += 1
                active_cart_item_rows.append(
                    (
                        cart_item_base + cart_item_index,
                        cart_id,
                        variant.variant_id,
                        randomizer.randint(1, 3),
                        True,
                        created_at,
                        None,
                        updated_at,
                    )
                )
        _write_batched(stream, "carts", ("cart_id", "public_id", "customer_id", "status", "created_at", "updated_at", "checked_out_at"), active_cart_rows)
        _write_batched(stream, "cart_items", ("cart_item_id", "cart_id", "variant_id", "quantity", "is_present", "first_added_at", "removed_at", "updated_at"), active_cart_item_rows)

        inventory_rows: list[Sequence[SqlValue]] = []
        for variant in variant_records:
            sold_quantity = sold_quantities[variant.variant_id]
            buffer_quantity = 80 + randomizer.randrange(0, 121)
            opening_on_hand = sold_quantity + buffer_quantity
            inventory_rows.append(
                (
                    variant.variant_id,
                    opening_on_hand,
                    opening_on_hand - sold_quantity,
                    inventory_versions[variant.variant_id],
                    history_end,
                )
            )
        _write_batched(
            stream,
            "inventory",
            ("variant_id", "opening_on_hand", "on_hand", "version", "updated_at"),
            inventory_rows,
        )

        stream.write(
            "COMMIT;\n\n"
            "-- Verification summary for the imported generation run.\n"
            f"SELECT '{generation_run_id}' AS generation_run_id,\n"
            f"       (SELECT COUNT(*) FROM customers WHERE generation_run_id = '{generation_run_id}') AS customers,\n"
            f"       (SELECT COUNT(*) FROM orders WHERE generation_run_id = '{generation_run_id}') AS orders;\n"
        )

    temporary_path.replace(output_path)

    return DatasetSummary(
        sql_path=output_path,
        generation_run_id=generation_run_id,
        demo_email=demo_email,
        demo_password=DEMO_PASSWORD,
        customers=customer_count,
        products=product_count,
        variants=variant_count,
        orders=order_count,
    )
