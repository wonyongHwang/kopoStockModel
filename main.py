# -*- coding: utf-8 -*-
import FinanceDataReader as web
from datetime import date, timedelta
import matplotlib.pyplot as plt
import datetime
import earningsRate
import numpy as np
from codeList import queryCodeList
from matplotlib import font_manager, rc
import matplotlib.ticker as ticker

from mplfinance.original_flavor import candlestick2_ohlc # pip install https://github.com/matplotlib/mpl_finance/archive/master.zip #pip install --upgrade mplfinance

from scipy import stats # line regression
from chart_studio.plotly import plot, iplot #  conda install -c plotly chart-studio
# import plotly.graph_objects as go
import plotly.express as px #  conda install -c plotly plotly-orca
import os

ma1 = 5
ma2 = 20
duration = 720
last_period = 50
set_period = 12 # 오늘날짜 기준 12일 전부터의 주식데이터 접근
'''
# line chart test
t = np.linspace(0, 2*np.pi, 100)
fig = px.line(x=t, y=np.cos(t), labels={'x':'t', 'y':'cos(t)'})
fig.show()
fig.write_image("aa.png")
print(fig)
'''

qc = queryCodeList()


def getClosePrice(code, startDay, EndDay):
    today = date.today()
    if startDay >= today or EndDay >= today or startDay > EndDay:
        print("date Error #1")
        return None
    if code is None:
        print("code Error #1")
        return None
    df = web.DataReader(code, startDay, EndDay)
    #print(df.head())
    return df

def getDiffMAs(code, df,n1,n2):
    if n1 >= n2:
        print("MA set error #1")
        return None
    if len(df) == 0:
        print("dataFrame has no data - ",qc.get_codename_by_codenum(code))
        return None
    if len(df) <= n1:
        print("length of dataFrame is less than or equal to ma #1")
        return None
    df["MA#1"] = np.round(df["Close"].rolling(window=n1, center=False).mean(),2)
    df["MA#2"] = np.round(df["Close"].rolling(window=n2, center=False).mean(),2)
    df["MA#Diff"] = df["MA#1"] - df["MA#2"]
    #print(df.head())
    #print(df["MA#Diff"].tolist())
    return df["MA#Diff"].tolist()


# 함수설명 : 투자심리선 지표 = 2주간의 상승일수 / 12 * 100 (※ 2주=12일로 설정된 경우)
#            75% 이상인 경우 단기 과열상태, 25% 이하이면 단기 침체상태
# author : 3기 주신이
def getPsychologicalLine(df):
    stockDiffList = []
    pLineList = []
    if len(df) < set_period:  # 가져온 주식데이터가 12일만큼의 데이터가 없을 때
        print("DataSet is not enough")
        pass
    else:
        df["stockDiff"] = 0  # stockDiff의 첫번째 값은 NaN이기 때문에 초기 세팅을 0값으로 준 후 그 다음 열부터 종가차이 깂을 넣어준다.
        df.loc[1:, "stockDiff"] = df["Close"] - df.shift(1)["Close"]
        for i in range(0, len(df)):
            #     stockDiffList = list(data.stockDiff[i-set_period:i])
            stockDiffList.append(list(df.stockDiff[(i + 1) - set_period:(i + 1)]))

        #         pLineList = []
        for stockDiff in stockDiffList:
            if not stockDiff:  # 리스트가 비어있을 때
                print(" StockDiff Data does not exist")
                pLineList.append("0")
            else:
                plusValue = []
                for stockDiffValue in stockDiff:
                    if stockDiffValue > 0:
                        plusValue.append(stockDiffValue)
                #               len(plusValue)
                pLineSon = len(plusValue)
                pLineMother = len(stockDiff)
                if pLineMother == 0:
                    pass
                else:
                    pLine = pLineSon / pLineMother * 100
                    pLineList.append(pLine)
    df["pLineValue"] = pLineList
    print(df)
    print(len(df))
    return df["pLineValue"].tolist()

# 함수설명 : 일목균형 계산
# author : 3기 황현빈
def ichimokuDataFrame(codeNum, companyName):
    # 종목코드를 가져와서 주가 정보를 가져온다.
    codeNum = codeNum
    companyName = companyName

    today = date.today()
    startday = date.today() - timedelta(720)

    stockDf = web.DataReader(codeNum, startday, today)
    # stockDf= stockDf.reset_index()

    conversionLine_window = 9
    standardLine_window = 26
    preSpan_window = 52
    preSpan = 26
    laggingSpan = -26

    # conversionLine
    # 전환선 : (과거 9일간의 최고가 + 과거 9일간의 최저가) / 2

    conversion_High = stockDf['High'].rolling(window=conversionLine_window, center=False).max()
    conversion_Low = stockDf['Low'].rolling(window=conversionLine_window, center=False).min()
    stockDf['Conversion'] = (conversion_High + conversion_Low) / 2

    # standardLine
    # 기준선 : (과거 26일간의 최고가 + 과거 26일간의 최저가) / 2

    standard_High = stockDf['High'].rolling(window=standardLine_window, center=False).max()
    standard_Low = stockDf['Low'].rolling(window=standardLine_window, center=False).min()
    stockDf['Standard'] = (standard_High + standard_Low) / 2

    # prespan1
    # 선행스팬1 : (금일 전환선 값 + 금일 기준선 값) / 2, 이 수치를 26일 후에 기입

    stockDf["Prespan1"] = ((stockDf["Conversion"] + stockDf["Standard"]) / 2).shift(preSpan)
    stockDf["futureSpan"] = (stockDf["Conversion"] + stockDf["Standard"]) / 2

    # prespan2
    # 선행스팬2 : (과거 52일간의 최고가 + 과거 52일간의 최저가) / 2, 이 수치를 26일 후에 기입

    preSpan2_High = stockDf["High"].rolling(window=preSpan_window, center=False).max()
    preSpan2_Low = stockDf["Low"].rolling(window=preSpan_window, center=False).min()
    stockDf["Prespan2"] = ((preSpan2_High + preSpan2_Low) / 2).shift(preSpan)

    # laggingSpan
    # 후행스팬 : 금일 종가를 26일 전에 기입

    stockDf["Laggingspan"] = stockDf["Close"].shift(laggingSpan)

    # conversion - standard 전환선과 기준선의 차이

    stockDf["ConStanDif"] = stockDf["Conversion"] - stockDf["Standard"]

    # 여러 계산을 통해 매수와 매도를 결정하기 위해 점수생성
    score = 0
    stockDf2 = stockDf.loc[:, ['Open', 'High', 'Low', 'Close']]
    stockDf2 = stockDf.tail(3)

    # 전환선이 기준선을 상향 돌파하며 기준선이 상승추세일 경우 매수 score + 1

    try:
        if stockDf.ConStanDif[-1] > 0 and stockDf.tail(10).ConStanDif.min() < 0:
            upDownMove = 0
            for i in range(1, 10):
                if stockDf.Standard[-1] > stockDf.Standard[-i + 1]:
                    upDownMove = upDownMove + 1
            if upDownMove > 7:
                score = score + 1
    except Exception as e:
        print(e, companyName)
        pass

    # 전환선이 기준선을 하향 돌파하며 기준선이 하강추세일 경우 매수 score - 1

    try:
        if stockDf.ConStanDif[-1] < 0 and stockDf.tail(10).ConStanDif.max() > 0:
            upDownMove = 0
            for i in range(1, 10):
                if stockDf.Standard[-1] > stockDf.Standard[-i + 1]:
                    upDownMove = upDownMove - 1
            if upDownMove < -6:
                score = score - 1
    except Exception as e:
        print(e, companyName)
        pass

        # 주가가 전환선, 기준선, 구름대를 상향 돌파할 때 매수 score + 1

    try:
        if stockDf2.max(axis=0).max() > stockDf2.Conversion.min() and stockDf2.max(
                axis=0).max() > stockDf2.Standard.min() and \
                stockDf2.max(axis=0).max() > stockDf2.Prespan1.min() and stockDf2.max(axis=0).max() > stockDf2.Prespan2.min():
            upDownMove = 0

            for i in range(1, 10):
                if stockDf.Close[-1] > stockDf.Close[-i + 1]:
                    upDownMove = upDownMove + 1
            if upDownMove > 7:
                score = score + 1
    except Exception as e:
        print(e, companyName)
        pass

    # 주가가 전환선, 기준선, 구름대를 하향 돌파할 때 매수 score - 1

    try:
        if stockDf2.max(axis=0).max() < stockDf2.Conversion.max() and stockDf2.max(
                axis=0).max() < stockDf2.Standard.max() and \
                stockDf2.max(axis=0).max() < stockDf2.Prespan1.max() and stockDf2.max(axis=0).max() < stockDf2.Prespan2.max():
            upDownMove = 0
            for i in range(1, 10):
                if stockDf.Close[-1] > stockDf.Close[-i + 1]:
                    upDownMove = upDownMove - 1
            if upDownMove < -7:
                score = score - 1
    except Exception as e:
        print(e, companyName)
        pass

    # 26일후의 선행스팬1이 상승추세일 경우 매수 score + 1
    # 26일후의 선행스팬1이 하승추세일 경우 매수 score - 1

    upDownMove = 0
    for i in range(15, 25):
        try:
            if stockDf.futureSpan[-15] > stockDf.futureSpan[-i + 1]:
                upDownMove = upDownMove + 1
            elif stockDf.futureSpan[-15] < stockDf.futureSpan[-i + 1]:
                upDownMove = upDownMove - 1
        except Exception as e:
            print(e, companyName)
            print("선행스팬")
            pass
    if upDownMove > 6:
        score = score + 1
    elif upDownMove < -6:
        score = score - 1

    # 점수가 2점 이상일때 stockBuySell = True(매수)
    if score > 1:
        stockBuySell = True
        buyStock(stockDf, codeNum, companyName, stockBuySell)

    # 점수가 -2점 이하일때 stockBuySell = False(매도)
    elif score < -1:
        stockBuySell = False
        buyStock(stockDf, codeNum, companyName, stockBuySell)

# 함수설명 : 일목균형 매수/매도 추천 그래프 저장
# author : 3기 황현빈
def buyStock(stockDf, codeNum, companyName, stockBuySell):
    # 그래프에서 날짜를 표시가기위해 datetime64 형의 인덱스를 String화하여 연도-월-일 형태로 저장
    candlesticks_df = stockDf.tail(200)

    day_list = []
    name_list = []

    for i, day in enumerate(candlesticks_df.index):
        if day.dayofweek == 0:  # 월요일에 해당하는 날짜값만 x축에 표시하기 위함
            day_list.append(i)
            name_list.append(day.strftime('%y-%m-%d'))

    candlesticks_df = candlesticks_df.reset_index()

    # 한글 폰트 지정
    font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
    rc('font', family=font_name)

    fig, ax = plt.subplots(figsize=(20, 10))

    ax.xaxis.set_major_locator(ticker.FixedLocator(day_list))
    ax.xaxis.set_major_formatter(ticker.FixedFormatter(name_list))

    ax.plot(candlesticks_df.index, list(candlesticks_df.Conversion), label="전환선", linewidth=0.7, color='#0496ff')
    ax.plot(candlesticks_df.index, list(candlesticks_df.Standard), label="기준선", linewidth=0.7, color='#991515')
    ax.plot(candlesticks_df.index, list(candlesticks_df.Prespan1), label="선행스팬1", linewidth=0.7, color='#008000')
    ax.plot(candlesticks_df.index, list(candlesticks_df.Prespan2), label="선행스팬2", linewidth=0.7, color='#ff0000')
    ax.plot(candlesticks_df.index, list(candlesticks_df.Laggingspan), label="후행스팬", linewidth=0.7, color='black')

    # green cloud
    ax.fill_between(candlesticks_df.index, candlesticks_df['Prespan1'], candlesticks_df['Prespan2'], \
                    where=candlesticks_df['Prespan1'] > candlesticks_df['Prespan2'], facecolor='#008000', interpolate=True, alpha=0.25)
    # red cloud
    ax.fill_between(candlesticks_df.index, candlesticks_df['Prespan1'], candlesticks_df['Prespan2'], \
                    where=candlesticks_df['Prespan2'] > candlesticks_df['Prespan1'], facecolor='#ff0000', interpolate=True, alpha=0.25)

    candlestick2_ohlc(ax, candlesticks_df['Open'], candlesticks_df['High'], candlesticks_df['Low'], \
                      candlesticks_df['Close'], width=0.6, colorup='r', colordown='b', alpha=0.5)

    plt.xticks(rotation=45)
    plt.grid()

    # Chart info
    title = companyName + " (" + codeNum + ")"
    bgcolor = '#131722'
    grid_color = '#363c4e'
    spines_color = '#d9d9d9'
    # Axes
    plt.title(title, fontsize=20)
    plt.xlabel('날짜', fontsize=15)
    plt.ylabel('주가(원)', fontsize=15)

    ax.grid(linewidth='0.3')
    ax.spines['bottom'].set_color(spines_color)
    ax.spines['top'].set_color(spines_color)
    ax.spines['right'].set_color(spines_color)
    ax.spines['left'].set_color(spines_color)
    fig.tight_layout()
    ax.autoscale_view()
    plt.legend(loc='upper right', fontsize=15)

    tempToday = str(date.today())
    createFolder("./" + tempToday + "/매수추천")
    createFolder("./" + tempToday + "/매도추천")

    # stockBuySell = True 경우 매수 추천 저장
    if stockBuySell == True:
        tempStr = "./" + tempToday + "/매수추천/매수추천 - " + companyName + "(" + tempToday + ").png"
        plt.savefig(tempStr)
        print(companyName + "매수추천 저장 완료")

    # stockBuySell = False 경우 매도 추천 저장
    elif stockBuySell == False:
        tempStr = "./" + tempToday + "/매도추천/매도추천 - " + companyName + "(" + tempToday + ").png"
        plt.savefig(tempStr)
        print(companyName + "매도추천 저장 완료")

# 함수설명 : 일목균형 매수/매도 추천 그래프 저장을 위한 폴더 생성
# author : 3기 황현빈
def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error: Creating directory. ' + directory)



kospi_stocks = qc.download_stock_codes('kospi')
codeNum = list(kospi_stocks['종목코드'])
companyName = list(kospi_stocks['회사명'])

# for i in range(0, len(kospi_stocks)):
#     ichimokuDataFrame(codeNum[i], companyName[i])



#tc = earningsRate.earningCalc()

myCodeList = qc.get_code_list()
print(myCodeList) # ['005560', '101380', '114140', '064900', ...
print(len(myCodeList))

for i in myCodeList:
    data = getClosePrice(i,date.today() - timedelta(duration),date.today() - timedelta(1))
    madf = getDiffMAs(i,data,ma1,ma2)
    #print(i," ",qc.get_codename_by_codenum(i),madf)
    code_name = qc.get_codename_by_codenum(i)
    if madf is not None: # 마지막 ** 기간의 추세 확인
        tempX = list(range(0,last_period))
        tempY = madf[-(last_period)-1:-1]
        try:
            grad, intercept, r_square, p_value, std_err = stats.linregress(tempX, tempY)
            #print(grad, intercept, r_square*r_square, p_value, std_err) # p_value <= 05, r^2 >=0..64
            if grad >= 0 :

                print(">>>>> ",i," ",code_name," ", grad, " ", r_square*r_square, " ",p_value)
                print("     ---->",tempY)
                tempText = code_name
                tempText += ' grad: %4.2f, R^2: %4.2f, p_value: %4.2f' % (grad, r_square*r_square, p_value)

                fig = px.line(x=tempX, y=tempY, labels={'x': 'days', 'y': 'MA diff'}, title=tempText)
                # fig.show()
                tempToday = str(date.today())
                tempToday += " 회귀"
                if not os.path.exists(tempToday):
                    os.mkdir(tempToday)
                tempStr = tempToday+"/"+code_name + ".png"
                fig.write_image(tempStr)
                # print(fig)
        except Exception as e:
            print("Error Occurs while trying to get lineregress X:", tempX)
            print("Error Occurs while trying to get lineregress Y:",tempY)
            print("Exception e :",e)
    else:
        print(code_name," ", "ma diff gradient less than zero")

# pycharm에서 자신의 모듈 임포트하기 위해서 필요한 설정(mark as a source root)
# https://stackoverflow.com/questions/28705029/pycharm-error-no-module-when-trying-to-import-own-module-python-script
