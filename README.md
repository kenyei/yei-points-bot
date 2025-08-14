# YEI Points Bot

一個自動化的 DeFi 協議互動機器人，用於在 Sei 區塊鏈上進行 YEI Finance 協議的供應和借貸操作。

## 功能特色

- 🔄 自動化供應和借貸循環操作
- ⏰ 支援多錢包排程執行
- 💰 智能健康因子管理
- 🛡️ 安全的私鑰管理
- 📊 即時餘額監控

## 專案結構

```
yei-points-bot/
├── main.py          # 主程式 - 執行自動化供應借貸循環
├── schedule.py      # 排程工具 - 為錢包生成隨機執行時間
├── bot.py           # 核心機器人邏輯
├── abi.py           # 智能合約 ABI 定義
├── wallets.json     # 錢包配置檔案
├── schedule.json    # 執行排程檔案
├── .env             # 環境變數設定檔案（需要自行建立）
└── README.md        # 專案說明文件
```

## 安裝需求

確保你已安裝 Python 3.8+ 和 uv 套件管理器。

```bash
# 安裝相依套件
uv sync
```

## 環境變數設定

本專案需要設定以下環境變數來連接到 Sei 區塊鏈和 YEI Finance 協議：

### 必要環境變數

在專案根目錄建立 `.env` 檔案，並設定以下環境變數：

```bash
# Sei 區塊鏈 RPC 端點
RPC_URL=https://evm-rpc.sei-apis.com

# YEI Finance 協議合約地址（請替換為實際地址）
POOL_ADDRESS=0x_your_pool_contract_address_here
WSEI_ADDRESS=0x_your_wsei_contract_address_here
ATOKEN_ADDRESS=0x_your_atoken_contract_address_here
DEBT_ADDRESS=0x_your_debt_token_contract_address_here
```

**設定步驟：**

1. 複製上述內容到 `.env` 檔案
2. 將 `0x_your_*_here` 替換為實際的合約地址
3. 確認 RPC URL 可正常連接

### 環境變數說明

| 變數名稱         | 說明                             | 範例                           |
| ---------------- | -------------------------------- | ------------------------------ |
| `RPC_URL`        | Sei 區塊鏈的 RPC 端點 URL        | `https://evm-rpc.sei-apis.com` |
| `POOL_ADDRESS`   | YEI Finance 的主要 Pool 合約地址 | `0x1234...`                    |
| `WSEI_ADDRESS`   | Wrapped SEI (WSEI) 代幣合約地址  | `0x5678...`                    |
| `ATOKEN_ADDRESS` | aWSEI 代幣合約地址（供應憑證）   | `0x9abc...`                    |
| `DEBT_ADDRESS`   | 債務代幣合約地址（借貸憑證）     | `0xdef0...`                    |

### 網路環境檔案

專案支援多個網路環境，你可以根據需求建立對應的環境檔案：

- `.env.sei` - Sei 主網環境設定
- `.env.inj` - Injective 網路環境設定（如適用）

**注意：** 請確保 `.env` 檔案已加入 `.gitignore`，避免敏感資訊被提交到版本控制。

## 使用方法

### 1. 設定環境變數

首先建立 `.env` 檔案並設定必要的環境變數（參考上方環境變數設定章節）。

### 2. 設定錢包檔案

建立 `wallets.json` 檔案，包含你的錢包資訊：

```json
[
  {
    "address": "0x你的錢包地址1",
    "pk": "你的私鑰1"
  },
  {
    "address": "0x你的錢包地址2",
    "pk": "你的私鑰2"
  }
]
```

### 3. 生成執行排程

使用 `schedule.py` 為每個錢包分配隨機執行時間：

```bash
# 基本用法 - 設定開始和結束時間戳記
python schedule.py --start 1754542179 --end 1754552179
```

這個指令會讀取 `wallets.json` 中的錢包地址，為每個地址在指定的時間範圍內分配一個隨機時間戳記，並將結果儲存到 `schedule.json`。

### 4. 執行主程式

確保已設定好環境變數、`wallets.json` 和 `schedule.json` 後，執行主程式：

```bash
# SEI
cp .env.sei .env
python main.py

# Injective
cp .env.inj .env
python main.py
```

## 主程式功能 (main.py)

### 核心功能

1. **錢包管理**

   - 載入多個錢包配置
   - 管理私鑰和地址映射

2. **排程執行**

   - 根據 `schedule.json` 中的時間戳記執行操作
   - 支援多錢包並行排程

3. **自動化操作流程**
   ```
   檢查餘額 → 轉換 SEI 為 WSEI → 供應抵押品 → 借貸循環 → 監控健康因子
   ```

### 操作邏輯

1. **餘額檢查與轉換**

   - 檢查 SEI 和 WSEI 餘額
   - 保留 10 SEI 作為手續費
   - 將多餘的 SEI 轉換為 WSEI

2. **供應與借貸循環**

   - 供應 WSEI 作為抵押品
   - 計算可借貸金額（抵押品的 80%）
   - 借出 WSEI 並再次供應
   - 重複直到健康因子接近最低閾值 (1.1)

3. **風險管理**
   - 最低健康因子設定為 1.1
   - 每次借貸使用 99% 的可借貸金額以留安全邊際

## 排程工具功能 (schedule.py)

`schedule.py` 是一個簡單的工具，用於為每個錢包地址生成隨機執行時間。它會讀取 `wallets.json` 檔案中的錢包地址，在指定的時間範圍內為每個地址分配一個隨機的 Unix 時間戳記，然後將結果儲存到 `schedule.json` 檔案中。

需要提供開始時間 (`--start`) 和結束時間 (`--end`) 兩個必要參數，時間格式為 Unix 時間戳記。
