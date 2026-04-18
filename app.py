import streamlit as st
import yfinance as yf

st.title("🛠️ クラウドデータ調査ツール")
st.write("Macとクラウドで何がズレているのか、中身を直接覗き見します！")

# Macでヒットした銘柄を入力してもらう
ticker_input = st.text_input("Macのターミナルで ⭐マーク（合格） がついた銘柄コードを入れてください (例: 9602.T)", value="9602.T")

if st.button("生データを確認する"):
    try:
        ticker = yf.Ticker(ticker_input)
        # 直近1ヶ月のデータを取得
        df = ticker.history(period="1mo", interval="1d")
        
        if df.empty:
            st.error("データが空っぽです！Yahoo Financeに通信を弾かれています。")
        else:
            st.success("データ取得成功！クラウドは以下のデータを見ています。")
            
            # 直近5日分のデータを新しい順に表示
            st.write(f"### {ticker_input} の直近5日間の生データ")
            
            # 見やすいように列を絞る
            display_df = df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(5).sort_index(ascending=False)
            
            # 日付だけを綺麗に表示
            display_df.index = display_df.index.strftime('%Y-%m-%d')
            st.dataframe(display_df, use_container_width=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
