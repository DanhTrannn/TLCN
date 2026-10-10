#!/usr/bin/env python3
"""Interactive CLI Controller for Real-Time CDC Business Signals Simulation."""

import argparse
import os
import sys
import time

# Ensure /app or repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from demo.scenarios import (
    reset_all,
    s1_marketing_flash_sale,
    s2_inventory_depletion,
    s3_operations_boom_spike,
    s4_pos_store_rush,
    s5_sales_viral_surge,
    s6_executive_cash_flow,
)

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"

SCENARIOS = {
    "1": ("Marketing: Cháy ngân sách Flash Sale (95%) & Bùng phát 1-Star Review Spam", s1_marketing_flash_sale.run),
    "2": ("Inventory: Tốc độ rút kho nguy cấp (<10p) & Cháy hàng kích hoạt Sold Out", s2_inventory_depletion.run),
    "3": ("Operations: Điểm nóng Boom COD Bình Tân (100%) & Ùn tắc đóng gói >20 đơn", s3_operations_boom_spike.run),
    "4": ("Store POS: Cháy hàng tại quầy POS & Giờ cao điểm bán lẻ kéo Run-Rate đạt chỉ tiêu", s4_pos_store_rush.run),
    "5": ("Sales: Mẫu sản phẩm Viral tăng tốc x4.8 lần & Cảnh báo lệch pha kênh Online", s5_sales_viral_surge.run),
    "6": ("Executive: Tiền mặt COD shipper trôi nổi (+350tr) & Xói mòn biên lợi nhuận gộp", s6_executive_cash_flow.run),
}


def print_menu() -> None:
    print(f"\n{C_BOLD}{C_BLUE}{'═' * 76}{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}  D&K E-COMMERCE LAKEHOUSE – TRÌNH MÔ PHỎNG TÍN HIỆU BIẾN ĐỘNG CDC{C_RESET}")
    print(f"{C_WHITE}  Change Data Capture Real-Time Business Signals Interactive Simulator{C_RESET}")
    print(f"{C_BLUE}{'═' * 76}{C_RESET}")
    for key, (desc, _) in SCENARIOS.items():
        print(f"  {C_BOLD}{C_YELLOW}[{key}]{C_RESET} {desc}")
    print(f"{C_BLUE}{'─' * 76}{C_RESET}")
    print(f"  {C_BOLD}{C_GREEN}[A]{C_RESET} Chạy TẤT CẢ 6 kịch bản cùng lúc (Full Demo)")
    print(f"  {C_BOLD}{C_MAGENTA}[R]{C_RESET} Khôi phục (Reset) toàn bộ dữ liệu demo về trạng thái ban đầu")
    print(f"  {C_BOLD}{C_RED}[Q]{C_RESET} Thoát chương trình")
    print(f"{C_BLUE}{'═' * 76}{C_RESET}\n")


def run_all() -> None:
    print(f"\n{C_BOLD}{C_GREEN}🚀 BẮT ĐẦU CHẠY TOÀN BỘ 6 KỊCH BẢN CDC...{C_RESET}\n")
    for key in sorted(SCENARIOS.keys()):
        desc, func = SCENARIOS[key]
        func()
        time.sleep(1)
    print(f"\n{C_BOLD}{C_GREEN}🎉 ĐÃ KÍCH HOẠT THÀNH CÔNG TẤT CẢ 6 TÍN HIỆU CDC TRÊN DASHBOARD!{C_RESET}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="D&K CDC Signals Simulator")
    parser.add_argument(
        "positional_scenario",
        nargs="?",
        choices=["1", "2", "3", "4", "5", "6", "all", "reset"],
        help="Chạy trực tiếp kịch bản cụ thể (ví dụ: 1, 2, all, reset)",
    )
    parser.add_argument(
        "--scenario",
        "-s",
        choices=["1", "2", "3", "4", "5", "6", "all", "reset"],
        help="Chạy trực tiếp kịch bản cụ thể mà không cần menu tương tác",
    )
    args = parser.parse_args()

    selected = args.scenario or args.positional_scenario
    if selected:
        if selected == "all":
            run_all()
        elif selected == "reset":
            reset_all.run()
        elif selected in SCENARIOS:
            SCENARIOS[selected][1]()
        return

    # Interactive mode
    while True:
        print_menu()
        try:
            choice = input(f"{C_BOLD}{C_WHITE}👉 Nhập lựa chọn của bạn [1-6, A, R, Q]: {C_RESET}").strip().upper()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã hủy.")
            sys.exit(0)

        if choice == "Q":
            print(f"\n{C_YELLOW}Tạm biệt! Chúc bạn có buổi thuyết trình bảo vệ đồ án thành công.{C_RESET}\n")
            break
        elif choice == "A":
            run_all()
        elif choice == "R":
            reset_all.run()
        elif choice in SCENARIOS:
            SCENARIOS[choice][1]()
        else:
            print(f"\n{C_RED}Lựa chọn không hợp lệ, vui lòng thử lại!{C_RESET}")

        try:
            input(f"\n{C_CYAN}Nhấn [Enter] để quay lại menu chính...{C_RESET}")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
