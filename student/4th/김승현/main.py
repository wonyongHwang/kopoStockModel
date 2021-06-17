import pandas as pd
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
# import matplotlib.pyplot as plt
from fbprophet import Prophet
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import FinanceDataReader as web
from datetime import date, timedelta
import matplotlib.pyplot as plt, pylab
import numpy as np
import urllib.parse
import numpy as np
from matplotlib import font_manager, rc
import re
import warnings
warnings.filterwarnings(action='ignore')

PORT_NUMBER = 8666


# kospi top50 기업
def get_finance():
    financeUrl = "https://finance.naver.com/sise/sise_market_sum.nhn?page=1"
    financeUrl = requests.get(financeUrl)
    finance = financeUrl.text
    financeData = pd.read_html(financeUrl.text)[1][0:]
    financeData.drop(index=0, inplace=True)
    financeKey = ["토론실", "외국인비율"]
    financeData.drop(financeKey, axis=1, inplace=True)
    financeData.dropna(how="all", inplace=True)
    financeData.reset_index(inplace=True)
    financeData.drop("index", axis=1, inplace=True)

    targetUrl = "https://finance.naver.com/sise/sise_market_sum.nhn?page=1"
    data = requests.get(targetUrl)
    bsData = BeautifulSoup(data.text, 'lxml')
    typeTag = bsData.find("table", {"class": "type_2"})
    tbodyTag = typeTag.find("tbody")
    top50 = tbodyTag.find_all("a", {"class": "tltle"})
    linkList = []
    for i in range(0, len(top50)):
        linkList.append(list(top50[i].attrs["href"][-6:].split(" ")))
    codeDf = pd.DataFrame(linkList, columns=["종목코드"])
    kospi50 = pd.merge(left=financeData, right=codeDf, left_index=True, right_index=True, how="left")
    kospi50.drop(columns="N", inplace=True)
    return kospi50


# 선정 기업의 code
def code(kospi50):
    try:
        code = kospi50[kospi50["종목명"] == codeDf].iloc[0]['종목코드']
        return code
    except Exception as e:
        return "No stock name"


# 선정 기업의 PER
def stockPer(kospi50):
    try:
        stock = kospi50.loc[kospi50["종목명"] == codeDf]
        stockPer = stock["PER"].item()
        return stockPer
    except Exception as e:
        return "No stock name"


# 선정 기업의 재무제표(연간, 분기)
def information(code):
    codeUrl = "https://finance.naver.com/item/main.nhn?code="
    Html = requests.get(codeUrl + code)
    codeHtml = Html.text
    codeData = pd.read_html(Html.text)[3]

    codeData.set_index(("주요재무정보", "주요재무정보", "주요재무정보"), inplace=True)
    codeData.index.rename("주요재무정보", inplace=True)
    codeKey = ["영업이익률", "순이익률", "부채비율", "당좌비율", "유보율", "BPS(원)", "주당배당금(원)", "시가배당률(%)", "배당성향(%)"]
    codeData.drop(index=codeKey, inplace=True)
    codeData.columns = codeData.columns.droplevel(2)
    codeData = codeData.transpose()
    codeData.columns = ["매출액", "영업이익", "당기순이익", "ROE", "EPS", "PER", "PBR"]
    codeData.dropna(axis=0, inplace=True)
    codeData = codeData.reset_index()
    codeData = codeData.drop(columns="level_0")
    codeData.rename(columns={"level_1": "date"}, inplace=True)
    return codeData


# 동일업종 per
def same_industryPer(code):
    codeUrl = "https://finance.naver.com/item/main.nhn?code="
    Html = requests.get(codeUrl + code)
    sameIndustryPer = pd.read_html(Html.text)[9]
    sameIndustryPer = sameIndustryPer[1][0].split("배")[0]
    sameIndustryPer = float(sameIndustryPer)
    return sameIndustryPer


# 동일업종 pbr
def same_industryPbr(code):
    codeUrl = "https://finance.naver.com/item/main.nhn?code="
    Html = requests.get(codeUrl + code)
    sameIndustryPbr = pd.read_html(Html.text)[4]
    sameIndustryPbr = sameIndustryPbr.transpose()
    sameIndustryPbr
    dropCol = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    sameIndustryPbr.drop(columns=dropCol, inplace=True)
    sameIndustryPbr = sameIndustryPbr.reset_index()
    sameIndustryPbr.columns = ["종목명", "PER", "PBR"]
    sameIndustryPbr = sameIndustryPbr.drop(index=0, axis=0)
    sameIndustryPbr = sameIndustryPbr["PBR"].rolling(window=5).mean()
    sameIndustryPbr = sameIndustryPbr[-1:].item()
    return sameIndustryPbr


# 선정 기업의 주식 가격
def stock_price(code):
    today = date.today()
    startday = date.today() - timedelta(90)
    yesterday = date.today() - timedelta(1)
    SEC = web.DataReader(code, startday, yesterday)

    # 장이 열리지 않을 때
    SEC = SEC[SEC["Volume"] != 0]

    # log rate
    SEC["logRate"] = np.log(SEC["Close"].astype(float) / SEC["Close"].shift(1).astype(float)) * 1000

    SEC['MA_5'] = SEC['Close'].rolling(window=5).mean()
    SEC['MA_20'] = SEC['Close'].rolling(window=20).mean()
    SEC['diff'] = SEC['MA_5'] - SEC['MA_20']

    # (Bollinger Bands) - upperLimit, lowerLimit
    SEC["upperLimit"] = SEC.MA_20 + (np.std(SEC.MA_20)) * 2
    SEC["lowerLimit"] = SEC.MA_20 - (np.std(SEC.MA_20)) * 2
    SEC['Signal'] = 0.0
    SEC['Signal'] = np.where(SEC['MA_5'] > SEC['MA_20'], 1.0, 0.0)
    SEC['Position'] = SEC['Signal'].diff()
    SEC = np.floor(SEC, dtype=float)
    SEC.reset_index(inplace=True)
    return SEC


# 선정 기업의 futures_data (과거기준 미래 데이터 학습용)
def futures_data(code):
    today = date.today()
    startday = date.today() - timedelta(90)
    endday = date.today() + timedelta(30)
    fitSEC = web.DataReader(code, startday, endday)
    return fitSEC


# 동일업종 per 비교 (고평가, 저평가)
def evaluation_value(stockPer, sameIndustryPer):
    if stockPer > sameIndustryPer:
        return "overValued"
    else:
        return "underValued"


# upperLimit(위), lowerLimit(아래) 제외
def stop_trading(evaluationValue, stockPrice):
    try:
        if ((evaluationValue == "overValued") and (
                stockPrice['Close'][-1:].item() < stockPrice['upperLimit'][-1:].item())
                and (stockPrice['Close'][-1:].item() > stockPrice['lowerLimit'][-1:].item())):
            return "overTrading"
        elif ((evaluationValue == "underValued") and (
                stockPrice['Close'][-1:].item() < stockPrice['upperLimit'][-1:].item())
              and (stockPrice['Close'][-1:].item() > stockPrice['lowerLimit'][-1:].item())):
            return "underTrading"
        else:
            return "not recommend"
    except Exception as e:
        return "no value"


# (고/저)평가 현재-기준 매도, 매수 추천
def stock_recommend(trading, information, sameIndustryPbr):
    if ((trading == "overTrading") and (information['PBR'][-1:].item() < sameIndustryPbr)):
        return "buying"
    elif ((trading == "underTrading") and (information['PBR'][-1:].item() < sameIndustryPbr)):
        return "sell"
    else:
        return "short-term not recommend"


def fit_plot(futuresData):
    try:
        # 예측할 날짜 ds
        futuresData = pd.DataFrame({'ds': futuresData.index, 'y': futuresData['Close']})
        m = Prophet()
        m.fit(futuresData)
        futures = m.make_future_dataframe(periods=90) # 90일
        forecast = m.predict(futuresData)
        m.plot_components(forecast)
        plt.show()
        return m
    except Exception as e:
        return "no plot"


def stockPrice_plot(stockPrice, codeDf, code):
    try:
        pylab.rcParams['figure.figsize'] = (15, 9)
        font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
        rc('font', family=font_name)
        plt.figure(figsize=(20, 10))

        stockPrice['Close'].plot(color='k', label='Close')
        stockPrice['MA_5'].plot(color='b', label='5-day SMA')
        stockPrice['MA_20'].plot(color='g', label='20-day SMA')

        # plot ‘buy’ signals
        plt.plot(stockPrice[stockPrice['Position'] == 1].index, stockPrice['MA_5'][stockPrice['Position'] == 1],
                 '^', markersize=15, color='g', label='buy')

        # plot ‘sell’ signals
        plt.plot(stockPrice[stockPrice['Position'] == -1].index, stockPrice['MA_5'][stockPrice['Position'] == -1],
                 'v', markersize=15, color='r', label='sell')
        plt.ylabel('Price', fontsize=15)
        plt.xlabel('Date', fontsize=15)
        plt.title(codeDf + " 분석결과" " (" + code + ")", fontsize=15)
        plt.legend()
        plt.grid()
        plt.show()
    except Exception as e:
        return "no plot"


kospi50 = get_finance()
print(kospi50)
codeDf = input("kospi50(종목명): ")
code = code(kospi50)
stockPer = stockPer(kospi50)
information = information(code)
sameIndustryPer = same_industryPer(code)
sameIndustryPbr = same_industryPbr(code)
evaluationValue = evaluation_value(stockPer, sameIndustryPer)
stockPrice = stock_price(code)
trading = stop_trading(evaluationValue, stockPrice)
futuresData = futures_data(code)
stockRecommend = stock_recommend(trading, information, sameIndustryPbr)
fitPlot = fit_plot(futuresData)
stockPricePlot = stockPrice_plot(stockPrice, codeDf, code)

result = ("종목명 : " + codeDf + "/ 종목코드 : " + code + "/ (매수/매도) 추천 : " + stockRecommend)
print(result)

# server에서 input값을 못받음 500 Error
# class myHandler(BaseHTTPRequestHandler):
#
#     def do_GET(self):
#         data = []  # response json data
#         if None != re.search('/stock/*', self.path):
#             if None != re.search('/stock/get_finance', self.path):
#
#                 try:
#                     self.send_response(200)
#                     self.send_header('Content-type', 'application/json')
#                     self.end_headers()
#
#                     try:
#                         kospi50 = get_finance()
#                         codeDf = input("kospi50(종목명): ")
#                         code = code(kospi50)
#                         stockPer = stockPer(kospi50)
#                         information = information(code)
#                         sameIndustryPer = same_industryPer(code)
#                         sameIndustryPbr = same_industryPbr(code)
#                         evaluationValue = evaluation_value(stockPer, sameIndustryPer)
#                         stockPrice = stock_price(code)
#                         trading = stop_trading(evaluationValue, stockPrice)
#                         futuresData = futures_data(code)
#                         stockRecommend = stock_recommend(trading, information, sameIndustryPbr)
#                         fitPlot = fit_plot(futuresData)
#                         stockPricePlot = stockPrice_plot(stockPrice, codeDf, code)
#
#                         result = ("종목명 : " + codeDf + "/ 종목코드 : " + code + "/ (매수/매도) 추천 : " + stockRecommend)
#                         print(result)
#                         data.append(result)
#                         self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))
#                     except:
#                         print("Error")
#                         data.append("Error")
#                         self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))
#                 except:
#                     self.send_response(500)
#                     self.send_header('Content-type', 'application/json')
#                     self.end_headers()
#                     data.append("error")
#             else:
#                 self.send_response(404)
#                 self.send_header('Content-type', 'application/json')
#                 self.end_headers()
#                 data.append("{info:no such api}")
#                 self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))
#
# # class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
# #     """Handle requests in a separate thread."""
#
# try:
#     # Create a web server and define the handler to manage the
#     # incoming request
#     server = HTTPServer(('', PORT_NUMBER), myHandler)
#     # server = ThreadedHTTPServer(('', PORT_NUMBER), myHandler)
#     print('Started httpserver on port ', PORT_NUMBER)
#
#     # Wait forever for incoming http requests
#     server.serve_forever()
#
# except (KeyboardInterrupt, Exception) as e:
#     print('^C received, shutting down the web server')
#     print(e)
#     server.socket.close()