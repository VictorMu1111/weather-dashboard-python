import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

current_dir = Path(__file__).parent.resolve()
load_dotenv(dotenv_path=current_dir / '.env')


class AIWeatherService:
    """提供 AI 天氣分析、穿搭建議與互動對話的服務類別（支援 Gemini + DeepSeek 依使用者選擇切換）"""

    def __init__(self, gemini_api_key: Optional[str] = None, deepseek_api_key: Optional[str] = None, provider: str = "gemini"):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.provider = provider.lower()
        self.last_error = ""

    def build_weather_context(
        self,
        city_name: str,
        current_weather: Optional[Dict[str, Any]],
        forecast_data: Optional[List[Dict[str, Any]]],
        aqi_data: Optional[Dict[str, Any]]
    ) -> str:
        """將氣象數據整理為 AI 易於理解的 Markdown 格式 Context"""
        lines = [f"### 📍 城市：{city_name}"]

        if current_weather:
            main = current_weather.get('main', {})
            weather_desc = current_weather.get('weather', [{}])[0].get('description', '未知')
            lines.append("#### 【即時天氣】")
            lines.append(f"- 當前氣溫：{main.get('temp', '--')}°C (體感: {main.get('feels_like', '--')}°C)")
            lines.append(f"- 當前濕度：{main.get('humidity', '--')}%")
            lines.append(f"- 當前天氣狀況：{weather_desc}")

        if aqi_data and 'list' in aqi_data and len(aqi_data['list']) > 0:
            aq = aqi_data['list'][0]
            aqi = aq.get('main', {}).get('aqi', '未知')
            comps = aq.get('components', {})
            lines.append("#### 【空氣品質 (AQI)】")
            lines.append(f"- AQI 等級 (1優~5極差)：{aqi}")
            lines.append(f"- PM2.5: {comps.get('pm2_5', '--')} μg/m³, PM10: {comps.get('pm10', '--')} μg/m³")

        if forecast_data:
            lines.append("#### 【未來 5 天逐日預報】")
            for day in forecast_data:
                lines.append(
                    f"- **{day.get('date')}**：最低溫 {day.get('min_temp')}°C ~ 最高溫 {day.get('max_temp')}°C | "
                    f"降雨機率 {day.get('pop')}% | 天氣：{day.get('description')}"
                )

        return "\n".join(lines)

    def generate_weather_and_outfit_summary(
        self,
        city_name: str,
        current_weather: Optional[Dict[str, Any]],
        forecast_data: Optional[List[Dict[str, Any]]],
        aqi_data: Optional[Dict[str, Any]],
        style_preference: str = "通用日常"
    ) -> str:
        """生成未來 5 天的天氣總整理與穿搭建議（依照使用者選擇的 provider）"""
        self.last_error = ""
        context = self.build_weather_context(city_name, current_weather, forecast_data, aqi_data)

        if self.provider == "deepseek":
            if self.deepseek_api_key:
                ai_res = self._call_deepseek_summary(context, city_name, style_preference)
                if ai_res:
                    return ai_res
                self.last_error = f"[DeepSeek 失敗] {self.last_error}"
                print(f"DeepSeek 失敗，嘗試 Gemini。原因: {self.last_error}")
            if self.gemini_api_key:
                ai_res = self._call_gemini_summary(context, city_name, style_preference)
                if ai_res:
                    return ai_res
                self.last_error = f"[Gemini 也失敗] {self.last_error}"
                print(f"Gemini 也失敗，切換到規則引擎。原因: {self.last_error}")

        elif self.provider == "gemini":
            if self.gemini_api_key:
                ai_res = self._call_gemini_summary(context, city_name, style_preference)
                if ai_res:
                    return ai_res
                self.last_error = f"[Gemini 失敗] {self.last_error}"
                print(f"Gemini 失敗，嘗試 DeepSeek。原因: {self.last_error}")
            if self.deepseek_api_key:
                ai_res = self._call_deepseek_summary(context, city_name, style_preference)
                if ai_res:
                    return ai_res
                self.last_error = f"[DeepSeek 也失敗] {self.last_error}"
                print(f"DeepSeek 也失敗，切換到規則引擎。原因: {self.last_error}")

        else:
            self.last_error = "使用規則引擎模式（無 API Key）"

        return self._generate_fallback_summary(city_name, current_weather, forecast_data, aqi_data, style_preference)

    def chat_response(
        self,
        messages: List[Dict[str, str]],
        city_name: str,
        current_weather: Optional[Dict[str, Any]],
        forecast_data: Optional[List[Dict[str, Any]]],
        aqi_data: Optional[Dict[str, Any]],
        style_preference: str = "通用日常"
    ) -> str:
        """針對使用者的問題進行天氣與穿搭對話（依照使用者選擇的 provider）"""
        self.last_error = ""
        context = self.build_weather_context(city_name, current_weather, forecast_data, aqi_data)

        if self.provider == "deepseek":
            if self.deepseek_api_key:
                res = self._call_deepseek_chat(messages, context, city_name, style_preference)
                if res:
                    return res
                self.last_error = f"[DeepSeek 失敗] {self.last_error}"
                print(f"DeepSeek 失敗，嘗試 Gemini。原因: {self.last_error}")
            if self.gemini_api_key:
                res = self._call_gemini_chat(messages, context, city_name, style_preference)
                if res:
                    return res
                self.last_error = f"[Gemini 也失敗] {self.last_error}"
                print(f"Gemini 也失敗，切換到規則引擎。原因: {self.last_error}")

        elif self.provider == "gemini":
            if self.gemini_api_key:
                res = self._call_gemini_chat(messages, context, city_name, style_preference)
                if res:
                    return res
                self.last_error = f"[Gemini 失敗] {self.last_error}"
                print(f"Gemini 失敗，嘗試 DeepSeek。原因: {self.last_error}")
            if self.deepseek_api_key:
                res = self._call_deepseek_chat(messages, context, city_name, style_preference)
                if res:
                    return res
                self.last_error = f"[DeepSeek 也失敗] {self.last_error}"
                print(f"DeepSeek 也失敗，切換到規則引擎。原因: {self.last_error}")

        else:
            self.last_error = "使用規則引擎模式（無 API Key）"

        user_query = messages[-1]["content"] if messages else ""
        return self._generate_fallback_chat(user_query, city_name, forecast_data, aqi_data)

    # -------------------------------------------------------------
    # Gemini API 呼叫
    # -------------------------------------------------------------
    def _call_gemini_summary(self, weather_context: str, city_name: str, style_preference: str) -> Optional[str]:
        prompt = f"""
你是一位專業且具同理心的【天氣氣象分析師與時尚穿搭顧問】(AI Weather & Style Specialist)。
請根據以下提供的【{city_name}】即時天氣與未來預報數據，為使用者撰寫一份結構清晰、實用貼心的「未來 5 天氣象總評與穿搭指南」。
穿搭風格偏好：{style_preference}
請嚴格遵循以下 Markdown 結構進行輸出（使用豐富的 Emoji 與清晰的條列）：
## 🌤️ 【{city_name}】未來 5 天氣象總整理
- **氣溫趨勢與溫差**：分析整體氣溫走向、最高/最低溫區間、日夜溫差狀況。
- **晴雨與降水提醒**：點出哪幾天有較高降雨機率、何時放晴。
- **空氣品質與環境指數**：根據 AQI 提供呼吸道防護或戶外活動評估。
## 👔 智慧穿搭與造型指南 ({style_preference})
- **整體穿著原則**：（例如：多層次洋蔥式穿搭 / 清爽透氣防曬 / 防風保暖禦寒）
- **分段/逐日穿搭建議**：針對這 5 天中溫度或天氣有明顯轉折的天數給出具體單品建議（上衣、外套、褲/裙、鞋履）。
- **特殊防護單品**：（例如：防風外套、發熱衣、透氣麻料短袖等）
## 🎒 出行與隨身必備清單
- 🌂 **雨具建議**：是否需常備折疊傘或雨衣
- 🕶️ **防護與護膚**：防曬乳、遮陽帽、太陽眼鏡、保濕乳液等
- 😷 **健康口罩**：根據 AQI 評估是否需配戴醫療/防霾口罩
## 🏃 戶外活動與生活叮嚀
- 戶外慢跑/健行適宜天數、洗衣服曬被子最佳時機，以及生活上的溫馨小提醒。
---
以下為氣象數據：
{weather_context}
"""
        api_key = self.gemini_api_key.strip()
        models_to_try = [
            "gemini-3.7-flash",
            "gemini-2.5-flash"
        ]
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048
            }
        }
        for model in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                resp = requests.post(url, headers=headers, json=payload, timeout=3)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                else:
                    if resp.status_code in [429, 503]:
                        self.last_error = f"Google API ({model}) HTTP {resp.status_code}: 額度不足或服務不可用"
                        print(f"Gemini API ({model}) 回傳錯誤 [{resp.status_code}]，直接切換")
                        break
                    self.last_error = f"Google API ({model}) HTTP {resp.status_code}: {resp.text[:200]}"
                    print(f"Gemini API ({model}) 回傳錯誤 [{resp.status_code}]")
            except Exception as e:
                self.last_error = f"Gemini API ({model}) 連線異常: {e}"
                print(f"Gemini API 呼叫 ({model}) 連線異常: {e}")
                continue
        return None

    def _call_gemini_chat(self, messages: List[Dict[str, str]], weather_context: str, city_name: str, style_preference: str) -> Optional[str]:
        system_instruction = f"""你是一位貼心專業的 AI 天氣機器人與穿搭顧問。
你已經掌握 {city_name} 的即時與未來 5 天天氣/AQI 數據：
{weather_context}
使用者的風格偏好是：{style_preference}。
請用繁體中文、親切幽默且實用的口吻回答使用者的問題。回答需條理清晰，適當搭配 Emoji。"""
        api_key = self.gemini_api_key.strip()
        gemini_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            if not gemini_contents and role == "model":
                continue
            if gemini_contents and gemini_contents[-1]["role"] == role:
                gemini_contents[-1]["parts"][0]["text"] += "\n" + msg["content"]
            else:
                gemini_contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        if not gemini_contents:
            return None

        models_to_try = [
            "gemini-3.7-flash",
            "gemini-2.5-flash"
        ]
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024
            }
        }
        for model in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                resp = requests.post(url, headers=headers, json=payload, timeout=3)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                else:
                    if resp.status_code in [429, 503]:
                        self.last_error = f"Google API ({model}) HTTP {resp.status_code}: 額度不足或服務不可用"
                        print(f"Gemini Chat ({model}) 回傳錯誤 [{resp.status_code}]，直接切換")
                        break
                    self.last_error = f"Google API ({model}) HTTP {resp.status_code}: {resp.text[:200]}"
                    print(f"Gemini Chat ({model}) 回傳錯誤 [{resp.status_code}]")
            except Exception as e:
                self.last_error = f"Gemini Chat ({model}) 連線異常: {e}"
                print(f"Gemini Chat 呼叫 ({model}) 連線異常: {e}")
                continue
        return None

    # -------------------------------------------------------------
    # DeepSeek API 呼叫 (OpenAI 相容格式)
    # -------------------------------------------------------------
    def _call_deepseek_summary(self, weather_context: str, city_name: str, style_preference: str) -> Optional[str]:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_api_key.strip()}"
        }
        
        prompt = f"""
請根據以下【{city_name}】的天氣數據，提供未來 5 天氣象總整理與穿搭建議（偏好：{style_preference}）。
請以繁體中文撰寫，包含：
1. 🌤️ 未來 5 天氣候總評（溫差、晴雨趨勢、空氣品質）
2. 👔 智慧穿搭指南（分日或分段穿搭建議）
3. 🎒 隨身攜帶推薦（雨具、防曬、口罩）
4. 🏃 戶外活動與生活建議

氣象資料：
{weather_context}
"""
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一位專業貼心的氣象與時尚穿搭 AI 顧問。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                self.last_error = f"DeepSeek API HTTP {resp.status_code}: {resp.text[:200]}"
                print(f"DeepSeek API 回傳錯誤 [{resp.status_code}]")
        except Exception as e:
            self.last_error = f"DeepSeek API 連線異常: {e}"
            print(f"DeepSeek API 呼叫異常: {e}")
        
        return None

    def _call_deepseek_chat(self, messages: List[Dict[str, str]], weather_context: str, city_name: str, style_preference: str) -> Optional[str]:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_api_key.strip()}"
        }
        
        system_msg = {
            "role": "system",
            "content": f"你是一位貼心的 AI 天氣機器人與穿搭顧問。目前城市為 {city_name}，偏好風格為 {style_preference}。以下是當前氣象數據：\n{weather_context}\n請以繁體中文親切回答使用者的提問。"
        }
        
        chat_messages = [system_msg] + messages
        
        payload = {
            "model": "deepseek-chat",
            "messages": chat_messages,
            "temperature": 0.7
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                self.last_error = f"DeepSeek API HTTP {resp.status_code}: {resp.text[:200]}"
                print(f"DeepSeek API 回傳錯誤 [{resp.status_code}]")
        except Exception as e:
            self.last_error = f"DeepSeek API 連線異常: {e}"
            print(f"DeepSeek API 呼叫異常: {e}")
        
        return None

    # -------------------------------------------------------------
    # 智慧型規則引擎 (Fallback)
    # -------------------------------------------------------------
    def _generate_fallback_summary(
        self,
        city_name: str,
        current_weather: Optional[Dict[str, Any]],
        forecast_data: Optional[List[Dict[str, Any]]],
        aqi_data: Optional[Dict[str, Any]],
        style_preference: str
    ) -> str:
        if not forecast_data:
            return f"⚠️ 暫無足夠預報數據可為 {city_name} 產生 AI 穿搭建議。"

        all_mins = [d['min_temp'] for d in forecast_data]
        all_maxs = [d['max_temp'] for d in forecast_data]
        overall_min = min(all_mins)
        overall_max = max(all_maxs)
        avg_temp = (sum(all_mins) + sum(all_maxs)) / (len(all_mins) * 2)
        rainy_days = [d['date'] for d in forecast_data if d.get('pop', 0) >= 40]
        max_pop = max([d.get('pop', 0) for d in forecast_data])

        temp_range = overall_max - overall_min
        if temp_range >= 10:
            diff_text = f"🚨 **日夜溫差與氣溫起伏較大（{overall_min}°C ~ {overall_max}°C，溫差達 {temp_range}°C）**，務必注意洋蔥式穿法，早晚保暖。"
        elif temp_range >= 6:
            diff_text = f"🌡️ **氣溫介於 {overall_min}°C 至 {overall_max}°C 之間**，體感舒適但早晚微涼。"
        else:
            diff_text = f"🌡️ **氣溫相對穩定（約 {overall_min}°C ~ {overall_max}°C）**，氣候變化平緩。"

        if rainy_days:
            rain_text = f"🌧️ **降雨提醒**：預計在 **{', '.join(rainy_days)}** 降雨機率較高 (最高達 {max_pop}%)，出門務必攜帶雨具。"
        else:
            rain_text = f"☀️ **晴朗乾燥**：未來 5 天整體降雨機率低 (最高僅 {max_pop}%)，適合外出與戶外活動。"

        aqi_text = "🌿 **空氣品質**：良好，適合各類戶外運動。"
        need_mask = False
        if aqi_data and 'list' in aqi_data and len(aqi_data['list']) > 0:
            aqi = aqi_data['list'][0].get('main', {}).get('aqi', 1)
            if aqi >= 4:
                aqi_text = "😷 **空氣品質警報**：AQI 達不良/極差等級，敏感族群應避免戶外劇烈運動，建議配戴口罩。"
                need_mask = True
            elif aqi == 3:
                aqi_text = "🟡 **空氣品質普通**：呼吸道敏感族群外出時建議備好防護口罩。"

        if avg_temp < 10:
            layering = "🧥 **極致保暖防風型**：發熱衣 + 厚毛衣/刷毛衛衣 + 羽絨大衣/防風防潑水厚外套 + 發熱褲與保暖長褲。"
            shoes = "🥾 保暖厚襪、防滑靴或皮鞋。"
            gear = "🧤 圍巾、手套、毛帽、保濕護唇膏。"
        elif avg_temp < 18:
            layering = "🧥 **洋蔥式層次穿搭**：長袖棉 T/襯衫 + 針織衫/帽 T + 風衣/夾克/羽絨背心（方便進出室內穿脫）。"
            shoes = "👟 休閒球鞋、透氣皮鞋或短靴。"
            gear = "🧣 薄圍巾或輕便外套。"
        elif avg_temp < 26:
            layering = "👕 **舒適休閒/商務**：短袖 T-shirt、棉麻襯衫或薄長袖，搭配休閒長褲或九分褲；早晚可搭一件薄防曬/防風外套。"
            shoes = "👟 透氣運動鞋、休閒帆布鞋。"
            gear = "🕶️ 太陽眼鏡、輕量防曬外套。"
        else:
            layering = "🎽 **清爽透氣防暑**：吸濕排汗短袖、無袖背心、亞麻短褲或涼感長褲，以淺色系為主以防吸熱。"
            shoes = "🩴 涼鞋、透氣網布慢跑鞋。"
            gear = "🧴 防曬乳、遮陽帽、太陽眼鏡、足量飲用水。"

        daily_recommendations = []
        for d in forecast_data:
            day_avg = (d['min_temp'] + d['max_temp']) / 2
            day_pop = d.get('pop', 0)
            if day_avg < 15:
                day_outfit = "長袖保暖衣物 + 外套"
            elif day_avg < 24:
                day_outfit = "薄長袖或短袖 + 薄外套"
            else:
                day_outfit = "清涼短袖、透氣下身"
            if day_pop >= 40:
                day_outfit += " ＋ 帶傘/防水鞋"
            daily_recommendations.append(f"- **{d['date']}** ({d['min_temp']}°C ~ {d['max_temp']}°C，降雨 {day_pop}%)：{day_outfit}")
        daily_section = "\n".join(daily_recommendations)

        return f"""
> 💡 *小提示：目前為智慧規則生成模式。若配置 Gemini 或 DeepSeek API Key，AI 機器人將提供更具個人化與時尚細節的建議！*
## 🌤️ 【{city_name}】未來 5 天氣象總評
- {diff_text}
- {rain_text}
- {aqi_text}
---
## 👔 智慧穿搭指南 (風格：{style_preference})
- **整體穿著原則**：
{layering}
- **推薦鞋履搭配**：
{shoes}
- **逐日建議快覽**：
{daily_section}
---
## 🎒 出行隨身必備
- 🌂 **雨具**：{'建議常備折疊傘 ☔' if max_pop >= 30 else '天氣相對穩定，可視當天降雨率準備'}
- 🕶️ **防護裝備**：{'遮陽帽、太陽眼鏡與高係數防曬' if overall_max >= 25 else '保濕乳液、護唇膏'}
- 😷 **口罩防護**：{'出門必備醫療/防霾口罩 😷' if need_mask else '依個人體質彈性配戴'}
---
## 🏃 戶外活動與生活建議
- **洗曬衣物**：{'避開雨天，建議在晴朗無雨的日子曬被洗衣服 🧺' if rainy_days else '陽光充足，未來幾天均適合洗曬衣物 🧺'}
- **運動指南**：{'戶外路跑適宜，注意補水 🏃‍♂️' if not rainy_days and not need_mask else '天雨路滑或空氣欠佳時，建議轉為室內健身房運動 🏋️'}
"""

    def _generate_fallback_chat(self, user_query: str, city_name: str, forecast_data: Optional[List[Dict[str, Any]]], aqi_data: Optional[Dict[str, Any]]) -> str:
        q = user_query.lower()

        if "傘" in q or "雨" in q or "rain" in q or "umbrella" in q:
            if forecast_data:
                rain_days = [f"{d['date']}(降雨率{d['pop']}%)" for d in forecast_data if d.get('pop', 0) >= 30]
                if rain_days:
                    return f"☔ 根據 {city_name} 的預報，以下幾天降雨機率較高，出門記得帶傘喔：\n" + "\n".join([f"- {r}" for r in rain_days])
                else:
                    return f"☀️ {city_name} 未來 5 天降雨機率都在 30% 以下，基本上不需要太擔心下雨，但隨身帶把輕便折傘以備不時之需也很安心！"
            return f"📍 目前暫無 {city_name} 的詳細降雨資料。"

        if "穿" in q or "衣服" in q or "外套" in q or "褲" in q or "wear" in q or "outfit" in q:
            if forecast_data:
                first_day = forecast_data[0]
                return f"👔 針對 {city_name} 的氣候（近期約 {first_day['min_temp']}°C ~ {first_day['max_temp']}°C），建議採用多層次穿法。早晚可備一件輕便外套，搭配透氣舒適的內搭，方便隨氣溫調節！"
            return "👔 建議依據早晚溫差準備好外套與透氣內搭。"

        if "跑" in q or "運動" in q or "戶外" in q:
            return f"🏃 建議觀察 {city_name} 降雨率較低且氣溫適中的時段外出運動。如果 AQI 空氣品質普通或不良，也可以考慮室內伸展或健身！"

        return f"🤖 我是 {city_name} 的天氣與穿搭小助理！您可以詢問我關於「哪天要帶傘？」、「某天的穿搭推薦」、「適不適合戶外運動」或「洗曬衣物時機」等問題喔！"