#!/usr/bin/env python3
"""
Script to create a schedule.json file with random timestamps for each wallet address
"""

import argparse
import json
import random
import sys


def load_wallets(wallets_file: str) -> list:
    with open(wallets_file, "r", encoding="utf-8") as f:
        return json.load(f)


def create_schedule(wallets: list, start_time: int, end_time: int) -> dict:
    """Create schedule with random timestamps for each wallet address"""
    if start_time >= end_time:
        print("錯誤：開始時間必須小於結束時間")
        sys.exit(1)

    schedule = {}

    for wallet in wallets:
        address = wallet.get("address")
        if not address:
            print("警告：發現沒有地址的錢包，跳過")
            continue

        # Generate random timestamp between start and end
        random_time = random.randint(start_time, end_time)
        schedule[address] = random_time

    return schedule


def save_schedule(schedule: dict, output_file: str):
    """Save schedule to JSON file"""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)
        print(f"排程已儲存至 {output_file}")
    except Exception as e:
        print(f"錯誤：無法儲存排程檔案 - {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="為錢包地址建立隨機時間排程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python schedule.py --start 1754542179 --end 1754552179
  python schedule.py --start 1754542179 --end 1754552179 --wallets custom_wallets.json
  python schedule.py --start 1754542179 --end 1754552179 --output custom_schedule.json
        """,
    )

    parser.add_argument(
        "--start", type=int, required=True, help="開始時間戳記（Unix timestamp）"
    )

    parser.add_argument(
        "--end", type=int, required=True, help="結束時間戳記（Unix timestamp）"
    )

    parser.add_argument(
        "--wallets",
        type=str,
        default="wallets.json",
        help="錢包檔案路徑（預設：wallets.json）",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="schedule.json",
        help="輸出排程檔案路徑（預設：schedule.json）",
    )

    parser.add_argument("--seed", type=int, help="隨機數種子（用於可重現的結果）")

    args = parser.parse_args()

    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        print(f"使用隨機數種子：{args.seed}")

    print(f"讀取錢包檔案：{args.wallets}")
    wallets = load_wallets(args.wallets)
    print(f"找到 {len(wallets)} 個錢包")

    print(f"建立排程（時間範圍：{args.start} - {args.end}）")
    schedule = create_schedule(wallets, args.start, args.end)

    print(f"為 {len(schedule)} 個地址分配了隨機時間")

    save_schedule(schedule, args.output)

    # Display sample of the schedule
    print("\n排程範例：")
    for i, (address, timestamp) in enumerate(schedule.items()):
        if i < 3:  # Show first 3 entries
            print(f"  {address}: {timestamp}")
        elif i == 3 and len(schedule) > 3:
            print(f"  ... 還有 {len(schedule) - 3} 個地址")
            break


if __name__ == "__main__":
    main()
