import streamlit as st
import streamlit.components.v1 as components

st.title("BTCUSDT Chart with Indicators")

tradingview_html = """
<div id="tradingview_widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script type="text/javascript">
new TradingView.widget({
  "container_id": "tradingview_widget",
  "width": "100%",
  "height": 600,
  "symbol": "BINANCE:BTCUSDT",
  "interval": "1",
  "timezone": "Asia/Kolkata",
  "theme": "dark",
  "style": "1",
  "toolbar_bg": "#f1f3f6",
  "hide_side_toolbar": false,
  "studies": [
    "Supertrend",
    "RSI@tv-basicstudies"
  ]
});
</script>
"""

components.html(tradingview_html, height=650, scrolling=True)
