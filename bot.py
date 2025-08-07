import random
import time

from eth_account import Account
from web3 import Web3

from abi import ERC20_ABI, POOL_ABI, WSEI_ABI


class YeiPointBot:
    RPC_URL = "https://evm-rpc.sei-apis.com/?x-apikey=d0227c6f"
    POOL_ADDRESS = "0x4a4d9abD36F923cBA0Af62A39C01dEC2944fb638"
    WSEI_ADDRESS = "0xE30feDd158A2e3b13e9badaeABaFc5516e95e8C7"
    ATOKEN_ADDRESS = "0x809FF4801aA5bDb33045d1fEC810D082490D63a4"
    DEBT_ADDRESS = "0x648e683aaE7C18132564F8B48C625aE5038A9607"

    def __init__(self, private_key):
        """
        Initialize Aave V3 Bot

        Args:
            rpc_url: RPC endpoint URL
            private_key: Private key for transactions
            pool_address: Aave V3 Pool contract address
        """
        self.w3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        self.account = Account.from_key(private_key)
        self.pool_contract = self.w3.eth.contract(
            address=self.POOL_ADDRESS, abi=POOL_ABI
        )
        self.wsei_contract = self.w3.eth.contract(
            address=self.WSEI_ADDRESS, abi=WSEI_ABI
        )
        self.atoken_contract = self.w3.eth.contract(
            address=self.ATOKEN_ADDRESS, abi=ERC20_ABI
        )
        self.debt_contract = self.w3.eth.contract(
            address=self.DEBT_ADDRESS, abi=ERC20_ABI
        )

    def random_sleep(self, min_seconds=3, max_seconds=10):
        sleep_time = random.uniform(min_seconds, max_seconds)
        time.sleep(sleep_time)

    def get_erc20_contract(self, token_address):
        """Get ERC20 token contract instance"""
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address), abi=ERC20_ABI
        )

    def get_wsei_contract(self):
        return self.w3.eth.contract(address=self.WSEI_ADDRESS, abi=WSEI_ABI)

    def get_atoken_contract(self):
        return self.w3.eth.contract(address=self.ATOKEN_ADDRESS, abi=ERC20_ABI)

    def get_debt_contract(self):
        return self.w3.eth.contract(address=self.DEBT_ADDRESS, abi=ERC20_ABI)

    def get_wsei_balance(self):
        return self.wsei_contract.functions.balanceOf(self.account.address).call()

    def get_atoken_balance(self):
        return self.atoken_contract.functions.balanceOf(self.account.address).call()

    def get_debt_balance(self):
        return self.debt_contract.functions.balanceOf(self.account.address).call()

    def wrap_sei_to_wsei(self, amount):
        txn = self.wsei_contract.functions.deposit(amount).build_transaction(
            {
                "from": self.account.address,
                "value": amount,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 300000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        signed_txn = self.w3.eth.account.sign_transaction(txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.random_sleep()
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"Wrapped {amount} SEI to WSEI! Transaction hash: {tx_hash.hex()}")
        else:
            print(
                f"Wrapped {amount} SEI to WSEI failed! Transaction hash: {tx_hash.hex()}"
            )

    def approve_token(self, token_address, amount):
        """
        Approve token spending for Aave Pool

        Args:
            token_address: Token contract address
            amount: Amount to approve
        """
        token_contract = self.get_erc20_contract(token_address)

        # Build approve transaction
        approve_txn = token_contract.functions.approve(
            self.pool_contract.address, amount
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 100000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(approve_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.random_sleep()

        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"Token approved! Transaction hash: {tx_hash.hex()}")
        else:
            print(f"Token approval failed! Transaction hash: {tx_hash.hex()}")
        return receipt

    def supply(self, token_address, amount, on_behalf_of=None):
        """
        Supply tokens to Aave V3 Pool

        Args:
            token_address: Token contract address to supply
            amount: Amount to supply (in wei)
            on_behalf_of: Address to receive aTokens (default: caller)
        """
        if on_behalf_of is None:
            on_behalf_of = self.account.address

        # First approve token spending
        print(f"Approving {amount} tokens...")
        self.approve_token(token_address, amount)

        # Build supply transaction
        supply_txn = self.pool_contract.functions.supply(
            Web3.to_checksum_address(token_address),
            amount,
            Web3.to_checksum_address(on_behalf_of),
            0,  # referralCode
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 300000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(supply_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.random_sleep()

        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"Supply successful! Transaction hash: {tx_hash.hex()}")
        else:
            print(f"Supply failed! Transaction hash: {tx_hash.hex()}")
        return receipt

    def set_user_emode(self, category_id):
        """
        Set user efficiency mode (eMode)

        Args:
            category_id: eMode category ID (0 to disable, 1+ for categories)
        """
        # Build setUserEMode transaction
        emode_txn = self.pool_contract.functions.setUserEMode(
            category_id
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 150000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(emode_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.random_sleep()

        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(
                f"eMode set to category {category_id}! Transaction hash: {tx_hash.hex()}"
            )
        else:
            print(
                f"eMode set to category {category_id} failed! Transaction hash: {tx_hash.hex()}"
            )
        return receipt

    def borrow(self, token_address, amount, interest_rate_mode=2, on_behalf_of=None):
        """
        Borrow tokens from Aave V3 Pool

        Args:
            token_address: Token contract address to borrow
            amount: Amount to borrow (in wei)
            interest_rate_mode: 1 for stable, 2 for variable (default: 2)
            on_behalf_of: Address to receive borrowed tokens (default: caller)
        """
        if on_behalf_of is None:
            on_behalf_of = self.account.address

        # Build borrow transaction
        borrow_txn = self.pool_contract.functions.borrow(
            Web3.to_checksum_address(token_address),
            amount,
            interest_rate_mode,
            0,  # referralCode
            Web3.to_checksum_address(on_behalf_of),
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 400000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(borrow_txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        self.random_sleep()

        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"Borrow successful! Transaction hash: {tx_hash.hex()}")
        else:
            print(f"Borrow failed! Transaction hash: {tx_hash.hex()}")
        return receipt

    def get_user_emode(self, user_address=None):
        """
        Get user's current eMode category

        Args:
            user_address: User address to check (default: caller)
        """
        if user_address is None:
            user_address = self.account.address

        emode_category = self.pool_contract.functions.getUserEMode(
            Web3.to_checksum_address(user_address)
        ).call()

        return emode_category

    def get_native_balance(self, address=None):
        """
        Get native token (SEI) balance

        Args:
            address: Address to check balance (default: caller)
        """
        if address is None:
            address = self.account.address

        balance = self.w3.eth.get_balance(Web3.to_checksum_address(address))
        return balance

    def get_erc20_balance(self, token_address, address=None):
        """
        Get ERC20 token balance

        Args:
            token_address: Token contract address
            address: Address to check balance (default: caller)
        """
        if address is None:
            address = self.account.address

        token_contract = self.get_erc20_contract(token_address)
        balance = token_contract.functions.balanceOf(
            Web3.to_checksum_address(address)
        ).call()
        return balance

    def get_user_account_data(self, user_address=None):
        """
        Get user's account data from Aave

        Args:
            user_address: User address to check (default: caller)
        """
        if user_address is None:
            user_address = self.account.address

        account_data = self.pool_contract.functions.getUserAccountData(
            Web3.to_checksum_address(user_address)
        ).call()

        # Returns: totalCollateralBase, totalDebtBase, availableBorrowsBase,
        # currentLiquidationThreshold, ltv, healthFactor
        return {
            "totalCollateralBase": account_data[0],
            "totalDebtBase": account_data[1],
            "availableBorrowsBase": account_data[2],
            "currentLiquidationThreshold": account_data[3],
            "ltv": account_data[4],
            "healthFactor": account_data[5],
        }

    def get_reserve_data(self, token_address):
        """
        Get reserve data for a specific token

        Args:
            token_address: Token contract address
        """
        reserve_data = self.pool_contract.functions.getReserveData(
            Web3.to_checksum_address(token_address)
        ).call()

        return {
            "configuration": reserve_data[0],
            "liquidityIndex": reserve_data[1],
            "currentLiquidityRate": reserve_data[2],
            "variableBorrowIndex": reserve_data[3],
            "currentVariableBorrowRate": reserve_data[4],
            "currentStableBorrowRate": reserve_data[5],
            "lastUpdateTimestamp": reserve_data[6],
            "id": reserve_data[7],
            "aTokenAddress": reserve_data[8],
            "stableDebtTokenAddress": reserve_data[9],
            "variableDebtTokenAddress": reserve_data[10],
            "interestRateStrategyAddress": reserve_data[11],
            "accruedToTreasury": reserve_data[12],
            "unbacked": reserve_data[13],
            "isolationModeTotalDebt": reserve_data[14],
        }
