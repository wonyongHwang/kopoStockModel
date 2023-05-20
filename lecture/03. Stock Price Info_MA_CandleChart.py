import urllib.parse

import pandas as pd


MARKET_CODE_DICT = {

    'kospi': 'stockMkt',

    'kosdaq': 'kosdaqMkt',

    'konex': 'konexMkt'

}

DOWNLOAD_URL = 'https://kind.krx.co.kr/corpgeneral/corpList.do'



# 6자리 안되면 0으로 앞을 채워라.
def zeroFill(columnValue):

    columnValue = str(columnValue)

    outValue = columnValue.zfill(6)

    return outValue


def get_stock_codes(market=None, delisted=False):

    params = {'method': 'download'}

    if market.lower() in MARKET_CODE_DICT:

        ## marketType 키 추가

        params['marketType'] = MARKET_CODE_DICT[market]

        print(market.lower()+" market key is exist")

    else:

        print("invalid market")

    # make url  key=value & key = value
    params_string = urllib.parse.urlencode(params)

    request_url = DOWNLOAD_URL+"?"+params_string

    df = pd.read_html(request_url)[0]

    df["종목코드"] = df.종목코드.apply(zeroFill)
#     df["종목코드"] = df.종목코드.map('{:06d}'.format) # 동일 결과
#     06d : 숫자가 없는 칸은 0으로 맞춰줌.

    return df


# ##### 종목코드 가져오기

stocks = get_stock_codes('kospi')


# 매수 / 매도 결정 기본 예제 연습

stock_code = stocks.iloc[0]['종목코드']
stock_name = stocks.iloc[0]['회사명']
print(stock_name)
print(stock_code)
# 내가 원하는 종목을 가져올 수 있다 ( 여기까지 했다면 )
# 해당 조건식에 맞는 종목코드를 가져오기
# #### 가져올 회사 종목코드 - > 회사명 : 보험업 / 주요제품 : 손해보험

seek1 = "보험업"
seek2 = "손해보험"
seekCom = stocks.loc[(stocks.업종.str.upper() == seek1) & (stocks.주요제품.str.upper() == seek2)]

targetColumn = ["종목코드"]

seekStockCode = seekCom.loc[: ,targetColumn]



import FinanceDataReader as web
from datetime import date, timedelta
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import platform

print(platform.system())

if platform.system() == 'Windows':
    font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
    rc('font', family=font_name)
elif platform.system() == 'Darwin':
    rc('font', family='AppleGothic')
else:
    pass


end = date.today()
start = date.today() - timedelta(50) # datetime.datetime(2021,4,1)

STOCK = web.DataReader(stock_code, start, end)



STOCK['Close'].plot()
# print(plt.style.available)
# plt.style.use(['fivethirtyeight'])
plt.title(stock_name+" 종가 시세")
plt.show()

STOCK["MA_5"]=STOCK["Close"].rolling(window=5, min_periods=1).mean() # min_periods=1
STOCK["MA_20"]=STOCK["Close"].rolling(window=20, min_periods=1).mean()
STOCK["diff"]=STOCK["MA_5"]-STOCK["MA_20"]
STOCK.tail()


plt.figure(figsize = (16,10))

#price (가격)
plt.subplot(311)
plt.plot(STOCK.index, STOCK['Close'], label = 'Close')
plt.plot(STOCK.index, STOCK['MA_5'], label='MA 5day')
plt.plot(STOCK.index, STOCK['MA_20'], label='MA 20day')
plt.title(stock_name+"분석결과")
plt.legend(loc='best')

# volume (거래량)
plt.subplot(312)
plt.bar(STOCK.index, STOCK['Volume'], color='black')

#  이동평균 차이 (diff)
plt.subplot(313)
plt.rc('axes', unicode_minus=False)
plt.plot(STOCK.index, STOCK['diff'].fillna(0), color='g')
plt.axhline(y=0, color='r',linestyle=':', linewidth=3) # https://financedata.github.io/posts/matplotlib_hline_and_vline.html

plt.show()


