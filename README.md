# 🌤️ 全球天氣與 AI 智慧穿搭儀表板

這是一個使用 Python 和 Streamlit 開發的即時天氣查詢系統，對接 OpenWeather API 提供全球城市的即時天氣、空氣品質細項以及未來五天的預報，並內建 **AI 氣象與穿搭顧問機器人**！

---

## ✨ 功能特色

### 🌡️ 天氣資訊
- **即時天氣**：氣溫、體感溫度、濕度、日落時間與今日降雨機率。
- **空氣品質**：AQI 指標與污染物濃度，並針對 PM2.5 提供具體的戶外運動建議。
- **5 天氣溫趨勢預報**：溫度變化折線圖與詳細氣象描述。

### 🤖 AI 智慧穿搭顧問
- **AI 5 天天氣總整理與穿搭指南**：
  - 綜合溫差起伏、晴雨轉折與 AQI 空氣指數，AI 自動生成條理清晰的天氣總評。
  - 提供分日穿搭、洋蔥式層次搭配、外出鞋履推薦與隨身必備清單。
  - 支援客製化穿搭風格（通用日常、上班通勤、休閒出遊、運動戶外、極簡防曬等）。

### 💬 AI 互動對話機器人
- 直接與 AI 機器人對話，隨時詢問特定行程穿搭。
- 內建一鍵快捷提問按鈕。

### ⚡ 雙 AI 引擎 + 智慧備援
- **Google Gemini**（主要 AI 引擎）
- **DeepSeek**（備援 AI 引擎）
- **智慧規則引擎**（免 API Key 備援模式）
- 使用者可自由切換 AI 引擎！

---

## 🚀 本地開發安裝步驟

1. **進入專案目錄**：
```bash
cd "weather dashboard"
```

2. **安裝必要套件**：
```bash
pip install -r requirements.txt
```

3. **設定 API 金鑰**：
在根目錄的 `.env` 檔案中填入金鑰：
```env
OPENWEATHER_API_KEY=你的OpenWeather金鑰
GEMINI_API_KEY=你的Gemini金鑰（選填）
DEEPSEEK_API_KEY=你的DeepSeek金鑰（選填）
```

4. **啟動 Web App**：
```bash
streamlit run streamlit_app.py
```

5. **或執行終端機 CLI 版本**：
```bash
python MyWeatherDashboard.py
```

---

## ☁️ Streamlit Cloud 部署

1. 將專案推送到 GitHub。
2. 到 [Streamlit Cloud](https://share.streamlit.io/) 建立新的 App。
3. 在 **Settings → Secrets** 中加入：
```toml
OPENWEATHER_API_KEY = "你的OpenWeather金鑰"
GEMINI_API_KEY = "你的Gemini金鑰"
DEEPSEEK_API_KEY = "你的DeepSeek金鑰"
```

---

## 🛠️ 使用的技術

- **Python 3.8+**
- **Streamlit**：Web 介面
- **OpenWeather API**：天氣資料
- **Google Gemini API**：AI 分析
- **DeepSeek API**：備援 AI 分析
- **Requests**：API 呼叫
- **python-dotenv**：環境變數管理

---

## 📁 專案結構

```
weather-dashboard-python/
├── streamlit_app.py          # Streamlit Web 主程式
├── MyWeatherDashboard.py     # CLI 版本主程式
├── ai_service.py             # AI 服務（Gemini/DeepSeek/規則引擎）
├── cities.json               # 城市資料庫
├── requirements.txt          # 依賴套件
├── .env                      # 環境變數（請勿上傳）
└── README.md                 # 說明文件
```

---

## 📝 版本歷史

- **v1**：基本天氣查詢功能
- **v2**：加入空氣品質與 5 天預報
- **v3**：加入 AI 穿搭顧問（Gemini）
- **v4**：加入 AI 對話機器人
- **v5**：新增 DeepSeek 備援引擎、AI 引擎自由切換

---

## 📜 授權

MIT License

---

## 💡 免責聲明

本工具僅供個人使用與學習參考。天氣與 AI 分析的結果可能因資料來源或模型差異而有所不同。
```

---

### 存檔後推送到 GitHub：

```bash
cd "/Users/victormu/Desktop/python work/weather dashboard"
git add README.md
git commit -m "docs: 更新 README 加入 DeepSeek 與雙引擎說明"
git push origin main --force