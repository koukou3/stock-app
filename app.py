import streamlit as st
import yfinance as yf
import pandas as pd
import time
import warnings
from datetime import datetime

# ページ設定（iPhoneで見やすいようにワイドモードに）
st.set_page_config(page_title="Ultimate Stock Screener", page_icon="📈")

# タイトルと説明
st.title("📈 アルティメット・スクリーナー")
st.caption("対象：日経225＋JPX400＋プライム・スタンダード主力（約580銘柄）")

# --- ロジック部分（既存のロジックを統合） ---
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def check_ultimate_swing(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        df_daily = ticker.history(period="1y", interval="1d")
        if df_daily.empty or len(df_daily) < 75:
            return False, "データ不足", None, None, None
            
        df_daily['5MA'] = df_daily['Close'].rolling(window=5).mean()
        df_daily['20MA'] = df_daily['Close'].rolling(window=20).mean()
        df_daily['75MA'] = df_daily['Close'].rolling(window=75).mean()
        df_daily['RSI'] = calculate_rsi(df_daily)
        df_daily['20MA_Dev'] = (df_daily['Close'] - df_daily['20MA']) / df_daily['20MA'] * 100
        df_daily['Vol_Avg'] = df_daily['Volume'].rolling(window=20).mean()
        
        last_trading_value = df_daily['Close'].iloc[-1] * df_daily['Volume'].iloc[-1]
        std = df_daily['Close'].rolling(window=20).std()
        df_daily['Upper_2sigma'] = df_daily['20MA'] + (std * 2)
        
        last = df_daily.iloc[-1]
        prev = df_daily.iloc[-2]
        
        trend_daily = (last['Close'] > last['5MA'] > last['20MA']) and (last['Close'] > last['75MA'])
        candle_ok = (last['Close'] > last['Open']) or ((prev['Close'] > prev['Open']) and (last['Open'] > prev['Close']))
        vol_ok = last['Volume'] > last['Vol_Avg']
        rsi_safe = last['RSI'] < 75
        dev_safe = last['20MA_Dev'] < 10
        bb_safe = last['Close'] < last['Upper_2sigma']

        df_weekly = ticker.history(period="1y", interval="1wk")
        if df_weekly.empty or len(df_weekly) < 20: return False, "週足不足", None, None, None
        last_w = df_weekly.iloc[-1]
        df_weekly['5MA'] = df_weekly['Close'].rolling(window=5).mean()
        df_weekly['20MA'] = df_weekly['Close'].rolling(window=20).mean()
        trend_weekly = (last_w['Close'] > df_weekly['5MA'].iloc[-1] > df_weekly['20MA'].iloc[-1])

        if not (trend_daily and trend_weekly): return False, "トレンド未達", None, None, None
        if last_trading_value < 1000000000: return False, "流動性不足", None, None, None
        if not candle_ok: return False, "形状不適合", None, None, None
        if not vol_ok: return False, "活況不足", None, None, None
        if not (rsi_safe and dev_safe and bb_safe): return False, "過熱/乖離過大", None, None, None

        info_data = ticker.info
        name = info_data.get('shortName') or '不明'
        sector = info_data.get('sector') or '不明'
        
        earnings_date = "不明"
        try:
            cal = ticker.calendar
            if isinstance(cal, dict) and 'Earnings Date' in cal:
                earnings_date = cal['Earnings Date'][0].strftime('%Y/%m/%d')
        except: pass
            
        return True, f"{last['Close']:,.0f}円", name, sector, earnings_date
    except:
        return False, "エラー", None, None, None

# --- UI部分 ---
# 母集団：日経225 + JPX400 + プライム・スタンダード主力（全約580銘柄）
tickers = sorted(list(set([
    "1332.T", "1414.T", "1605.T", "1719.T", "1720.T", "1721.T", "1801.T", "1802.T", "1803.T", "1808.T",
    "1812.T", "1820.T", "1821.T", "1860.T", "1861.T", "1878.T", "1893.T", "1911.T", "1925.T", "1928.T",
    "1941.T", "1942.T", "1944.T", "1951.T", "1959.T", "2002.T", "2127.T", "2148.T", "2154.T", "2158.T",
    "2160.T", "2175.T", "2181.T", "2201.T", "2212.T", "2229.T", "2264.T", "2267.T", "2269.T", "2282.T",
    "2331.T", "2353.T", "2371.T", "2379.T", "2413.T", "2432.T", "2501.T", "2502.T", "2503.T", "2531.T",
    "2587.T", "2651.T", "2670.T", "2681.T", "2702.T", "2768.T", "2784.T", "2801.T", "2802.T", "2809.T",
    "2811.T", "2871.T", "2875.T", "2897.T", "2914.T", "2980.T", "3003.T", "3038.T", "3064.T", "3086.T",
    "3092.T", "3099.T", "3107.T", "3116.T", "3132.T", "3133.T", "3141.T", "3182.T", "3197.T", "3231.T",
    "3288.T", "3289.T", "3291.T", "3349.T", "3382.T", "3391.T", "3401.T", "3402.T", "3405.T", "3407.T",
    "3436.T", "3498.T", "3549.T", "3563.T", "3659.T", "3660.T", "3697.T", "3762.T", "3769.T", "3778.T",
    "3861.T", "3863.T", "3902.T", "3923.T", "3941.T", "3993.T", "3994.T", "4004.T", "4005.T", "4021.T",
    "4042.T", "4043.T", "4061.T", "4063.T", "4088.T", "4091.T", "4114.T", "4151.T", "4165.T", "4183.T",
    "4185.T", "4188.T", "4194.T", "4204.T", "4208.T", "4307.T", "4324.T", "4385.T", "4443.T", "4452.T",
    "4475.T", "4478.T", "4485.T", "4502.T", "4503.T", "4506.T", "4507.T", "4516.T", "4519.T", "4523.T",
    "4527.T", "4528.T", "4536.T", "4543.T", "4565.T", "4568.T", "4578.T", "4592.T", "4612.T", "4631.T",
    "4661.T", "4665.T", "4666.T", "4684.T", "4689.T", "4704.T", "4716.T", "4732.T", "4736.T", "4739.T",
    "4751.T", "4755.T", "4768.T", "4816.T", "4901.T", "4902.T", "4911.T", "4912.T", "4922.T", "4927.T",
    "5019.T", "5020.T", "5032.T", "5101.T", "5105.T", "5108.T", "5201.T", "5202.T", "5214.T", "5232.T",
    "5233.T", "5253.T", "5301.T", "5332.T", "5333.T", "5401.T", "5406.T", "5411.T", "5486.T", "5541.T",
    "5574.T", "5582.T", "5586.T", "5595.T", "5631.T", "5703.T", "5706.T", "5711.T", "5713.T", "5714.T",
    "5726.T", "5802.T", "5803.T", "5831.T", "5844.T", "5901.T", "5929.T", "5938.T", "5947.T", "5991.T",
    "6005.T", "6027.T", "6028.T", "6098.T", "6103.T", "6113.T", "6118.T", "6141.T", "6146.T", "6181.T",
    "6201.T", "6254.T", "6268.T", "6273.T", "6301.T", "6302.T", "6305.T", "6324.T", "6326.T", "6361.T",
    "6367.T", "6383.T", "6395.T", "6407.T", "6412.T", "6436.T", "6448.T", "6460.T", "6471.T", "6472.T",
    "6473.T", "6479.T", "6481.T", "6490.T", "6501.T", "6503.T", "6504.T", "6506.T", "6525.T", "6526.T",
    "6532.T", "6573.T", "6586.T", "6594.T", "6613.T", "6619.T", "6645.T", "6701.T", "6702.T", "6723.T",
    "6724.T", "6728.T", "6752.T", "6753.T", "6758.T", "6762.T", "6770.T", "6841.T", "6857.T", "6861.T",
    "6869.T", "6890.T", "6902.T", "6920.T", "6927.T", "6952.T", "6954.T", "6965.T", "6971.T", "6976.T",
    "6981.T", "6988.T", "7003.T", "7004.T", "7011.T", "7012.T", "7013.T", "7014.T", "7163.T", "7180.T",
    "7182.T", "7186.T", "7201.T", "7202.T", "7203.T", "7205.T", "7211.T", "7239.T", "7240.T", "7259.T",
    "7261.T", "7267.T", "7269.T", "7270.T", "7272.T", "7282.T", "7309.T", "7379.T", "7453.T", "7459.T",
    "7518.T", "7532.T", "7564.T", "7701.T", "7731.T", "7732.T", "7733.T", "7735.T", "7741.T", "7747.T",
    "7751.T", "7752.T", "7762.T", "7780.T", "7794.T", "7832.T", "7911.T", "7912.T", "7936.T", "7951.T",
    "7974.T", "8001.T", "8002.T", "8015.T", "8031.T", "8035.T", "8053.T", "8058.T", "8113.T", "8136.T",
    "8227.T", "8233.T", "8252.T", "8267.T", "8282.T", "8304.T", "8306.T", "8308.T", "8309.T", "8316.T",
    "8331.T", "8354.T", "8355.T", "8359.T", "8382.T", "8411.T", "8473.T", "8591.T", "8593.T", "8601.T",
    "8604.T", "8628.T", "8630.T", "8697.T", "8725.T", "8750.T", "8766.T", "8795.T", "8801.T", "8802.T",
    "8804.T", "8830.T", "8876.T", "8905.T", "8919.T", "9001.T", "9005.T", "9007.T", "9008.T", "9009.T",
    "9020.T", "9021.T", "9022.T", "9064.T", "9065.T", "9069.T", "9101.T", "9104.T", "9107.T", "9110.T",
    "9142.T", "9143.T", "9166.T", "9201.T", "9202.T", "9227.T", "9301.T", "9404.T", "9432.T", "9433.T",
    "9434.T", "9501.T", "9502.T", "9503.T", "9506.T", "9508.T", "9509.T", "9531.T", "9532.T", "9552.T",
    "9602.T", "9613.T", "9627.T", "9684.T", "9697.T", "9719.T", "9735.T", "9766.T", "9843.T", "9962.T",
    "9983.T", "9984.T", "9989.T",
    
    # --- 追加銘柄（人気中小型株・グロース・スタンダード主力） ---
    "2698.T", "2782.T", "3053.T", "3196.T", "3397.T", "3543.T", "7550.T", "7616.T", "8200.T", "9873.T",
    "9861.T", "9842.T", "7421.T", "7522.T", "7581.T", "7649.T", "9936.T", "9948.T", "9279.T", "3561.T",
    "3632.T", "3656.T", "3765.T", "3903.T", "3904.T", "3922.T", "3932.T", "3962.T", "3983.T", "3989.T",
    "4308.T", "4436.T", "4442.T", "4449.T", "4477.T", "4483.T", "4488.T", "4393.T", "3911.T", "3914.T",
    "3926.T", "4051.T", "4053.T", "4056.T", "4176.T", "4180.T", "9553.T", "9211.T", "9212.T", "9229.T",
    "4890.T", "5125.T", "5129.T", "5132.T", "5240.T", "6140.T", "6166.T", "6232.T", "6255.T", "6298.T",
    "6315.T", "6323.T", "6425.T", "6590.T", "6614.T", "6627.T", "6630.T", "6658.T", "6668.T", "6787.T",
    "6814.T", "6855.T", "6871.T", "6966.T", "6999.T", "7729.T", "7730.T", "7769.T", "7775.T", "7868.T",
    "7944.T", "2337.T", "2412.T", "2427.T", "2471.T", "2492.T", "2882.T", "2929.T", "2931.T", "3048.T",
    "3088.T", "3134.T", "3186.T", "3193.T", "3222.T", "3232.T", "3254.T", "3276.T", "3284.T", "3328.T",
    "3431.T", "3465.T", "3482.T", "3489.T", "3539.T", "3673.T", "3681.T", "3774.T", "3834.T", "3853.T",
    "3920.T", "3939.T", "4293.T", "4344.T", "4348.T", "4369.T", "4651.T", "4674.T", "4686.T", "4694.T",
    "4722.T", "4733.T", "4745.T", "4763.T", "4828.T", "4849.T", "4974.T", "4980.T", "5949.T", "5988.T",
    "6035.T", "6036.T", "6058.T", "6080.T", "6095.T"
])))
if st.button('🔍 スキャン開始', type='primary'):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, code in enumerate(tickers):
        progress = (i + 1) / len(tickers)
        progress_bar.progress(progress)
        status_text.text(f"分析中: {code} ({i+1}/{len(tickers)})")
        
        is_match, price, name, sector, e_date = check_ultimate_swing(code)
        if is_match:
            results.append({
                "コード": code,
                "銘柄名": name,
                "セクター": sector,
                "終値": price,
                "決算予定": e_date
            })
            
    status_text.text("✅ スキャン完了！")
    
    if results:
        st.success(f"お宝銘柄が {len(results)} 件見つかりました！")
        df_res = pd.DataFrame(results)
        st.dataframe(df_res, use_container_width=True)
        
        # CSVダウンロード機能
        csv = df_res.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 結果をCSVで保存", csv, "scan_result.csv", "text/csv")
    else:
        st.info("条件に一致する銘柄はありませんでした。")
