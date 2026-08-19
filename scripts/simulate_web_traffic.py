#!/usr/bin/env python3
"""Simulate natural real-time web traffic against the ecommerce API.

Spawns concurrent virtual user sessions that navigate the storefront, search,
filter, manage carts and wishlists, and complete orders with realistic pacing.

Usage:
    uv run --package data-generator -- python scripts/simulate_web_traffic.py \
        --concurrency 5 --duration 300 --error-rate 0.05
"""
from __future__ import annotations

import argparse
import json
import random
import signal
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx
from faker import Faker

PASSWORD = "SimPass!123"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
]

# Synchronized with MySQL & Generator catalog constants
SIZES = ["XS", "S", "M", "L", "XL"]
COLORS = ["BLACK", "WHITE", "RED", "GREEN", "BLUE", "YELLOW", "PINK", "PURPLE", "ORANGE", "BROWN", "GRAY", "BEIGE"]
SEARCH_TERMS = [
    "áo sơ mi nữ",
    "đầm dự tiệc",
    "chân váy midi",
    "quần jeans ống rộng",
    "áo khoác nữ",
    "túi xách nữ",
    "giày nữ",
    "phụ kiện nữ",
    "đầm linen",
    "áo công sở",
]
CITIES = ["TP.HCM", "Hà Nội", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Huế", "Nha Trang", "Đà Lạt"]


@dataclass
class SimUser:
    email: str
    display_name: str

    def to_row(self) -> str:
        return f"{self.email}\t{self.display_name}"


class UserPool:
    """Persistent pool of simulated customers stored in scripts/.sim_users.tsv."""

    def __init__(self, path: Path, base_url: str) -> None:
        self.path = path
        self.base_url = base_url
        self._lock = threading.Lock()
        self.users: list[SimUser] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                self.users.append(SimUser(parts[0], parts[1]))

    def save(self) -> None:
        with self._lock:
            self.path.write_text("\n".join(u.to_row() for u in self.users) + "\n")

    def seed(self, count: int, fake: Faker, client: httpx.Client) -> None:
        for _ in range(count):
            email = fake.unique.email()
            data = {"email": email, "password": PASSWORD, "display_name": fake.name()}
            response = client.post(f"{self.base_url}/api/v1/auth/register", json=data)
            if response.status_code in (200, 201):
                with self._lock:
                    self.users.append(SimUser(email, data["display_name"]))
                self.save()
        fake.unique.clear()

    def pick(self) -> SimUser:
        if not self.users:
            raise RuntimeError("User pool is empty; seeding failed")
        return random.choice(self.users)


class Stats:
    """Thread-safe request metrics accumulator."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total = 0
        self.by_status: dict[str, int] = {}
        self.by_route: dict[str, int] = {}
        self.start_time = time.monotonic()

    def record(self, status: int, route: str) -> None:
        with self._lock:
            self.total += 1
            self.by_status[str(status)] = self.by_status.get(str(status), 0) + 1
            self.by_route[route] = self.by_route.get(route, 0) + 1

    def summary(self) -> str:
        elapsed = max(0.1, time.monotonic() - self.start_time)
        rps = self.total / elapsed
        lines = [
            "\n" + "=" * 50,
            f"==> Traffic Simulation Summary ({elapsed:.1f}s, {rps:.2f} req/s)",
            f"==> Total requests: {self.total}",
            "=" * 50,
            "--- By severity ---",
        ]
        severity = {"INFO (2xx/3xx)": 0, "WARN (4xx)": 0, "ERROR (5xx)": 0}
        for code, count in self.by_status.items():
            if code == "0" or code.startswith("5"):
                severity["ERROR (5xx)"] += count
            elif code.startswith("4"):
                severity["WARN (4xx)"] += count
            else:
                severity["INFO (2xx/3xx)"] += count
        lines += [f"  {k}: {v}" for k, v in severity.items()]
        lines.append("--- By status code ---")
        lines += [f"  {k}: {v}" for k, v in sorted(self.by_status.items(), key=lambda x: int(x[0]))]
        lines.append("--- By route ---")
        lines += [f"  {k:30s}: {v}" for k, v in sorted(self.by_route.items())]
        lines.append("=" * 50)
        return "\n".join(lines)


class Session:
    """One simulated visitor session: natural sequence of HTTP requests."""

    def __init__(
        self,
        client: httpx.Client,
        stats: Stats,
        user: SimUser,
        base_url: str,
        fake: Faker,
        error_rate: float,
        internal_secret: str,
    ) -> None:
        self.client = client
        self.stats = stats
        self.user = user
        self.base_url = base_url
        self.fake = fake
        self.error_rate = error_rate
        self.internal_secret = internal_secret
        self.prefix = "/api/v1"
        self._csrf: str | None = None

    def _vietnam_mobile(self) -> str:
        return "09" + "".join(random.choices("0123456789", k=8))

    def _user_agent(self) -> str:
        return self.fake.user_agent() if random.random() < 0.5 else random.choice(USER_AGENTS)

    def _request(
        self,
        method: str,
        path: str,
        route: str,
        *,
        json_body: dict | None = None,
        idem: str | None = None,
        internal: bool = False,
    ) -> httpx.Response:
        headers = {
            "User-Agent": self._user_agent(),
            "Accept": "application/json",
        }
        if internal:
            headers["X-Internal-Secret"] = self.internal_secret
        prefix = "/internal/v1" if internal else self.prefix
        request = self.client.build_request(method, f"{self.base_url}{prefix}{path}", headers=headers, json=json_body)
        if self._csrf:
            request.headers["X-CSRF-Token"] = self._csrf
        if idem:
            request.headers["Idempotency-Key"] = idem
        try:
            response = self.client.send(request)
        except httpx.HTTPError:
            self.stats.record(0, route)
            return httpx.Response(0, request=request)
        self._csrf = self.client.cookies.get("web_csrf")
        self.stats.record(response.status_code, route)
        return response

    def _get(self, path: str, route: str) -> httpx.Response:
        return self._request("GET", path, route)

    def _json(self, response: httpx.Response) -> dict:
        try:
            return response.json()
        except json.JSONDecodeError:
            return {}

    def _sleep(self, lo: float = 0.3, hi: float = 1.2) -> None:
        time.sleep(random.uniform(lo, hi))

    def _product_listing(self, path: str, route: str) -> list[str]:
        response = self._json(self._get(path, route))
        return [item["slug"] for item in response.get("items", [])]

    def _product_public_ids(self) -> list[str]:
        response = self._json(self._get("/products", "product_list"))
        return [item["public_id"] for item in response.get("items", [])]

    def browse(self) -> str | None:
        self._get("/catalog/facets", "facets")
        self._sleep()
        self._get("/categories", "categories")
        self._sleep()

        slugs = self._product_listing("/products", "product_list")
        if slugs:
            self._sleep()
            slug = random.choice(slugs[:8])
            detail = self._json(self._get(f"/products/{slug}", "product_detail"))
            self._sleep(0.4, 1.5)
            if detail.get("variants"):
                return random.choice(detail["variants"])["public_id"]
        return None

    def search(self) -> None:
        term = random.choice(SEARCH_TERMS)
        if random.random() < 0.10:
            term = self._typo(term)
        self._get(f"/products?q={term}", "product_search")
        self._sleep()
        if random.random() < 0.4:
            self._get(f"/products?q={term}&sort=price_asc", "product_search_sorted")

    @staticmethod
    def _typo(term: str) -> str:
        if len(term) < 2:
            return term
        pos = random.randrange(len(term))
        return term[:pos] + term[pos + 1 :]

    def filtered_listing(self) -> None:
        size = random.choice(SIZES)
        color = random.choice(COLORS)
        self._get(f"/products?size={size}&color={color}&sort=newest", "product_list_filtered")

    def abandon_cart(self) -> None:
        variant = self.browse()
        if not variant:
            return
        self._request("PUT", f"/cart/items/{variant}", "cart_add", json_body={"quantity": random.randint(1, 2)})
        self._sleep()
        self._request("GET", "/cart", "cart_view")

    def wishlist(self) -> None:
        public_ids = self._product_public_ids()
        if not public_ids:
            return
        public_id = random.choice(public_ids)
        self._sleep(0.2, 0.8)
        if random.random() < 0.5:
            self._request("PUT", f"/wishlist/products/{public_id}", "wishlist_add", json_body={})
        self._request("GET", "/wishlist", "wishlist_read")
        self._sleep(0.2, 0.8)
        if random.random() < 0.3:
            self._request("DELETE", f"/wishlist/products/{public_id}", "wishlist_remove")

    def coupon_glance(self) -> None:
        self._request("GET", "/coupons/available", "coupon_available")

    def coupon_abandon(self) -> None:
        variant = self.browse()
        if not variant:
            return
        self._request("PUT", f"/cart/items/{variant}", "cart_add", json_body={"quantity": 1})
        self._sleep()
        code = "EXPIRED-" + self.fake.word().upper()[:8]
        self._request("POST", "/checkout/quote", "checkout_quote_invalid", json_body={"coupon_code": code})

    def dead_link(self) -> None:
        bogus = f"san-pham-khong-ton-tai-{uuid.uuid4().hex[:6]}"
        self._get(f"/products/{bogus}", "product_dead_link")

    def failed_login(self) -> None:
        self._request(
            "POST",
            "/auth/login",
            "auth_login_failed",
            json_body={"email": self.user.email, "password": self.fake.password()},
        )

    def purchase(self) -> None:
        if random.random() < self.error_rate:
            self.coupon_abandon()
            return
        variant = self.browse()
        if not variant:
            return
        self._request("PUT", f"/cart/items/{variant}", "cart_add", json_body={"quantity": random.randint(1, 2)})
        self._sleep(0.4, 1.2)
        self._request("POST", "/checkout/quote", "checkout_quote", json_body={})
        self._sleep(0.4, 1.2)

        body = {
            "receiver_name": self.fake.name(),
            "receiver_phone": self._vietnam_mobile(),
            "shipping_address_text": f"{self.fake.street_address()}, {random.choice(CITIES)}",
        }
        idem = str(uuid.uuid4())
        response = self._request("POST", "/checkout", "checkout_submit", json_body=body, idem=idem)
        if response.status_code not in (200, 201):
            return
        order = self._json(response).get("order_number")
        if not order:
            return
        self._sleep(0.4, 1.0)
        self._get(f"/orders/{order}", "order_detail")
        if random.random() < 0.7:
            self.complete_and_review(order)

    def complete_and_review(self, order_number: str) -> None:
        idem = str(uuid.uuid4())
        self._request("POST", f"/orders/{order_number}/confirm", "order_confirm", idem=idem, internal=True)
        self._sleep(0.3, 0.8)
        self._request("POST", f"/orders/{order_number}/complete", "order_complete", idem=str(uuid.uuid4()))
        self._sleep(0.4, 1.0)
        detail = self._json(self._get(f"/orders/{order_number}", "order_detail"))
        items = detail.get("items", [])
        if not items:
            return
        item = random.choice(items)
        rating = random.choice([5, 5, 4, 4, 3, 2, 1])
        content = "Sản phẩm đẹp, chất vải tốt, giao hàng nhanh!" if rating >= 4 else "Chất lượng bình thường."
        self._request(
            "POST",
            f"/orders/{order_number}/items/{item['public_id']}/review",
            "review_write",
            json_body={"rating": rating, "content": content},
        )

    def random_mistake(self) -> None:
        if random.random() < 0.4:
            self.failed_login()
        elif random.random() < 0.5:
            self.dead_link()
        else:
            self.coupon_glance()

    def run(self) -> None:
        steps = random.randint(2, 5)
        for i in range(steps):
            if random.random() < self.error_rate:
                self.random_mistake()
                self._sleep()
                continue
            roll = random.random()
            if i == steps - 1 and roll < 0.35:
                self.purchase()
            elif roll < 0.15:
                self.abandon_cart()
            elif roll < 0.28:
                self.wishlist()
            elif roll < 0.38:
                self.coupon_glance()
            elif roll < 0.58:
                self.search()
            elif roll < 0.75:
                self.filtered_listing()
            else:
                self.browse()
            self._sleep()


class Simulator:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.stats = Stats()
        self.fake = Faker("vi_VN")
        self.stop = threading.Event()
        self._lock = threading.Lock()
        self._active: dict[threading.Thread, SimUser] = {}

    def _spawn(self, pool: UserPool) -> None:
        with self._lock:
            client = httpx.Client(timeout=15.0, follow_redirects=True)
            user = pool.pick()
        session = Session(
            client,
            self.stats,
            user,
            self.args.base_url,
            self.fake,
            self.args.error_rate,
            self.args.internal_secret,
        )
        thread = threading.Thread(target=self._run_session, args=(session,), daemon=True)
        with self._lock:
            self._active[thread] = user
        thread.start()

    def _run_session(self, session: Session) -> None:
        try:
            response = session._request(
                "POST",
                "/auth/login",
                "auth_login",
                json_body={"email": session.user.email, "password": PASSWORD},
            )
            if response.status_code not in (200, 201):
                session._request(
                    "POST",
                    "/auth/register",
                    "auth_register",
                    json_body={
                        "email": session.user.email,
                        "password": PASSWORD,
                        "display_name": session.user.display_name,
                    },
                )
            session.run()
        finally:
            with self._lock:
                self._active.pop(threading.current_thread(), None)

    def run(self, pool: UserPool) -> None:
        started = time.monotonic()
        deadline = started + self.args.duration
        print(f"==> Simulating real-time web traffic to {self.args.base_url}")
        print(f"==> Duration: {self.args.duration}s | Concurrency: {self.args.concurrency} | Error rate: {self.args.error_rate:.1%}")
        print("==> Press Ctrl+C to stop early.\n")

        while not self.stop.is_set():
            now = time.monotonic()
            if now >= deadline:
                break
            with self._lock:
                current = len(self._active)
            for _ in range(max(0, self.args.concurrency - current)):
                self._spawn(pool)
            time.sleep(0.5)

        self.stop.set()
        with self._lock:
            for thread in list(self._active):
                thread.join(timeout=0.5)
        print(self.stats.summary())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate natural real-time web traffic against the ecommerce API.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="FastAPI base URL")
    parser.add_argument("--duration", type=int, default=300, help="Total run duration in seconds (default: 300)")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent virtual users (default: 5)")
    parser.add_argument("--seed-users", type=int, default=20, help="Initial user pool size (default: 20)")
    parser.add_argument("--error-rate", type=float, default=0.05, help="Rate of natural user errors (default: 0.05)")
    parser.add_argument("--pool-file", type=Path, default=Path(__file__).parent / ".sim_users.tsv", help="Path to user pool cache")
    parser.add_argument("--internal-secret", default="change-me-internal-secret", help="X-Internal-Secret for order fulfillment")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    simulator = Simulator(args)
    signal.signal(signal.SIGINT, lambda *_: simulator.stop.set())

    client = httpx.Client(timeout=15.0)
    try:
        pool = UserPool(args.pool_file, args.base_url)
        if len(pool.users) < args.seed_users:
            print(f"==> Initializing user pool with {args.seed_users - len(pool.users)} virtual users...")
            pool.seed(args.seed_users - len(pool.users), simulator.fake, client)
        if not pool.users:
            raise RuntimeError("No users in pool; seeding failed")
        simulator.run(pool)
    finally:
        client.close()


if __name__ == "__main__":
    main()