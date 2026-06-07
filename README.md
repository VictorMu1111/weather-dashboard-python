# 🌤️ 全球天氣與空氣品質儀表板

這是一個使用 Python 和 Streamlit 開發的即時天氣查詢系統，對接 OpenWeather API 提供全球城市的即時天氣、空氣品質細項以及未來五天的預報。

## ✨ 功能特色
- **即時天氣**：包含氣溫、體感溫度、濕度、日落時間與今日降雨機率。
- **空氣品質**：顯示 AQI 指標，並針對 PM2.5 提供具體的戶外運動建議。
- **7 天預報**：提供溫度趨勢圖表與詳細的氣象描述（視 API 權限而定）。

## 🚀 本地開發安裝步驟

1. **複製專案**：
   ```bash
   git clone [你的倉庫網址]
   cd [專案目錄]
   ```
2. **安裝必要套件**：
   ```bash
   pip install -r requirements.txt
   ```
3. **設定 API 金鑰**：
   在根目錄建立 `.env` 檔案並填入：`OPENWEATHER_API_KEY=你的金鑰`
4. **啟動 App**：
   ```bash
   streamlit run streamlit_app.py
   ```