# Weather Dashboard Tool

這是一個基於 Python 的天氣與空氣品質查詢工具，串接 OpenWeather API 提供多層級選單式的城市查詢。

## 功能特點
- 提供 5 天天氣預報。
- 即時天氣資訊（體感溫度、濕度、日落時間）。
- 空氣品質指標 (AQI) 與健康建議。

## 安裝與執行

1. **複製專案**
   ```bash
   git clone <你的 GitHub 專案網址>
   cd "weather dashboard"
   ```

2. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

3. **設定環境變數**
   建立 `.env` 檔案並填入你的 API Key：
   ```env
   OPENWEATHER_API_KEY='你的金鑰'
   ```