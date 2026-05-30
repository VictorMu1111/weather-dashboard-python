import os
import requests
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from pathlib import Path
import warnings
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any

# 忽略 urllib3 的 NotOpenSSLWarning (macOS 系統 Python 常見問題)
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# 使用 pathlib 取得路徑，更現代且易讀
current_dir = Path(__file__).parent.resolve()
dotenv_path = current_dir / '.env'
load_dotenv(dotenv_path=dotenv_path)

# 從環境變數獲取 API 金鑰
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')

class WeatherService:
    """封裝 OpenWeather API 的服務類別"""
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key 缺失，請檢查 .env 檔案")
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"

    def get_daily_forecast(self, city_name: str) -> Optional[List[Dict[str, Any]]]:
        """取得五天預報並彙整"""
        url = f"{self.base_url}/forecast"
        params = {'q': city_name, 'appid': self.api_key, 'units': 'metric', 'lang': 'zh_tw'}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            daily_forecast = defaultdict(lambda: {'temp_min': float('inf'), 'temp_max': float('-inf'), 'description': set(), 'icon': set()})
            for item in data['list']:
                date = datetime.fromisoformat(item['dt_txt']).date()
                daily_forecast[date]['temp_min'] = min(daily_forecast[date]['temp_min'], item['main']['temp_min'])
                daily_forecast[date]['temp_max'] = max(daily_forecast[date]['temp_max'], item['main']['temp_max'])
                daily_forecast[date]['description'].add(item['weather'][0]['description'])
                daily_forecast[date]['icon'].add(item['weather'][0]['icon'])

            return [{
                'date': d.strftime('%Y-%m-%d'),
                'min_temp': round(v['temp_min'], 1),
                'max_temp': round(v['temp_max'], 1),
                'description': ', '.join(sorted(list(v['description'])))
            } for d, v in sorted(daily_forecast.items())]
        except Exception as e:
            print(f"預報查詢失敗: {e}")
            return None

    def get_current_weather(self, city_name: str) -> Optional[Dict[str, Any]]:
        """取得即時天氣"""
        url = f"{self.base_url}/weather"
        params = {'q': city_name, 'appid': self.api_key, 'units': 'metric', 'lang': 'zh_tw'}
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"即時天氣錯誤: {e}")
            return None

    def get_air_quality(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """取得空氣品質"""
        url = f"{self.base_url}/air_pollution"
        params = {'lat': lat, 'lon': lon, 'appid': self.api_key}
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"空氣品質錯誤: {e}")
            return None


def aqi_label(aqi: Optional[int]) -> str:
    labels = {1: "優", 2: "良好", 3: "普通", 4: "不良", 5: "非常差"}
    return labels.get(aqi, "未知")

def component_ch_name(key: str) -> str:
    names = {
        'pm2_5': 'PM2.5',
        'pm10': 'PM10',
        'no2': 'NO2',
        'so2': 'SO2',
        'o3': 'O3',
        'co': 'CO',
        'nh3': 'NH3'
    }
    return names.get(key, key)


def aqi_health_advice(aqi: Optional[int]) -> str:
    """根據 AQI 等級回傳健康建議（中文）。"""
    advice = {
        1: "空氣品質優良，適合外出活動。",
        2: "空氣品質良好，少數敏感族群可能有輕微不適。",
        3: "空氣品質普通，敏感族群建議減少長時間或劇烈的戶外活動。",
        4: "空氣品質不良，敏感族群應避免外出，一般族群減少戶外劇烈活動。",
        5: "空氣品質非常差，建議避免所有戶外活動，並採取防護措施（關閉門窗、使用空氣清淨）。"
    }
    return advice.get(aqi, "無健康建議 (AQI 未知)")

# --- 主要執行部分 ---
def main():
    weather_svc = WeatherService(OPENWEATHER_API_KEY)

    # 1. 讀取外部地理資料檔案
    cities_path = current_dir / 'cities.json'
    try:
        with open(cities_path, 'r', encoding='utf-8') as f:
            geo_data = json.load(f)
    except FileNotFoundError:
        print(f"錯誤: 找不到資料檔案 {cities_path}")
        return
    except json.JSONDecodeError:
        print(f"錯誤: {cities_path} 格式不正確")
        return
    except Exception as e:
        print(f"讀取資料時發生未知錯誤: {e}")
        return

    while True:
        print("\n" + "="*40)
        print("      天氣預報查詢系統 (多層級選單)")
        print("="*40)

        # 第一層：選擇區域
        regions = list(geo_data.keys())
        print("\n[第一層] 請選擇區域：")
        for i, region in enumerate(regions, 1):
            print(f"{i}. {region}")
        print("0. 結束程式")

        choice1 = input("\n請輸入編號: ").strip()
        if choice1 == '0': break
        if not choice1.isdigit() or int(choice1) < 1 or int(choice1) > len(regions):
            print("無效輸入，請重新選擇。")
            continue
        
        selected_region = regions[int(choice1) - 1]

        # 第二層：選擇國家
        countries = list(geo_data[selected_region].keys())
        print(f"\n[第二層] {selected_region} -> 請選擇國家：")
        for i, country in enumerate(countries, 1):
            print(f"{i}. {country}")
        print("0. 回上層")

        choice2 = input("\n請輸入編號: ").strip()
        if choice2 == '0': continue
        if not choice2.isdigit() or int(choice2) < 1 or int(choice2) > len(countries):
            print("無效輸入，請重新選擇。")
            continue

        selected_country = countries[int(choice2) - 1]

        # 第三層：選擇城市
        cities = geo_data[selected_region][selected_country]
        print(f"\n[第三層] {selected_region} > {selected_country} -> 請選擇城市：")
        for i, city in enumerate(cities, 1):
            print(f"{i}. {city}")
        print(f"{len(cities) + 1}. 手動輸入其他城市名稱")
        print("0. 回上層")

        choice3 = input("\n請輸入編號: ").strip()
        if choice3 == '0': continue
        
        max_choice3 = len(cities) + 1
        if not choice3.isdigit() or int(choice3) < 1 or int(choice3) > max_choice3:
            print("無效輸入，請重新選擇。")
            continue

        target_city = ""
        idx = int(choice3) - 1
        if 0 <= idx < len(cities):
            target_city = cities[idx]
        elif idx == len(cities):
            target_city = input("請輸入城市英文名稱 (例如: Paris): ").strip()
        
        if target_city:
            print(f"\n正在查詢 {target_city} 的天氣預報...")
            forecast = weather_svc.get_daily_forecast(target_city)
            if forecast:
                # 預報表格標頭
                print(f"\n{target_city} 未來幾天的天氣預報:")
                print("日期        | 最低   | 最高   | 天氣描述")
                print("------------+--------+--------+----------------------------")
                for day in forecast:
                    date = day['date']
                    min_t = f"{day['min_temp']}°C"
                    max_t = f"{day['max_temp']}°C"
                    desc = day['description']
                    print(f"{date:12}| {min_t:6} | {max_t:6} | {desc}")

                # 顯示當日即時天氣與空氣品質（格式化）
                current = weather_svc.get_current_weather(target_city)
                if current:
                    try:
                        lat = current['coord']['lat']
                        lon = current['coord']['lon']
                        feels = current['main'].get('feels_like')
                        humidity = current['main'].get('humidity')
                        sunset_ts = current['sys'].get('sunset')
                        timezone_offset = current.get('timezone', 0)
                        if sunset_ts:
                            # 修正 Python 3.12+ 的 utcfromtimestamp 警告
                            sunset_local = datetime.fromtimestamp(sunset_ts, tz=timezone.utc).astimezone(timezone(timedelta(seconds=timezone_offset))).strftime('%H:%M')
                        else:
                            sunset_local = '未知'

                        print(f"\n{target_city} - 即時天氣：")
                        print("----------------------------------------")
                        if feels is not None:
                            print(f"體感溫度 : {round(feels,1)} °C")
                        if humidity is not None:
                            print(f"濕度     : {humidity} %")
                        print(f"日落時間 : {sunset_local}")
                        print("----------------------------------------")

                        # 空氣品質 (需要座標)
                        air = weather_svc.get_air_quality(lat, lon)
                        if air and 'list' in air and len(air['list']) > 0:
                            aq = air['list'][0]
                            aqi = aq.get('main', {}).get('aqi')
                            comps = aq.get('components', {})
                            print("\n空氣品質指標:")
                            print(f"AQI 等級 : {aqi} ({aqi_label(aqi)})")
                            print("污染物     | 濃度 (μg/m3)")
                            print("-----------+-------------------")
                            for k in ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co', 'nh3']:
                                if k in comps:
                                    name = component_ch_name(k)
                                    val = comps.get(k)
                                    # CO 的單位在 API 是 μg/m3，顯示時適度四捨五入
                                    if isinstance(val, float):
                                        val_str = f"{round(val,2)}"
                                    else:
                                        val_str = str(val)
                                    print(f"{name:9} | {val_str:>17}")
                            # 顯示健康建議
                            print("\n健康建議:")
                            print(aqi_health_advice(aqi))
                        else:
                            print("無法取得空氣品質資料。")
                    except Exception as e:
                        print(f"處理即時天氣/空氣品質時發生錯誤: {e}")
            else:
                print(f"無法獲取 {target_city} 的天氣資料。")
            
            input("\n按 Enter 鍵返回主選單...")

    print("感謝使用，再見！")

if __name__ == "__main__":
    main()