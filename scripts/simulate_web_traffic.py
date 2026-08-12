#!/usr/bin/env python3
"""Simulate natural web traffic against the ecommerce API with time compression.

Runs for --real-seconds of wall-clock time while behaving as if the web ran for
--simulated-days. Concurrency follows an hourly intensity curve (quiet nights,
evening peaks) and weekday uplift; returning customers from the persistent user
pool (scripts/.sim_users.tsv) buy more often than new visitors.

Usage:
    uv run --package data-generator -- python scripts/simulate_web_traffic.py \
        --real-seconds 600 --simulated-days 7 --concurrency 8
"""
from __future__ import annotations

import argparse
import json
import random
import signal
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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

# Relative hourly traffic intensity: index 0 = 00:00, 23 = 23:00.
HOURLY_INTENSITY = [
    0.05, 0.04, 0.03, 0.03, 0.04, 0.08,  # 00-05 quiet night
    0.20, 0.35, 0.55,                    # 06-08 morning ramp
    0.70, 0.72, 0.75,                    # 09-11 morning peak
    0.85, 0.90,                          # 12-13 lunch
    0.75, 0.70, 0.65, 0.60,              # 14-17 afternoon decay
    0.75, 0.95,                          # 18-19 evening ramp
    1.00, 0.95, 0.85,                    # 20-22 evening peak
    0.30,                                 # 23 wind-down
]
WEEKDAY_UPLIFT = [1.0, 1.0, 1.0, 1.0, 1.0, 1.3, 1.35]  # Sat/Sun busier
SEARCH_TERMS = ["ao", "quan", "linen", "jean", "kaki", "non", "thun", "dam", "that lung", "short"]
SIZES = ["29", "30", "31", "32", "F", "L"]
COLORS = ["beige", "black", "blue", "brown", "gray", "navy", "white"]
CITIES = ["TP.HCM", "Hà Nội", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Huế", "Nha Trang", "Đà Lạt"]


class SimulatedClock:
    """Maps wall-clock time to a compressed simulated timeline."""

    def __init__(self, real_seconds: int, simulated_days: int) -> None:
        self._real_start = time.monotonic()
        self._sim_span = timedelta(days=simulated_days)
        self._real_span = timedelta(seconds=real_seconds)
        self._sim_start = datetime.now(timezone.utc) - self._sim_span

    def now(self) -> datetime:
        elapsed = timedelta(seconds=time.monotonic() - self._real_start)
        ratio = self._sim_span.total_seconds() / self._real_span.total_seconds()
        return self._sim_start + elapsed * ratio

    def intensity(self) -> float:
        sim = self.now()
        day_frac = (sim.hour * 3600 + sim.minute * 60 + sim.second) / 86400.0
        base = HOURLY_INTENSITY[min(int(day_frac * 24), 23)]
        return base * WEEKDAY_UPLIFT[sim.weekday()]


@dataclass
class SimUser:
    email: str
    display_name: str
    created_day: float  # simulated day number when first seen

    def to_row(self) -> str:
        return f"{self.email}\t{self.display_name}\t{self.created_day:.1f}"


class UserPool:
    """Persistent pool of simulated customers, stored in scripts/.sim_users.tsv."""

    def __init__(self, path: Path, clock: SimulatedClock, base_url: str) -> None:
        self.path = path
        self.clock = clock
        self.base_url = base_url
        self._lock = threading.Lock()
        self.users: list[SimUser] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                self.users.append(SimUser(parts[0], parts[1], float(parts[2])))

    def save(self) -> None:
        with self._lock:
            self.path.write_text("\n".join(u.to_row() for u in self.users) + "\n")

    def seed(self, count: int, fake: Faker, client: httpx.Client) -> None:
        day = self.clock.now()
        for _ in range(count):
            email = fake.unique.email()
            data = {"email": email, "password": PASSWORD, "display_name": fake.name()}
            response = client.post(f"{self.base_url}/api/v1/auth/register", json=data)
            if response.status_code in (200, 201):
                with self._lock:
                    self.users.append(SimUser(email, data["display_name"], day.timestamp()))
                self.save()
        fake.unique.clear()

    def pick(self, for_purchase: bool) -> SimUser:
        if not self.users:
            raise RuntimeError("User pool is empty; seeding failed")
        now = self.clock.now().timestamp()
        # Returning customers (created days ago) are preferred for purchase sessions;
        # casual browsing picks uniformly across the pool.
        if for_purchase:
            mature = [u for u in self.users if now - u.created_day > 3600 * 24 * 2]
            if mature:
                return random.choice(mature)
        return random.choice(self.users)


class Stats:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total = 0
        self.by_status: dict[str, int] = {}
        self.by_route: dict[str, int] = {}

    def record(self, status: int, route: str) -> None:
        with self._lock:
            self.total += 1
            self.by_status[str(status)] = self.by_status.get(str(status), 0) + 1
            self.by_route[route] = self.by_route.get(route, 0) + 1

    def summary(self) -> str:
        lines = [f"==> Total requests: {self.total}"]
        lines.append("--- By severity ---")
        severity = {"INFO": 0, "WARN": 0, "ERROR": 0}
        for code, count in self.by_status.items():
            if code == "0":
                severity["ERROR"] += count
            elif code.startswith("4"):
                severity["WARN"] += count
            else:
                severity["INFO"] += count
        lines += [f"  {k}: {v}" for k, v in severity.items()]
        lines.append("--- By status code ---")
        lines += [f"  {k}: {v}" for k, v in sorted(self.by_status.items(), key=lambda x: int(x[0]))]
        lines.append("--- By route ---")
        lines += [f"  {k}: {v}" for k, v in sorted(self.by_route.items())]
        return "\n".join(lines)


class Session:
    """One simulated visitor: a sequence of HTTP requests with natural pacing.

    Behaviors mirror real users: browse, search (with typos), filter, wishlist,
    coupons, cart abandonment, full purchase lifecycle + review. A small
    ``--error-rate`` of requests intentionally fails the way real users do
    (dead links, wrong passwords, expired coupons, premature reviews) so the
    access-log severity mix in the lakehouse looks real.
    """

    def __init__(
        self,
        client: httpx.Client,
        stats: Stats,
        user: SimUser,
        base_url: str,
        fake: Faker,
        clock: SimulatedClock,
        error_rate: float,
        internal_secret: str,
    ) -> None:
        self.client = client
        self.stats = stats
        self.user = user
        self.base_url = base_url
        self.fake = fake
        self.clock = clock
        self.error_rate = error_rate
        self.internal_secret = internal_secret
        self.prefix = "/api/v1"
        self._csrf: str | None = None

    def _vietnam_mobile(self) -> str:
        return "09" + "".join(random.choices("0123456789", k=8))

    def _user_agent(self) -> str:
        return self.fake.user_agent() if random.random() < 0.5 else random.choice(USER_AGENTS)

    def _request(self, method: str, path: str, route: str, *, json_body: dict | None = None, idem: str | None = None, internal: bool = False) -> httpx.Response:
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

    def _sleep(self, lo: float = 0.4, hi: float = 1.6) -> None:
        time.sleep(random.uniform(lo, hi))

    def _product_listing(self, path: str, route: str) -> list[str]:
        """Fetch product slugs from a listing endpoint."""
        response = self._json(self._get(path, route))
        return [item["slug"] for item in response.get("items", [])]

    def _product_public_ids(self) -> list[str]:
        response = self._json(self._get("/products", "product_list"))
        return [item["public_id"] for item in response.get("items", [])]

    def browse(self) -> None:
        self._get("/catalog/facets", "facets")
        self._sleep()
        self._get("/categories", "categories")
        self._sleep()

        slugs = self._product_listing("/products", "product_list")
        if slugs:
            self._sleep()
            slug = random.choice(slugs[:6])
            detail = self._json(self._get(f"/products/{slug}", "product_detail"))
            self._sleep(0.6, 2.0)
            if detail.get("variants"):
                return random.choice(detail["variants"])["public_id"]
        return None

    def search(self) -> None:
        term = random.choice(SEARCH_TERMS)
        if random.random() < 0.12:
            term = self._typo(term)
        self._get(f"/products?q={term}", "product_search")
        self._sleep()
        self._get(f"/products?q={term}&sort=price_asc", "product_search_sorted")

    @staticmethod
    def _typo(term: str) -> str:
        if len(term) < 2 or not term.isalpha():
            return term
        pos = random.randrange(len(term))
        return term[:pos] + term[pos + 1 :] if random.random() < 0.5 else term[:pos] + term[pos].swapcase() + term[pos + 1 :]

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
        self._sleep(0.3, 1.0)
        if random.random() < 0.3:
            self._request("PUT", f"/wishlist/products/{public_id}", "wishlist_add", json_body={})
        self._request("GET", "/wishlist", "wishlist_read")
        self._sleep(0.3, 1.0)
        if random.random() < 0.4:
            self._request("DELETE", f"/wishlist/products/{public_id}", "wishlist_remove")

    def coupon_glance(self) -> None:
        self._request("GET", "/coupons/available", "coupon_available")
        self._sleep()
        if random.random() < 0.35:
            self._request("GET", "/coupons/available", "coupon_available")

    def coupon_abandon(self) -> None:
        """Try an expired/invalid coupon code at quote time — a frequent real failure.

        The code is prefixed ``NOPE-`` so it can never collide with a real coupon
        in the OLTP database (e.g. WELCOME10); the failure stays genuine (409).
        """
        variant = self.browse()
        if not variant:
            return
        self._request("PUT", f"/cart/items/{variant}", "cart_add", json_body={"quantity": 1})
        self._sleep()
        code = "NOPE-" + self.fake.word().upper()[:10]
        self._request("POST", "/checkout/quote", "checkout_quote_invalid", json_body={"coupon_code": code})

    def dead_link(self) -> None:
        """A stale/deleted product link — real sites always have some 404s."""
        bogus = f"san-pham-{uuid.uuid4().hex[:8]}"
        self._get(f"/products/{bogus}", "product_dead_link")

    def failed_login(self) -> None:
        """Wrong password — most common 401 on the web."""
        self._request("POST", "/auth/login", "auth_login_failed",
                      json_body={"email": self.user.email, "password": self.fake.password()})

    def premature_review(self, order_number: str) -> None:
        """A customer tries to review before the order is completed → 409."""
        self._request("POST", f"/orders/{order_number}/items/{'00000000-0000-0000-0000-000000000000'}/review",
                      "review_premature", json_body={"rating": 5, "content": self.fake.sentence()})

    def purchase(self) -> None:
        if random.random() < self.error_rate:
            self.coupon_abandon()
            return
        variant = self.browse()
        if not variant:
            return
        self._request("PUT", f"/cart/items/{variant}", "cart_add", json_body={"quantity": random.randint(1, 3)})
        self._sleep(0.5, 1.5)
        self._request("POST", "/checkout/quote", "checkout_quote", json_body={})
        self._sleep(0.6, 2.0)

        body = {
            "receiver_name": self.fake.name(),
            "receiver_phone": self._vietnam_mobile(),
            "shipping_address_text": f"{self.fake.street_address()}, {random.choice(CITIES)}",
        }
        idem = str(uuid.uuid4())
        response = self._request("POST", "/checkout", "checkout_submit",
                                 json_body=body, idem=idem)
        if response.status_code not in (200, 201):
            return
        order = self._json(response).get("order_number")
        if not order:
            return
        self._sleep(0.5, 1.5)
        self._get(f"/orders/{order}", "order_detail")
        if random.random() < 0.1:
            self.premature_review(order)
        if random.random() < 0.6:
            self.complete_and_review(order)

    def complete_and_review(self, order_number: str) -> None:
        """Internal dispatch confirms, customer marks completed, then reviews — realistic lifecycle."""
        idem = str(uuid.uuid4())
        self._request("POST", f"/orders/{order_number}/confirm", "order_confirm",
                      idem=idem, internal=True)
        self._sleep(0.4, 1.2)
        self._request("POST", f"/orders/{order_number}/complete", "order_complete",
                      idem=str(uuid.uuid4()))
        self._sleep(0.5, 1.5)
        detail = self._json(self._get(f"/orders/{order_number}", "order_detail"))
        items = detail.get("items", [])
        if not items:
            return
        item = random.choice(items)
        rating = random.choice([5, 5, 4, 4, 4, 3, 3, 2, 1, 1])
        if rating >= 4:
            content = self.fake.sentence(nb_words=random.randint(6, 20))
        elif rating == 3:
            content = self.fake.sentence(nb_words=random.randint(4, 12))
        else:
            content = self.fake.sentence(nb_words=random.randint(4, 10)) + " không hài lòng lắm."
        self._request("POST", f"/orders/{order_number}/items/{item['public_id']}/review",
                      "review_write", json_body={"rating": rating, "content": content})

    def random_mistake(self) -> None:
        """One intentional, human-plausible error to keep the severity mix natural."""
        self.failed_login() if random.random() < 0.3 else (self.dead_link() if random.random() < 0.5 else self.coupon_glance())

    def run(self) -> None:
        """One visitor session: 2-6 actions with purchase probability by tenure."""
        steps = random.randint(2, 6)
        for i in range(steps):
            if random.random() < self.error_rate:
                self.random_mistake()
                self._sleep(0.3, 1.2)
                continue
            tenure_days = (self.clock.now().timestamp() - self.user.created_day) / 86400
            purchase_chance = min(0.08 + 0.04 * tenure_days, 0.45)
            roll = random.random()
            if i == steps - 1 and roll < purchase_chance:
                self.purchase()
            elif roll < 0.12:
                self.abandon_cart()
            elif roll < 0.22:
                self.wishlist()
            elif roll < 0.32:
                self.coupon_glance()
            elif roll < 0.50:
                self.search()
            elif roll < 0.65:
                self.filtered_listing()
            else:
                self.browse()
            self._sleep(0.3, 1.2)


class Simulator:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.clock = SimulatedClock(args.real_seconds, args.simulated_days)
        self.stats = Stats()
        self.fake = Faker("vi_VN")
        self.stop = threading.Event()
        self._lock = threading.Lock()
        self._active: dict[threading.Thread, SimUser] = {}

    def _spawn(self, pool: UserPool) -> None:
        with self._lock:
            client = httpx.Client(timeout=15.0, follow_redirects=True)
            user = pool.pick(for_purchase=random.random() < 0.25)
        session = Session(
            client,
            self.stats,
            user,
            self.args.base_url,
            self.fake,
            self.clock,
            self.args.error_rate,
            self.args.internal_secret,
        )

        thread = threading.Thread(target=self._run_session, args=(session,), daemon=True)
        with self._lock:
            self._active[thread] = user
        thread.start()

    def _run_session(self, session: Session) -> None:
        try:
            response = session._request("POST", "/auth/login", "auth_login", json_body={"email": session.user.email, "password": PASSWORD})
            if response.status_code not in (200, 201):
                session._request("POST", "/auth/register", "auth_register", json_body={"email": session.user.email, "password": PASSWORD, "display_name": session.user.display_name})
            session.run()
        finally:
            with self._lock:
                self._active.pop(threading.current_thread(), None)

    def run(self, pool: UserPool) -> None:
        started = time.monotonic()
        deadline = started + self.args.real_seconds
        print(f"==> Simulating web traffic to {self.args.base_url} for {self.args.real_seconds}s "
              f"simulating {self.args.simulated_days} days (concurrency {self.args.concurrency})")

        while not self.stop.is_set():
            now = time.monotonic()
            if now >= deadline:
                break
            target = max(1, round(self.args.concurrency * self.clock.intensity()))
            with self._lock:
                current = len(self._active)
            for _ in range(max(0, target - current)):
                self._spawn(pool)
            time.sleep(0.5)

        self.stop.set()
        with self._lock:
            for thread in list(self._active):
                thread.join(timeout=0.5)
        print(self.stats.summary())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate natural web traffic with time compression.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--real-seconds", type=int, default=300, help="Wall-clock run duration")
    parser.add_argument("--simulated-days", type=int, default=1, help="Simulated calendar span")
    parser.add_argument("--concurrency", type=int, default=8, help="Max concurrent sessions at peak hours")
    parser.add_argument("--seed-users", type=int, default=20, help="Seed users if pool is empty")
    parser.add_argument("--error-rate", type=float, default=0.06, help="Fraction of actions that fail like real users do (401/404/409)")
    parser.add_argument("--pool-file", type=Path, default=Path(__file__).parent / ".sim_users.tsv")
    parser.add_argument("--internal-secret", default="change-me-internal-secret", help="X-Internal-Secret for order confirm flow")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    simulator = Simulator(args)
    signal.signal(signal.SIGINT, lambda *_: simulator.stop.set())

    client = httpx.Client(timeout=15.0)
    try:
        pool = UserPool(args.pool_file, simulator.clock, args.base_url)
        if len(pool.users) < args.seed_users:
            print(f"==> Seeding user pool with {args.seed_users - len(pool.users)} users...")
            pool.seed(args.seed_users - len(pool.users), simulator.fake, client)
        if not pool.users:
            raise RuntimeError("No users in pool; seeding failed")
        simulator.run(pool)
    finally:
        client.close()


if __name__ == "__main__":
    main()