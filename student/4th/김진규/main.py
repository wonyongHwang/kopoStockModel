from bs4 import BeautifulSoup
import requests
from datetime import date, timedelta
import FinanceDataReader as fdr
import pandas as pd
import matplotlib.pyplot as plt
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import re
import json
import pyautogui as pg
# -----------------------------------------------------------------
#    Author: 김진규
#    Created: 2021.06.18
#    Description:
#       - 주요 함수 목록 -
#       isGoodStock - 5개의 지표를 활용, 해당 종목이 투자하기 좋은 종목인지 판단
#       sellBuyDay - 골든크로스, 데드크로스 상황에서의 장기적 추세로 사고 파는 날을 결정, 마진율을 표시.
#       drawGraph - 추세선을 그려주는 함수
#
#       - 사용 예시 -
#        http://localhost:8201/stock/isGoodStock?code=102280 으로 get 요청
# -----------------------------------------------------------------






PORT_NUMBER = 8201
def zeroFill(columnValue):
    columnValue = str(columnValue)

    outValue = columnValue.zfill(6)

    return outValue

## 거래 대상일 추출 함수
def decideDaysList(table):
    targetTable = table.reset_index()

    DateArray = targetTable.Date

    return DateArray

## 거래 대상일 중 가장 최근일 추출 함수
def lastDay(table):
    targetTable = table.reset_index()

    DateArray = targetTable.Date

    length = len(DateArray)

    lastday = DateArray[length - 1]

    return lastday


# 과열종목 판단 함수. true 일 경우 최근 상대강도과열종목(네이버 금융 기준)
def overHeatStock(stockCode):

    stock_code = str(stockCode).zfill(6)
    end = date.today()
    start = date.today() - timedelta(365)  # 1년 데이터.
    targetStock = fdr.DataReader(stock_code, start, end)
    df_krx = fdr.StockListing('KRX')
    targetName = df_krx.loc[df_krx.Symbol == stock_code].Name.item()  ## 해당 종목 이름 가져오기

    overHeatUrl = 'https://finance.naver.com/sise/item_overheating_2.nhn'
    resp = requests.get(url=overHeatUrl)  ## response 200 = 정상, 확인완료
    resp.encoding = "euc-kr"  ## 인코딩
    html = resp.text
    htmlObj = BeautifulSoup(html, "html.parser")  ## beautifulSoup 사용

    ## 목표 테이블 추출. 상대강도과열종목의 이름 List
    targetList = htmlObj.findAll("a", "tltle")

    targetList[0].text

    overHeatNameList = []

    for i in range(0, len(targetList)):
        overHeatNameList.append(targetList[i].text)

    ## 급등주 목록에 있는지 확인.
    for i in range(0, len(overHeatNameList)):
        if targetName == overHeatNameList[i]:
            return True
        else:
            return False


# 동일업종 per과 해당 종목간의 per 비교 함수. 1 리턴 -> PER수치 괜찮다
def comparePER(stockCode):


    # stock_code = '5490'
    stock_code = str(stockCode).zfill(6)

    url = 'https://finance.naver.com/item/main.nhn?code=' + stock_code
    table_df_list = pd.read_html(url, encoding='euc-kr')
    earningInfo = table_df_list[3]

    targetStockAvgPER = float(earningInfo.values[10][5:-1].mean())
    sameBusniessPER = table_df_list[9]
    targetBusniessPER = sameBusniessPER[1].values[0]
    targetBusniessPER = float(targetBusniessPER.split("배")[0])

    if targetStockAvgPER <= targetBusniessPER:
        return 1
    else:
        return 2


# 여러 조건 종합, 투자하기 좋은 조건의 종목인지 판단하는 함수. 0 리턴 -> 괜찮은 회사다

def isGoodStock(stockCode):

    stock_code = zeroFill(stockCode)
    end = date.today()
    start = date.today() - timedelta(365)  # 1년 데이터.
    targetStock = fdr.DataReader(stock_code, start, end)
    df_krx = fdr.StockListing('KRX')
    targetName = df_krx.loc[df_krx.Symbol == stock_code].Name.item()

    url = 'https://finance.naver.com/item/main.nhn?code=' + stock_code
    table_df_list = pd.read_html(url, encoding='euc-kr')
    earningInfo = table_df_list[3]
    earningArray = earningInfo.values[4][1:5]

    debtRatio = earningInfo.values[6]
    AvgDebtRatio = debtRatio[5:9].mean()


    recentEarningRate = pd.DataFrame(earningArray)
    dropNaEarningRate = recentEarningRate.dropna()
    recentGrowthRate = float(dropNaEarningRate.values[-1])

    # 1. 매출액이 감소하는 추세인지
    if recentGrowthRate < 0.1:
        return 1

    # 2. 부채비율이 200이상인 부실기업인지
    elif AvgDebtRatio >= 200:
        return 2

    # 3. 일일 평균거래량이 3만주 이내로 적은 종목인지
    elif targetStock.Volume.mean() < 30000:
        return 3

    # 4. 상대강도과열종목인지
    elif overHeatStock(stock_code) == True:
        return 4

    # 5. 동일업종 PER보다 해당 종목의 PER이 높은지
    elif comparePER(stock_code) == 2:
        return 5

    else:
        return 0



# 추세선 그리는 함수
def drawGraph(stockCode):

    # stock_code = '5490'
    stock_code = zeroFill(stockCode)
    df_krx = fdr.StockListing('KRX')

    MA_5 = 5  ## 단기추세선
    MA_20 = 20  ## 단기추세선
    MA_60 = 60  ## 단기추세선
    MA_120 = 120  ## 장기추세선
    MA_200 = 200  ## 장기추세선

    end = date.today()
    start = date.today() - timedelta(365)  # 1년 데이터.
    targetStock = fdr.DataReader(stock_code, start, end)
    # targetName = df_krx.loc[df_krx.Symbol == stock_code].Name.item()

    # STOCK["MA_5"]=STOCK["Close"].rolling(window=5).mean_periods=1.mean()
    targetStock["MA_5"] = targetStock["Close"].rolling(window=MA_5).mean()  # min_periods=1 5일치 종가를 가져와 rolling
    targetStock["MA_20"] = targetStock["Close"].rolling(window=MA_20).mean()
    targetStock["MA_60"] = targetStock["Close"].rolling(window=MA_60).mean()
    targetStock["MA_120"] = targetStock["Close"].rolling(window=MA_120).mean()
    targetStock["MA_200"] = targetStock["Close"].rolling(window=MA_200).mean()

    MA_5_data = targetStock.MA_5
    MA_20_data = targetStock.MA_20
    MA_60_data = targetStock.MA_60
    MA_120_data = targetStock.MA_120
    MA_200_data = targetStock.MA_200

    targetStock["MA_5_change"] = MA_5_data.pct_change()
    targetStock["MA_20_change"] = MA_20_data.pct_change()
    targetStock["MA_60_change"] = MA_60_data.pct_change()
    targetStock["MA_120_change"] = MA_120_data.pct_change()
    targetStock["MA_200_change"] = MA_200_data.pct_change()

    targetStock["MA_5_change_per"] = targetStock.MA_5_change.pct_change()
    targetStock["MA_20_change_per"] = targetStock.MA_20_change.pct_change()
    targetStock["MA_60_change_per"] = targetStock.MA_60_change.pct_change()
    targetStock["MA_120_change_per"] = targetStock.MA_120_change.pct_change()
    targetStock["MA_200_change_per"] = targetStock.MA_200_change.pct_change()

    plt.figure(figsize=(16, 10))

    plt.subplot(311)
    plt.plot(targetStock.index, targetStock['Close'], label='Close')
    plt.plot(targetStock.index, targetStock['MA_5'], label='MA 5day')
    plt.plot(targetStock.index, targetStock['MA_20'], label='MA 20day')
    plt.plot(targetStock.index, targetStock['MA_60'], label='MA 60day')
    plt.plot(targetStock.index, targetStock['MA_120'], label='MA 120day')
    plt.plot(targetStock.index, targetStock['MA_200'], label='MA 200day')
    plt.title("moving average")
    plt.legend(loc='best')

    plt.subplot(312)
    plt.plot(targetStock.index, targetStock['MA_5_change_per'], label='MA_5_change_per')
    plt.plot(targetStock.index, targetStock['MA_20_change_per'], label='MA_20_change_per')
    # plt.plot(targetStock.index, targetStock['MA_60_change_per'], label='MA_60_change_per')
    # plt.plot(targetStock.index, targetStock['MA_120_change_per'], label='MA_120_change_per')
    # plt.plot(targetStock.index, targetStock['MA_200_change_per'], label='MA_200_change_per')
    plt.title("MA_short_change")
    plt.legend(loc='best')

    plt.subplot(313)
    plt.plot(targetStock.index, targetStock['MA_60_change_per'], label='MA_60_change_per')
    plt.plot(targetStock.index, targetStock['MA_120_change_per'], label='MA_120_change_per')
    plt.plot(targetStock.index, targetStock['MA_200_change_per'], label='MA_200_change_per')
    plt.title("MA_long_change")
    plt.legend(loc='best')

    plt.show()




# 사고 파는날을 결정하는 함수
def sellBuyDay(stockCode):

    stock_code = zeroFill(stockCode)
    df_krx = fdr.StockListing('KRX')

    MA_5 = 5  ## 단기추세선
    MA_20 = 20  ## 단기추세선
    MA_60 = 60  ## 단기추세선
    MA_120 = 120  ## 장기추세선
    MA_200 = 200  ## 장기추세선

    end = date.today()
    start = date.today() - timedelta(365)  # 1년 데이터.
    targetStock = fdr.DataReader(stock_code, start, end)
    targetName = df_krx.loc[df_krx.Symbol == stock_code].Name.item()

    # STOCK["MA_5"]=STOCK["Close"].rolling(window=5).mean_periods=1.mean()
    targetStock["MA_5"] = round(targetStock["Close"].rolling(window=MA_5, min_periods=1).mean())
    targetStock["MA_20"] = round(targetStock["Close"].rolling(window=MA_20, min_periods=1).mean())
    targetStock["MA_60"] = round(targetStock["Close"].rolling(window=MA_60, min_periods=1).mean())
    targetStock["MA_120"] = round(targetStock["Close"].rolling(window=MA_120, min_periods=1).mean())
    targetStock["MA_200"] = round(targetStock["Close"].rolling(window=MA_200, min_periods=1).mean())

    ## 평균선들의 추세를 계산.
    MA_5_data = targetStock.MA_5
    MA_20_data = targetStock.MA_20
    MA_60_data = targetStock.MA_60
    MA_120_data = targetStock.MA_120
    MA_200_data = targetStock.MA_200

    targetStock["MA_5_change"] = MA_5_data.pct_change()
    targetStock["MA_20_change"] = MA_20_data.pct_change()
    targetStock["MA_60_change"] = MA_60_data.pct_change()
    targetStock["MA_120_change"] = MA_120_data.pct_change()
    targetStock["MA_200_change"] = MA_200_data.pct_change()

    targetStock["MA_5_change_per"] = targetStock.MA_5_change.pct_change()
    targetStock["MA_20_change_per"] = targetStock.MA_20_change.pct_change()
    targetStock["MA_60_change_per"] = targetStock.MA_60_change.pct_change()
    targetStock["MA_120_change_per"] = targetStock.MA_120_change.pct_change()
    targetStock["MA_200_change_per"] = targetStock.MA_200_change.pct_change()

    # ## 상승추세 . 5일선 위에 있는 상태
    # targetStock.loc[targetStock.Close > targetStock.MA_5]

    # ## 20일선 돌파한 상태
    # targetStock.loc[targetStock.Close > targetStock.MA_20]

    # ## 5일선과 20일선 둘다 돌파한 상태.
    # targetStock.loc[ (targetStock.Close > targetStock.MA_5) & (targetStock.Close > targetStock.MA_20)  ]

    # 상승하는 날들
    upList = targetStock.loc[(targetStock.Close > targetStock.MA_5) & (targetStock.Close > targetStock.MA_20) & (
                targetStock.MA_5_change > 0)]

    # 하락하는 날들
    downList = targetStock.loc[(targetStock.Close < targetStock.MA_5) & (targetStock.Close < targetStock.MA_20) & (
                targetStock.MA_5_change < 0)]

    # 20일 이동평균선이 60일 이동평균선을 돌파하는 골든크로스가 나타난다고 하더라도 중장기 선인 120일, 200일 이동평균선이 하락을 이어간다면 매도시점으로 보아야 한다.
    upButSellList = upList.loc[
        (upList.MA_20 > upList.MA_60) & (upList.MA_120_change_per < 0) & (upList.MA_200_change_per < 0)]

    # 일봉에서 5일 이동평균선과 20일 이동평균선이 데드크로스를 그리더라도 120일, 200일 이동평균선이 상승추세를 이어간다면 이 데드크로스는 오히려 매수시점으로 보아야한다.
    downButBuyList = downList.loc[
        (downList.MA_5 < downList.MA_20) & (downList.MA_120_change_per > 0) & (downList.MA_200_change_per > 0)]

    upDays = decideDaysList(upList)

    downDays = decideDaysList(downList)

    upButSellDays = decideDaysList(upButSellList)

    downButBuyDays = decideDaysList(downButBuyList)

    sellBuyArray = []

    recentUBSDay = lastDay(upButSellDays)
    recentDBBDAy = lastDay(downButBuyDays)

    # 가장 최근의 데이터 리턴.
    sellBuyArray.append(recentUBSDay)
    sellBuyArray.append(recentDBBDAy)

    return sellBuyArray

def initSvr(): ## 서버 시작시..
    print("init Server")


class myHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        data = "";

        print(self.path)
        if None != re.search('/stock/*', self.path):

            ## 해당 종목 평가 url
           if None != re.search('/stock/isGoodStock', self.path): # http://localhost:8201/stock/isGoodStock?code=102280
                stockCode = self.path.split("?")[-1].split("=")[-1]

                try:

                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    print(self.send_response)
                    print(self.path)
                    self.end_headers()

                    result = isGoodStock(stockCode)

                    if result == 1:
                        data = "row growthrate"
                    elif result == 2:
                        data = "lots of debt"
                    elif result == 3:
                        data = "row volume"
                    elif result == 4:
                        data = "overheatstock"
                    elif result == 5:
                        data = "high PER"
                    else: data = "good stock"


                except:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()

                finally:
                   self.wfile.write(data.encode())
                #self.wfile.write(3)

            # 사고파는 날짜와, 그 로직대로 했을 경우의 마진율 리턴(시작가 기준)
            # http://localhost:8201/stock/BuySellTiming?code=102280
           if None != re.search('/stock/BuySellTiming', self.path):
                stockCode = self.path.split("?")[-1].split("=")[-1]


                try:

                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    print(self.send_response)
                    print(self.path)
                    self.end_headers()

                    arr = sellBuyDay(stockCode)
                    print(arr)
                    day = {'SellDay': '', 'BuyDay': '', 'marginPercent' : ""}
                    day['SellDay'] = str(arr[0])
                    day['BuyDay'] = str(arr[1])

                    sellday = arr[0]
                    buyday = arr[1]
                    today = date.today()

                    ## 오늘이 팔거나 사는 날일때 alert.
                    if today == sellday or today == buyday:
                        a = pg.alert(text='오늘 거래하세요!', title='거래찬스!', button='OK')
                        print(a)


                    sellday = pd.to_datetime(sellday).date()
                    buyday = pd.to_datetime(buyday).date()
                    buydayInfo = fdr.DataReader(stockCode, buyday, buyday)
                    selldayInfo = fdr.DataReader(stockCode, sellday, sellday)
                    buyDayClose = buydayInfo.Open
                    sellDayClose = selldayInfo.Open
                    buyDayCloseDf = pd.DataFrame(buyDayClose)
                    sellDayCloseDf = pd.DataFrame(sellDayClose)
                    buyDayClosePrice = buyDayCloseDf.Open[0]
                    sellDayClosePrice = sellDayCloseDf.Open[0]

                    ## 주당 순이익
                    profitPerOneStock = sellDayClosePrice - buyDayClosePrice

                    ## 주당 상승률(수익률)
                    marginPercent = str(round((profitPerOneStock / sellDayClosePrice) * 100))

                    day['marginPercent'] = str(marginPercent + "%")

                    drawGraph(stockCode)



                except:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()

                finally:

                    self.wfile.write(bytes(json.dumps(day, sort_keys=True, indent=4), "utf-8"))
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        """Handle requests in a separate thread."""

try:

    # Create a web server and define the handler to manage the
    # incoming request
    # server = HTTPServer(('', PORT_NUMBER), myHandler)
    server = ThreadedHTTPServer(('', PORT_NUMBER), myHandler)
    print('Started httpserver on port ', PORT_NUMBER)

    initSvr()
    # Wait forever for incoming http requests
    server.serve_forever()

except (KeyboardInterrupt, Exception) as e:
    print('^C received, shutting down the web server')
    print(e)
    server.socket.close()