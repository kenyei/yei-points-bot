import json
import os
import random
import time

from eth_account import Account
from web3 import Web3

from bot import YeiPointBot

MIN_HEALTH_FACTOR = float(os.getenv("MIN_HEALTH_FACTOR"))
REMAINING_SEI_AMOUNT = int(float(os.getenv("REMAINING_SEI_AMOUNT")) * 1e18)
MAX_LTV = float(os.getenv("MAX_LTV"))
EMODE = int(os.getenv("EMODE"))


USDC_ADDRESS = "0x9cc91646ab84efa26469db98592f28B8b729C1c3"


def load_wallets() -> list:
    with open("wallets.json", "r") as f:
        wallets = json.load(f)
    return wallets


def load_schedules() -> dict:
    with open("schedule.json", "r") as f:
        schedule = json.load(f)
    return schedule


def supply_and_borrow(wallet: Account):
    print(f"=== Looping for {wallet.address} ===")

    bot = YeiPointBot(wallet.key)

    current_emode = bot.get_user_emode()
    print(f"Current eMode category: {current_emode}")
    if current_emode != EMODE:
        print(f"enabling eMode category {EMODE}...")
        bot.set_user_emode(EMODE)
    else:
        print(f"eMode already enabled with category {current_emode}")

    sei_balance = bot.get_native_balance(wallet.address)
    wsei_balance = bot.get_wsei_balance()

    print(f"SEI: {Web3.from_wei(sei_balance, 'ether'):.6f} SEI")
    print(f"WSEI: {Web3.from_wei(wsei_balance, 'ether'):.6f} WSEI")

    SUPPLY_WSEI_AMOUNT = int(0.5 * 1e18)
    BORROW_USDC_AMOUNT = int(0.1 * 1e6)
    REPAY_USDC_AMOUNT = int(0.05 * 1e6)
    WITHDRAW_WSEI_AMOUNT = int(0.1 * 1e18)

    bot.wrap_sei_to_wsei(SUPPLY_WSEI_AMOUNT)
    bot.supply(bot.WSEI_ADDRESS, SUPPLY_WSEI_AMOUNT)
    bot.borrow(USDC_ADDRESS, BORROW_USDC_AMOUNT)
    bot.repay(USDC_ADDRESS, REPAY_USDC_AMOUNT)
    bot.withdraw(bot.WSEI_ADDRESS, WITHDRAW_WSEI_AMOUNT)

    print("=== Looping completed ===\n")


def main():
    wallets = load_wallets()
    schedules = load_schedules()

    accounts = {wallet["address"]: Account.from_key(wallet["pk"]) for wallet in wallets}

    while True:
        current_time = time.time()
        print(current_time)

        new_schedules = {}
        for wallet_address, schedule_time in schedules.items():
            if schedule_time <= current_time:
                supply_and_borrow(accounts[wallet_address])
            else:
                new_schedules[wallet_address] = schedule_time
        schedules = new_schedules

        time.sleep(random.randint(1, 3))


if __name__ == "__main__":
    main()
