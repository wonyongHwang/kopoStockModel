# -----------------------------------------------------------------
#    Author: 최성운
#    Created: 2021.06.17
#    Description:
#    S&P500 섹터별 저평가주식을 RSI기법으로 매매. 
#    RSI 지표란 일정 기간 동안 주가가 전일 가격에 비해 상승한 변화량과 하락한 변화량의 
#    평균값을 구하여,상승한 변화량이 크면 과매수로, 하락한 변화량이 크면 과매도로 판단하는 방식.
#    RSI가  70 이상이면 과열상태로 판단하여 매도시점이 되고,
#    반대로 30 이하일 경우 매수시점이 된다.
#    매수와 매도 추천 시점을 표기하여 투자에 도움을 주도록 설계함.
# -----------------------------------------------------------------

import matplotlib as matplotlib
import pandas as pd
import urllib.parse
from bs4 import BeautifulSoup
import FinanceDataReader as fdr
from datetime import date, timedelta
import matplotlib.pyplot as plt
import datetime
import platform
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import json
import re
from urllib.parse import parse_qs
from urllib.parse import urlparse
import threading
import requests


PORT_NUMBER = 8666



#S&P500 평균 PER
def spxPer(url):
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:71.0) Gecko/20100101 Firefox/71.0'}
    r = requests.get(url, headers=header)
    spx_per_dfs = pd.read_html(r.text)
    return float(list(spx_per_dfs[0].iloc[0])[1][0:5])

#S&P500 평균 PBR
def spxPbr(url):
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:71.0) Gecko/20100101 Firefox/71.0'}
    r = requests.get(url, headers=header)
    spx_pbr_dfs = pd.read_html(r.text)
    return float(list(spx_pbr_dfs[0].iloc[0])[1][0:5])


#S&P IT 섹터 가져오기
def getITSector (df):
    sector_list=list(df.drop_duplicates(subset='Sector')['Sector'])
    return sector_list[2]


#S&P500의 IT 섹터 종목들을 가져옴
def getStockList(df):
    it_sector = getITSector(df)
    spx_cnt = len(df)
    spx_list = []
    for i in range(0, spx_cnt):
        if (df.iloc[i]['Sector']== it_sector):
            spx_list.append(df.loc[i])
    return pd.DataFrame(spx_list).reset_index(drop = True)



# 섹터에서 저평가 주식 목록 가져오기
def ticker (df):
    df_cnt = len(df)
    ticker_list = []
    for i in range(0, df_cnt):
        it_ticker = df.iloc[i]['Symbol']
        ticker_list.append(it_ticker)
    return ticker_list



# 저평가 가치주
# PER <= 10; 10년 기다리면 현재 주식의 가격만큼 돈을 범
# ROE >= 10; 수익성이 너무 낮으면 주식의 가격에 호재가 별로없는 소외된 없종
# PBR <= 1; 주당순자산가치보다 주가가 낮다는 것은 바닥에 근접, PBR 1로 오를 확률이 높음
# 시장이 너무 과열되어 저평가 주식이 없음
# S&P500 평균 PER, PBR 보다 작은 종목 가져옴
def spxUnderValued (url, url2, ticker_list):
    uv_stock = []
    lenList = len(ticker_list)
    spx_per = spxPer(url)
    spx_pbr = spxPbr(url2)
    for i in range (0, lenList):
        it_ticker = ticker_list[i]
        url = 'https://finviz.com/quote.ashx?t='+ it_ticker
        header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:71.0) Gecko/20100101 Firefox/71.0'}
        r = requests.get(url, headers=header)
        dfs = pd.read_html(r.text)
        stock_info = (dfs[5])
        stock_per = stock_info.iloc[0,3]
        stock_pbr = stock_info.iloc[4,3]
        stock_roe = stock_info.iloc[5,7][0:4]
        if stock_per == '-':
            continue
        elif stock_pbr == '-':
            continue
        elif stock_roe == '-':
            continue
        else:
            per_value = float(stock_per)
            pbr_value = float(stock_pbr)
            roe_value = float(stock_roe)
        if (per_value <= spx_per and pbr_value <= spx_pbr and roe_value >= 15):
            uv_stock.append(it_ticker)
        else:
            continue
        return uv_stock


## RSI 매매기법


#단순 이동 평균 (Simple Moving Average, SMA)
def SMA(df, period, column):
     return df[column].rolling(window=period).mean()

# RSI
# 1. RS / (1 + RS)
# 2. AU / (AU + AD)
# 주식의 가격이 전일보다 오늘 상승했다면 상승한 양은 U.
# 주식의 가격이 전일보다 오늘 하락했다면 하락한 양은 D.
# U 와 D 의 평균 = AU, AD
# AU / AD = RS
# 70 이상 매도
# 30 이하 매수
def RSI(df, period, column = 'Close'):
    U = np.where(df[column].diff(1) > 0, df[column].diff(1), 0)
    D = np.where(df[column].diff(1) < 0, df[column].diff(1) *(-1), 0)
    df['up'] = U
    df['down'] = D
    AU = SMA(df, period, 'up')
    AD = abs(SMA(df, period, 'down'))
    RS = AU / AD
    RSI = (RS / (1 + RS))*100
    return RSI

# 매매 날짜 정의
def tradingDate (number, stock_ticker):
    end = date.today()
    start = date.today() - timedelta(number)
    STOCK = fdr.DataReader(stock_ticker, start, end)
    return STOCK

#단순 이동 평균선 & 종가 차트
#RSI 차트
def plotChart (number, df):
    end = date.today()
    start = date.today() - timedelta(number)
    plt.figure(figsize=(12.4, 6.4))
    plt.subplot(2,1,1)
    y1 = df['SMA']
    y2 = df['Close']
    x = df['Date']
    plt.plot(x, y1)
    plt.plot(x, y2)
    plt.subplot(2,1,2)
    y3 = df['RSI']
    plt.plot(x, y3)
    plt.xlim(start, end)
    plt.show()

#매매 출력 함수
#RSI <= 40 : 1개의 주식을 삼
#RSI <= 30 : 2주식을 삼
#RSI >= 70 : 보유한 주식 모두 판매

def tradeStock (number, df, uv_list):
    deposit = number #예수금
    profit = 0 #수익
    balance = 0 #사용한 금액
    cnt = 0  #보유한 주식 수
    # 저평가 종목에 동등하게 분산투자
    invest_fund = round((deposit / len(uv_list)), 2)
    for i in range (0, len(df)):
        open_price = df["Open"][i]
        high_price = df["High"][i]
        low_price = df["Low"][i]
        trade_date = str(df["Date"][i])[0:10]
        avg_adj_price = ((open_price + high_price + low_price) / 3).round(2) #일일 평균 주가
        if ((df["RSI"][i] <= 30) & (invest_fund > avg_adj_price)) :
            invest_fund -= (avg_adj_price * 2)
            balance += (avg_adj_price * 2)
            cnt+=2
            print("")
            print(trade_date)
            print("buy 2")
            print("total stock:",cnt)
            print("price:",avg_adj_price)
            print("buying total:",(avg_adj_price*2))
            print("invest_fund:",(invest_fund).round(2))
            print("balance:",(balance).round(2))
        elif ((df["RSI"][i] <= 40) & (invest_fund > avg_adj_price)) :
            invest_fund -= (avg_adj_price)
            balance += (avg_adj_price)
            cnt+=1
            print("")
            print(trade_date)
            print("buy")
            print("total stock:",cnt)
            print("price:", avg_adj_price)
            print("invest_fund", (invest_fund).round(2))
            print("balance:", (balance).round(2))
        elif (df["RSI"][i] >= 70) & (balance > 0) :
            profit = (avg_adj_price * cnt) - balance
            invest_fund += balance
            cnt -= cnt
            balance -= balance
            print("")
            print(trade_date)
            print("sell all stock")
            print("total stock:", cnt)
            print("price:", avg_adj_price)
            print("invest_fund", (invest_fund).round(2))
            print("balance:", (balance).round(2))
            print("profit:$", (profit).round(2))
    return



# This class will handle any incoming request from
# a browser
class myHandler(BaseHTTPRequestHandler):

    #def __init__(self, request, client_address, server):
    #    BaseHTTPRequestHandler.__init__(self, request, client_address, server)
    # Handler for the GET requests
    def do_GET(self):
        data = []  # response json data
        if None != re.search('/stock/*', self.path):
            if None != re.search('/stock/trade', self.path):
                try:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()

                    try:
                        url = 'https://www.multpl.com/s-p-500-pe-ratio/table/by-year'
                        url2 = 'https://www.multpl.com/s-p-500-price-to-book/table/by-year'
                        # S&P 500 종목 전체
                        df_spx = fdr.StockListing('S&P500')
                        spx_it_df = getStockList(df_spx)
                        spx_it_ticker = ticker(spx_it_df)
                        print("getting undervalued stocks from the sector")
                        #해외 사이트에서 저평가 주식 정보를 가져오는 시간이 너무 오래 걸림
                        under_it = spxUnderValued(url, url2, spx_it_ticker)
                        if(len(under_it) > 0):
                            # for i in range(0, len(under_it)):
                            stock_ticker = under_it[0]
                            print(stock_ticker)
                            STOCK = tradingDate(120, under_it[0])
                            STOCK["Date"] = STOCK.index
                            STOCK["SMA"] = SMA(STOCK, period=14, column='Close')
                            STOCK["RSI"] = RSI(STOCK, period=14)
                            plotChart(100, STOCK)
                            tradeStock(100000, STOCK, under_it)
                            data.append("trade complete")
                            self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))
                        else:
                            print("NO TICKER FOUND")
                            data.append("NO TICKER FOUND")
                            self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

                    except:
                        print("error")
                        data.append("error")
                        self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

                except:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    data.append("internal server error")

        else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data.append("{info:no such api}")
                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))



# class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
#     """Handle requests in a separate thread."""



try:

    # Create a web server and define the handler to manage the
    # incoming request
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    # server = ThreadedHTTPServer(('', PORT_NUMBER), myHandler)
    print('Started httpserver on port ', PORT_NUMBER)
    # Wait forever for incoming http requests
    server.serve_forever()

except (KeyboardInterrupt, Exception) as e:
    print('^C received, shutting down the web server')
    print(e)
    server.socket.close()