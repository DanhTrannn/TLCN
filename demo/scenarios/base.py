"""Helper base module for CDC simulation scenarios."""

import sys
import uuid
from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from sqlalchemy.orm import Session

# ANSI terminal colors
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"
C_BG_BLUE = "\033[44m"
C_BG_RED = "\033[41m"
C_BG_GREEN = "\033[42m"


def print_banner(title: str, role: str, url: str) -> None:
    print(f"\n{C_CYAN}╔{'═' * 76}╗{C_RESET}")
    print(f"{C_CYAN}║ {C_BOLD}{C_WHITE}{title.center(74)}{C_RESET}{C_CYAN} ║{C_RESET}")
    print(f"{C_CYAN}╠{'═' * 76}╣{C_RESET}")
    print(f"{C_CYAN}║ {C_YELLOW}Vai trò quản trị:{C_RESET} {role:<57}{C_CYAN}║{C_RESET}")
    print(f"{C_CYAN}║ {C_GREEN}Trực quan Dashboard:{C_RESET} {url:<54}{C_CYAN}║{C_RESET}")
    print(f"{C_CYAN}╚{'═' * 76}╝{C_RESET}\n")


def print_step(step_num: int, title: str) -> None:
    print(f"{C_BOLD}{C_BLUE}[BƯỚC {step_num}]{C_RESET} {C_WHITE}{title}{C_RESET}")


def print_cdc_event(table: str, op: str, details: str) -> None:
    op_color = C_GREEN if op.upper() in ("INSERT", "CREATE") else (C_YELLOW if op.upper() == "UPDATE" else C_RED)
    print(f"  {C_BOLD}{C_MAGENTA}⚡ [CDC BINLOG]{C_RESET} Bảng {C_CYAN}`{table}`{C_RESET} | Thao tác {op_color}{op.upper()}{C_RESET}: {details}")


def print_dashboard_impact(metric: str, before: str, after: str, alert: str | None = None) -> None:
    print(f"  {C_BOLD}{C_GREEN}📊 [DASHBOARD IMPACT]{C_RESET} Chỉ số {C_WHITE}`{metric}`{C_RESET}: {C_YELLOW}{before}{C_RESET} ➔ {C_GREEN}{C_BOLD}{after}{C_RESET}")
    if alert:
        print(f"  {C_BOLD}{C_RED}🚨 [CẢNH BÁO BẬT]{C_RESET} {alert}")


def print_success(message: str) -> None:
    print(f"\n{C_BOLD}{C_GREEN}✔ {message}{C_RESET}\n")


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
