import requests
from bs4 import BeautifulSoup
import yfinance as yf
import os
import pandas as pd

# 설정 정보 (GitHub Secrets에서 가져옴)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 감시 키워드 (가이드님 맞춤형)
MY_KEYWORDS = ["공급계약", "사상 최대", "흑자전환", "수주", "M&A", "세계 최초"]

def get_all_stocks():
    try:
        url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
        df = pd.read_html(url, header=0, encoding='cp949')[0]
        return dict(zip(df['회사명'], df['종목코드'].apply(lambda x: str(x).zfill(6))))
    except: return {}

def send_telegram(title, link, reason, stock_info=None):
    try:
        if stock_info:
            name, price, code = stock_info
            f_url = f"https://finance.naver.com/item/main.naver?code={code}"
            c_url = f"https://ssl.pstatic.net/imgstock/chart/item/area/day/{code}.png"
            cap = f"🔍 종목 포착: {name}\n💰 현재가: {int(price):,}원\n\n📰 {title}\n\n🔗 [뉴스]({link}) | [상세]({f_url})"
            requests.get(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", params={"chat_id": CHAT_ID, "photo": c_url, "caption": cap, "parse_mode": "Markdown"})
        else:
            cap = f"🌟 [키워드 포착: {reason}]\n\n📰 {title}\n\n🔗 [뉴스]({link})"
            requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={"chat_id": CHAT_ID, "text": cap, "parse_mode": "Markdown"})
    except: pass

def run():
    url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=101"
    headers = {'User-Agent': 'Mozilla/5.0'}
    soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html.parser')
    stocks = get_all_stocks()
    sorted_stock_names = sorted(stocks.keys(), key=len, reverse=True)

    for a in soup.select('ul.type06_headline li dl dt:not(.photo) a'):
        title = a.get_text().strip()
        link = a['href']
        
        matched_stock = next((n for n in sorted_stock_names if n in title and len(n) > 1), None)
        if matched_stock:
            code = stocks[matched_stock]
            try:
                price = yf.Ticker(code + ".KS").history(period="1d")['Close'].iloc[-1]
                send_telegram(title, link, "종목", [matched_stock, price, code])
            except: pass
        else:
            matched_key = next((k for k in MY_KEYWORDS if k in title), None)
            if matched_key:
                send_telegram(title, link, matched_key)

if __name__ == "__main__":
    run()
