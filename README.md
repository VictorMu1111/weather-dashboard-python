# 🌤️ 全球天氣與 AI 智慧穿搭儀表板

這是一個使用 Python 和 Streamlit 開發的即時天氣查詢系統，對接 OpenWeather API 提供全球城市的即時天氣、空氣品質細項以及未來五天的預報，並內建 **AI 氣象與穿搭顧問機器人**！

---

## ✨ 功能特色

- **即時天氣**：包含氣溫、體感溫度、濕度、日落時間與今日降雨機率。
- **空氣品質**：顯示 AQI 指標與污染物濃度，並針對 PM2.5 提供具體的戶外運動建議。
- **5 天氣溫趨勢預報**：提供溫度變化折線圖與詳細氣象描述。
- 🤖 **AI 5 天氣象總整理與智慧穿搭指南**：
  - 綜合溫差起伏、晴雨轉折與 AQI 空氣指數，AI 自動生成條理清晰的天氣總評。
  - 提供分日穿搭、洋蔥式層次搭配、外出鞋履推薦與隨身必備清單（雨傘、防曬、口罩）。
  - 支援客製化穿搭風格（通用日常、上班通勤、休閒出遊、運動戶外、極簡防曬等）。
- 💬 **互動式 AI 天氣對話機器人 (Chatbot)**：
  - 在儀表板直接與 AI 機器人對話，隨時詢問特定行程穿搭（例如：「週五晚上約會該怎麼穿？」、「哪一天最適合洗曬衣服？」）。
  - 內建一鍵快捷提問按鈕。
- ⚡ **多模型與智慧備用支援**：
  - 支援 **Google Gemini**（推薦）與 **OpenAI**。
  - 內建 **智慧規則引擎 (Fallback)**，即使無 AI API Key 也能順暢產出高品質穿搭指南。

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
   在根目錄的 `.env` 檔案中填入金鑰（AI 金鑰可選填，亦可直接在網頁側邊欄輸入）：
   ```env
   OPENWEATHER_API_KEY=你的OpenWeather金鑰
   GEMINI_API_KEY=你的Gemini金鑰（選填）
   OPENAI_API_KEY=你的OpenAI金鑰（選填）
   ```

4. **啟動 Web App (推薦)**：
   ```bash
   streamlit run streamlit_app.py
   ```

5. **或執行終端機 CLI 版本**：
   ```bash
   python MyWeatherDashboard.py
   ```