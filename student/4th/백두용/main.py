from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse
from urllib.parse import parse_qs
import FinanceDataReader as web
import matplotlib.pyplot as plt
import datetime
from datetime import date, timedelta
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import threading
import time
import re
import json

PORT_NUMBER = 8200


def topTen() -> list:
    # from bs4 import BeautifulSoup
    # import requests
    # import pandas as pd

    # 시가 총액 상위 10개 종목이름을 가져옴('삼성전자(우)'를 제외한 11위까지의 종목)
    url = 'https://finance.naver.com/sise/sise_market_sum.nhn'
    topTen = pd.read_html(url, encoding='euc-kr')[1].head(18)

    # 상위 10개 종목 이름을 list형태로 저장함
    topList = []
    for i in range(0, len(topTen['종목명'])):
        if type(topTen['종목명'][i]) == float:
            continue
        else:
            topList.append(topTen['종목명'][i])

    # 네이버금융(현대차)과 한국거래소(현대자동차)간의 종목이름 차이를 없애줌
    for i in range(0, len(topList)):
        if '현대차' == topList[i]:
            topList[i] = topList[i].replace('현대차', '현대자동차')
            break
    # 중복종목(삼성전자(우))을 제외한 시가총액 상위 10개 종목명을 리스트에 담아서 반환
    return topList


def topTenSymbol(inValue: list) -> list:
    # from bs4 import BeautifulSoup
    # import requests
    # import pandas as pd
    # 거래소에서 KOSPI의 종목정보가 담겨있는 table을 가져옴
    df = pd.read_html('https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&marketType=stockMkt')
    totalList = df[0]

    # KOSPI의 종목코드들을 전부 담음
    totalSymbol = []
    for i in range(0, len(totalList['종목코드'])):
        totalSymbol.append(totalList['종목코드'][i])

    # KOSPI의 회사명들을 전부 담음
    totalName = []
    for i in range(0, len(totalList['회사명'])):
        totalName.append(totalList['회사명'][i])

    # 상위 10개종목의 회사명과 비교해서 같은 이름 회사들의 종목코드를 가져옴
    topSymbol = []
    for i in range(0, len(inValue)):
        for j in range(0, len(totalName)):
            if inValue[i] == totalName[j]:
                topSymbol.append(totalSymbol[j])
                break
    # 상위 10개 종목코드가 들어있는 리스트를 반환함
    return topSymbol


def zeroFill(columnValue) -> str:
    # 종목코드의 데이터 형태를 맞춰주기 위한 lpad함수
    columnValue = str(columnValue)
    # zfill(6)은 6자리로 문자열 맞춘다. 빈자리는 앞에서 부터 0을 채움
    outValue = columnValue.zfill(6)
    # 문자열 왼쪽에 0을 붙여 6자리를 만들어 준다.
    return outValue


def CCIftn(inValue: str, start: str) -> 'pandas.core.frame.DataFrame':
    import FinanceDataReader as web
    # CCI(Commodity Channel Index)
    # 최근의 가격이 평균가격의 이동평균과 얼마나 떨어져 있는가를 표시하여 추세의 강도와 방향을 나타내어 준다.
    # 가격이 한 방향으로 계속 움직일 경우에는 현재 가격이 이동편균과 멀리 떨어지게 되며 이 경우를 추세가 강하다고 볼 수 있다.
    # 따라서 CCI가 양(+)의 값을 가지면 상승추세, 음(-)의 값을 가질 경우에는 하락추세를 나타낸다고 할 수 있다.
    # CCI는 추세의 강도와 방향까지 동시에 알려주는 지표이다.
    # inValue=종목코드, start=시작일자
    '''
    이 함수는 주식의 CCI지표를 볼수있도록 값을 구해줍니다.
    단, 종가는 주식시장에서 보여지는 있는 그대로의 종가를 사용했기 때문에 수정종가를 사용하는 실제 CCI에 비해 정확도가 떨어질 수 있습니다.

    - 최근의 가격이 평균가격의 이동평균과 얼마나 떨어져 있는가를 표시하여 추세의 강도와 방향을 나타내어 준다.
    - 가격이 한 방향으로 계속 움직일 경우에는 현재 가격이 이동편균과 멀리 떨어지게 되며 이 경우를 추세가 강하다고 볼 수 있다.
    - 따라서 CCI가 양(+)의 값을 가지면 상승추세, 음(-)의 값을 가질 경우에는 하락추세를 나타낸다고 할 수 있다.
    - CCI는 추세의 강도와 방향까지 동시에 알려주는 지표이다.
    - inValue=종목코드, start=시작일자
    '''

    chart = web.DataReader(inValue, start=start)

    # 거래량이 없는 날은 제외함
    chart = chart[chart['Volume'] != 0]

    # CCI = (M - m) / (0.015 * d)
    # M = (고가 + 저가 + 종가) / 3
    # m = M의 N기간 동안의 단순 이동평균
    # d = (M - m)의 절대값의 N기간 단순 이동평균
    # N기간 : 주로 9/14/20일을 사용(여기서는 14일을 사용)
    M = (chart['High'] + chart['Low'] + chart['Close']) / 3
    chart.insert(len(chart.columns), "M", M)

    avgM = chart['M'].rolling(window=14).mean()
    chart.insert(len(chart.columns), "MAL", avgM)

    miusAbs = abs(chart['M'] - chart['MAL'])
    chart.insert(len(chart.columns), "ABS", miusAbs)

    avgAbs = chart['ABS'].rolling(window=14).mean()
    chart.insert(len(chart.columns), "ABS_MAL", avgAbs)

    CCI = (chart['M'] - chart['MAL']) / (0.015 * chart['ABS_MAL'])
    chart.insert(len(chart.columns), "CCI", CCI)

    # Date값을 사용하기 위해 인덱스를 초기화하면서 컬럼명을 다시 설정해준다.
    chart.reset_index(inplace=True)
    chart = chart[["Date", "Open", "High", "Low", "Close", "Volume", "Change", "M", "MAL", "ABS", "ABS_MAL", "CCI"]]

    # 파라미터로 들어온 데이터프레임에 CCI값이 들어있는 컬럼을 붙여서 데이터프레임으로 반환함
    return chart


class StockDate:
    def nowftn(self, chart: 'pandas.core.frame.DataFrame') -> str:
        # import datetime
        # from datetime import date, timedelta
        '''
        - 현재날짜 기준 가장 최근의 개장일을 구해줌
        - 만약 거래소 개장전인 오전 9시 이전이라면 하루 전 날짜로 반환함
        '''
        # 컬럼에 Date가 없을 경우를 대비(정상작동했다면 조건문을 들어오는 경우의 수가 존재하지 않음)
        if 'Date' not in chart.columns:
            chart.reset_index(inplace=True)
            chart = chart[["Date"]]

        # 현재 날짜를 구함
        now = datetime.datetime.now()
        nowDate = now.strftime('%Y-%m-%d')
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

        # 현재 날짜의 시간이 오전 9시이전이라면 개장전이므로 날짜를 하루전으로 반환함
        if (int(nowDatetime[11:13]) < 9):
            now = now - timedelta(days=1)
            nowDate = now.strftime('%Y-%m-%d')
        else:
            now = datetime.datetime.now()
            nowDate = now.strftime('%Y-%m-%d')

        # 반환한 현재날짜가 미개장일이라면 가장 최근의 개장일로 변경해줌
        while (True):
            # 지금 설정되어있는 날짜가 개장일이 맞는지를 검사함
            for i in range(len(chart['Date']) - 1, 0, -1):
                if (nowDate in str(list(chart['Date'])[i])):
                    isNotInDate = False
                    break

                elif (nowDate not in str(list(chart['Date'])[i])):
                    isNotInDate = True
            # 만약 미개장일이라면 하루를 빼주고 다시 while반복문으로 들어감
            if (isNotInDate == True):
                now = now - timedelta(days=1)
                nowDate = now
                nowDate = nowDate.strftime('%Y-%m-%d')
            elif (isNotInDate == False):
                break
        # 현재날짜를 str형태로 반환함(ex. 2021-05-30)
        return nowDate

    def beforeftn(self, nowDate: str, N: int, chart: 'pandas.core.frame.DataFrame') -> str:
        # import datetime
        # from datetime import date, timedelta

        '''
        - 가장 최근의 개장일에서 N일전의 거래소 개장일을 구해줌
        - N일전의 날짜가 공휴일이면, 뒷 날짜의 평일로 변경함
        '''

        # 컬럼에 Date가 없을 경우를 대비(정상작동했다면 조건문을 들어오는 경우의 수가 존재하지 않음)
        if 'Date' not in chart.columns:
            chart.reset_index(inplace=True)
            chart = chart[["Date"]]

        # 파라미터로 들어온 문자열을 datetime 타입으로 변경해서 N일전 날짜를 계산함
        from datetime import datetime
        now = datetime.strptime(nowDate, '%Y-%m-%d')
        before_date = now - timedelta(days=N)
        before_N_day = before_date.strftime('%Y-%m-%d')

        # N일전 날짜가 미개장일이라면, 미개장일 기준으로 가장 최근의 개장일로 변경함
        while (True):
            # 지금 설정되어있는 날짜가 개장일이 맞는지를 검사함
            for i in range(len(chart['Date']) - 1, 0, -1):
                if (before_N_day in str(list(chart['Date'])[i])):
                    isNotInDate = False
                    break

                elif (before_N_day not in str(list(chart['Date'])[i])):
                    isNotInDate = True

            # 만약 미개장일이라면 하루를 빼주고 다시 while반복문으로 들어감
            if (isNotInDate == True):
                before_date = before_date - timedelta(days=1)
                before_N_day = before_date.strftime('%Y-%m-%d')
            elif (isNotInDate == False):
                break
        # 이전날짜를 str형태로 반환함(ex. 2021-01-03)
        return before_N_day


def tradeftn(before_day: str, nowDate: str, chart: 'pandas.core.frame.DataFrame') -> 'pandas.core.frame.DataFrame':
    # import pandas as pd
    '''
    - CCI지표를 기준으로 특정기간동안의 매수&매도 타이밍을 알려줌
    - 매수와 매도는 간단하게 "(고가 + 저가 + 종가) / 3"로 구한 수정종가로 계산함
    - queue를 사용해서 간단하게 CCI지표의 성과를 보여줌
    '''
    # 반복문을 돌릴 수 있도록 파라미터로 들어온 날짜에 해당하는 DataFrame의 인덱스로 변경함
    startDay = chart['Date'].loc[chart['Date'] == before_day].index[0]
    endDay = chart['Date'].loc[chart['Date'] == nowDate].index[0]
    # 사용할 리스트를 생성함
    pan = []
    queue = []

    # 반복문을 돌려서 매수&매도 타이밍을 잡고 실현손익이 발생하면 함께 표시함
    for i in range(startDay, endDay):

        # CCI가 100보다 클 경우 매도 타이밍
        if chart['CCI'][i] > 100.0:
            date = chart['Date'][i]
            price = round(chart['M'][i], 2)

            # 배열이 빈 값인지 확인하는 조건문
            # 빈값이 아니라면 가장 먼저 매수했던 주식을 매도함
            if queue:
                res = round((price - queue[0]), 2)
                queue.pop(0)
            elif not queue:
                res = None
                print()
            # 결과를 리스트에 담음
            pan.append(["sell", date, price, res])

        # CCI가 -100보다 작을 경우 매수 타이밍
        elif chart['CCI'][i] < -100.0:
            date = chart['Date'][i]
            price = round(chart['M'][i], 2)
            queue.append(chart['M'][i])
            # 결과를 리스트에 담음
            pan.append(["buy", date, price, None])

    # 매수&매도 결과를 가지고 있는 리스트를 데이터 프레임형태로 변환
    CCIResult = pd.DataFrame(pan, columns=['Act', 'Date', 'Price', 'Profit'])

    # 결과값을 가지는 데이터 프레임을 반환함
    return CCIResult


def profitList(res: list) -> list:
    # 총 이익을 계산하기 위해 종목별 순이익을 리스트에 담는 함수
    # 들어오는 파라미터는 종목별 실현손익의 데이터프레임들이 담겨있는 리스트
    tempProfit = 0
    profit = []
    # res의 크기만큼 반복문을 돌려서 실현손익의 총합을 구함
    for i in range(0, len(res)):
        for j in range(0, len(res[i])):
            # 데이터프레임의 Profit컬럼이 전부 NULL값인 경우 continue
            if res[i]['Profit'][j] == None:
                continue
            # 이익이 존재하면 tempProfit에 더해줌.
            temp = str(res[i]['Profit'][j])
            if temp != 'nan':
                tempProfit += float(res[i]['Profit'][j])
        # 종목별 결과를 profit에 append해준다.
        profit.append(tempProfit)
        # 초기화
        tempProfit = 0

    # 종목별 총 손익을 리스트로 반환함
    return profit


def totalProfit(sumProfit: list) -> float:
    # CCI지표를 토대로 단기투자를 실행했을 때 벌어들이는 총 이익을 구하는 함수
    netIncome = 0
    for i in range(0, len(sumProfit)):
        netIncome += sumProfit[i]
    # 총손익을 float으로 반환함
    return netIncome


def showResult(nowDate: str, before_day: str, chart: 'pandas.core.frame.DataFrame', symbol: str) -> 'show':
    # import matplotlib.pyplot as plt
    # 차트 시각화를 위한 함수
    # 회색 점선으로 되어있는 라인을 기준으로 매수와 매도가 결정된다.

    fig = plt.figure(figsize=(20, 10))
    ax1 = fig.add_subplot(211)  # 2행1열의 첫번째칸에 그려라
    plt.xlim(datetime.date(int(before_day[0:4]), int(before_day[5:7]), int(before_day[8:10])), \
             datetime.date(int(nowDate[0:4]), int(nowDate[5:7]), int(nowDate[8:10])))
    plt.title(symbol, {'fontsize': 16}, loc='left', pad=10)
    x = chart['Date']
    y1 = chart['CCI']
    y2 = chart['M']
    ax1.plot(x, y1, 'r', label='CCI')
    ax1.legend(loc=2, prop={'size': 20})
    ax1.axhline(100, 0, 1, color='gray', linestyle='--')
    ax1.axhline(0, 0, 1, color='gray', linestyle='--')
    ax1.axhline(-100, 0, 1, color='gray', linestyle='--')
    ax1.legend(loc=2, prop={'size': 20})

    ax2 = fig.add_subplot(212)  # 2행1열의 두번째칸에 그려라
    plt.xlim(datetime.date(int(before_day[0:4]), int(before_day[5:7]), int(before_day[8:10])), \
             datetime.date(int(nowDate[0:4]), int(nowDate[5:7]), int(nowDate[8:10])))
    ax2.plot(x, y2, 'b', label='stockPrice')
    ax2.legend(loc=1, prop={'size': 20})
    plt.show()


class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = []  # response json data

        if None != re.search('/STOCK/*', self.path.upper()):
            if None != re.search('/STOCK/CCI', self.path.upper()):
                # http://localhost:8200/stock/cci
                try:
                    # 반복문을 돌면서 차트와 손익결과를 출력함
                    for i in range(0, len(symbol)):
                        showResult(nowDate, before_day, chartList[i], symbol[i])
                        print(top[i], "로 실현한 총이익 : ", sumProfit[i])

                    # 총이익을 출력함
                    print("10개 종목으로 실현한 총 이익", income)

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    data.append("{info:success}")
                    self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))


                # 시각화 함수실행이 에러나는 경우
                except:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    data.append("{info: not enough request}")
                    self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))
            
            # 시가총액 1위부터 10위까지의 종목중 원하는 범위를 지정하면 그 범위만큼의 종목들을 반환함
            elif None != re.search('/STOCK/TOP/*', self.path.upper()):
                # http://localhost:8200/STOCK/TOP/?1~10
                try:
                    # '~'을 기준으로 값을 나눈다
                    queryString = urlparse(self.path).query.split('~')
                    startPoint = queryString[0]
                    endPoint = queryString[1]

                    # 0이상의 양의 정수가 맞는지 정규표현식을 사용해 검증한다.
                    regex1 = re.match('^[0-9]+', startPoint)
                    regex2 = re.match('^[0-9]+', endPoint)

                    # 검증이 모두 True라면 조건문을 들어온다.
                    if regex1 != None and regex2 != None:
                        # int형으로 변환한다.
                        startPoint = int(startPoint)
                        endPoint = int(endPoint)

                        # 리스트의 인덱스와 숫자를 맞춰주기 위해 -1을 한다.
                        startPoint = startPoint - 1
                        endPoint = endPoint - 1

                        # 예외처리
                        if startPoint < 0 or startPoint > 10:
                            self.send_response(404)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            data.append("{info:out of range}")
                            self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

                        # 예외처리
                        elif endPoint > 9 or endPoint < 0:
                            self.send_response(404)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            data.append("{info:out of range}")
                            self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

                        # 원하는 조건에 모두 부합하면 해당하는 인덱스범위의 종목을 출력함
                        if startPoint >= 0 and endPoint <= 9 and startPoint <= endPoint:
                            eachIncome = []
                            # 반복문을 돌면서 차트와 손익결과를 출력함
                            for i in range(startPoint, endPoint + 1):
                                showResult(nowDate, before_day, chartList[i], symbol[i])
                                print(top[i], "로 실현한 총이익 : ", sumProfit[i])
                                eachIncome.append( sumProfit[i])

                            # 선택한 종목에 해당하는 총이익을 출력함
                            sum = 0
                            for i in range(0,len(eachIncome)):
                                sum += eachIncome[i]

                            print(len(eachIncome),"개 종목으로 실현한 총 이익", sum)

                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            data.append("{info:success}")
                            self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

                        else:
                            self.send_response(404)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            data.append("{info:startPoint is greater than the endPoint.}")
                            self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))
                    else:
                        self.send_response(404)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        data.append("{info:It does not match the format}")
                        self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))


                # /TOP?뒤에 오는 값이 양의 정수가 아니거나 1~10이외의 숫자인경우
                except:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    data.append("{info:request error}")
                    self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

            # 주소가 /CCI 또는 /TOP/*이 아닌경우
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data.append("{info: not enough request}")
                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

        # 주소아예 안맞는 경우
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data.append("{info:no such request}")
            self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))


res = []
chartList = []
top = topTen()
top.remove('삼성전자우')

symbol = topTenSymbol(top)
for i in range(0, len(symbol)):
    symbol[i] = zeroFill(symbol[i])

    chart = CCIftn(symbol[i], "20200101")
    chartList.append(chart)

    openingDate = StockDate()
    nowDate = openingDate.nowftn(chart)
    before_day = openingDate.beforeftn(nowDate, 120, chart)

    res.append(tradeftn(before_day, nowDate, chart))
    sumProfit = profitList(res)
    income = totalProfit(sumProfit)


# class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
#     """Handle requests in a separate thread."""


# main.py가 실행되면 조건문이 실행됨
if __name__ == '__main__':
    try:
        server = HTTPServer(('', PORT_NUMBER), MyHandler)
        # server = ThreadedHTTPServer(('', PORT_NUMBER), MyHandler)
        print('Started WebServer on port {}'.format(PORT_NUMBER))
        print('Press ^c to quit webserver')
        server.serve_forever()

    except (KeyboardInterrupt, Exception) as e:
        print('^C received, shutting down the web server')
        print(e)
        server.socket.close()