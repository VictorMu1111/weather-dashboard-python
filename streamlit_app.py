import streamlit as st
import json
from pathlib import Path
from MyWeatherDashboard import WeatherService, OPENWEATHER_API_KEY, aqi_label, aqi_health_advice, component_ch_name, get_component_status
from datetime import datetime, timezone, timedelta

# 頁面設定
st.set_page_config(page_title="全球天氣儀表板", page_icon="🌤️", layout="wide")

current_dir = Path(__file__).parent.resolve()

def load_geo_data():
    try:
        with open(current_dir / 'cities.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("找不到 cities.json 檔案，請確認檔案路徑。")
        return {}

# 使用快取來減少重複的 API 請求 (設定 TTL 為 600 秒，即 10 分鐘)
@st.cache_data(ttl=600)
def fetch_weather_data(_service, city):
    current = _service.get_current_weather(city)
    if not current:
        return None, None, None
    
    lat, lon = current['coord']['lat'], current['coord']['lon']
    air = _service.get_air_quality(lat, lon)
    forecast = _service.get_daily_forecast(city)
    
    return current, air, forecast

def main():
    st.title("🌤️ 全球天氣與空氣品質儀表板")

    # 優先從 Streamlit Secrets 讀取 (雲端部署用)，若無則從本地環境變數讀取
    api_key = st.secrets.get("OPENWEATHER_API_KEY", OPENWEATHER_API_KEY)
    
    if not api_key:
        st.error("❌ 找不到 API 金鑰！")
        st.info("本地執行：請確保 .env 檔案中有 OPENWEATHER_API_KEY\n\n雲端部署：請在 Streamlit Cloud 的 Secrets 設定中加入金鑰。")
        return

    try:
        weather_svc = WeatherService(api_key)
    except ValueError as e:
        st.error(f"初始化服務失敗: {e}")
        return
        
    geo_data = load_geo_data()
    if not geo_data:
        return

    # 側邊欄選單
    st.sidebar.header("地點選擇")
    regions = list(geo_data.keys())
    selected_region = st.sidebar.selectbox("選擇區域", regions)

    countries = list(geo_data[selected_region].keys())
    selected_country = st.sidebar.selectbox("選擇國家", countries)

    cities = geo_data[selected_region][selected_country]
    selected_city = st.sidebar.selectbox("選擇城市", cities + ["手動輸入"])

    target_city = selected_city
    if selected_city == "手動輸入":
        target_city = st.sidebar.text_input("請輸入城市英文名稱", value="London")

    # 當 target_city 有效時，自動執行查詢
    if target_city:
        # 使用優化後的快取函式獲取資料
        current, air, forecast = fetch_weather_data(weather_svc, target_city)

        if current:
            # --- 顯示當地時間 ---
            timezone_offset = current.get('timezone', 0)
            local_time = datetime.now(timezone.utc).astimezone(timezone(timedelta(seconds=timezone_offset)))
            st.subheader(f"📍 {target_city}")
            st.caption(f"當地時間: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            st.markdown("---")
            st.subheader(f"當前天氣")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            temp = current['main'].get('temp')
            feels = current['main'].get('feels_like')
            humidity = current['main'].get('humidity')
            
            col1.metric("氣溫", f"{int(round(temp)) if temp is not None else '--'}°C")
            col2.metric("體感溫度", f"{int(round(feels)) if feels is not None else '--'}°C")
            col3.metric("濕度", f"{humidity}%")
            
            # 日落時間處理
            sunset_ts = current['sys'].get('sunset')
            sunset_local = datetime.fromtimestamp(sunset_ts, tz=timezone.utc).astimezone(
                timezone(timedelta(seconds=timezone_offset))).strftime('%H:%M')
            col4.metric("日落時間", sunset_local)

            # 降雨機率 (從預報中取得今日數值)
            today_pop = 0
            if forecast:
                today_pop = forecast[0].get('pop', 0)
            col5.metric("今日降雨率", f"{today_pop}%")

            # 2. 空氣品質
            if air and 'list' in air:
                aq = air['list'][0]
                aqi = aq['main']['aqi']
                
                st.markdown("---")
                st.subheader("🌫️ 空氣品質指標 (AQI)")
                
                aqi_colors = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "🟣"}
                st.info(f"{aqi_colors.get(aqi, '⚪')} **AQI 等級: {aqi} ({aqi_label(aqi)})**\n\n💡 {aqi_health_advice(aqi)}")
                
                # 污染物詳細數據
                comps = aq['components']
                comp_cols = st.columns(len(comps))
                for i, (k, v) in enumerate(comps.items()):
                    comp_cols[i].caption(component_ch_name(k))
                    comp_cols[i].write(f"{v}")
                    status = get_component_status(k, v)
                    if status:
                        comp_cols[i].caption(status)

            # 3. 未來預報
            st.markdown("---")
            st.subheader("📅 未來 7 天天氣預報")
            st.caption("註：免費版 API 提供 5 天預報資料")
            if forecast:
                # 建立溫度趨勢圖數據
                chart_data = {
                    "日期": [d['date'] for d in forecast],
                    "最低溫": [d['min_temp'] for d in forecast],
                    "最高溫": [d['max_temp'] for d in forecast]
                }
                st.line_chart(data=chart_data, x="日期", y=["最低溫", "最高溫"])
                
                # 轉換為表格顯示
                display_forecast = []
                for d in forecast:
                    display_forecast.append({
                        "日期": d['date'],
                        "最低溫 (°C)": d['min_temp'],
                        "最高溫 (°C)": d['max_temp'],
                        "降雨機率": f"{d['pop']}%",
                        "天氣描述": d['description']
                    })
                st.table(display_forecast)
        else:
            st.error(f"⚠️ 無法取得 '{target_city}' 的天氣資料。")
            st.warning("請檢查：\n1. 城市英文名稱是否正確 (例如: London, Taipei)\n2. API 金鑰是否有效\n3. 網路連線是否正常")

if __name__ == "__main__":
    main()