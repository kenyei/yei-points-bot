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

    if sei_balance + wsei_balance > REMAINING_SEI_AMOUNT:
        if sei_balance > REMAINING_SEI_AMOUNT:
            convert_amount = sei_balance - REMAINING_SEI_AMOUNT
            bot.wrap_sei_to_wsei(convert_amount)
        if wsei_balance > 0:
            bot.supply(bot.WSEI_ADDRESS, wsei_balance)

    while True:
        health_factor = bot.get_user_account_data()["healthFactor"] / 1e18
        print(f"Health factor: {health_factor:.2f}")
        if health_factor <= MIN_HEALTH_FACTOR:
            break
        atoken_balance = bot.get_atoken_balance()
        debt_balance = bot.get_debt_balance()
        print(f"aWSEI: {Web3.from_wei(atoken_balance, 'ether'):.6f} aWSEI")
        print(f"debtWSEI: {Web3.from_wei(debt_balance, 'ether'):.6f} debtWSEI")
        borrowable_amount = atoken_balance * MAX_LTV - debt_balance
        borrowable_amount = int(borrowable_amount * 0.99)
        bot.borrow(bot.WSEI_ADDRESS, borrowable_amount)
        bot.supply(bot.WSEI_ADDRESS, borrowable_amount)

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
