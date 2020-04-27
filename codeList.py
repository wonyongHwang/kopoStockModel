import urllib.parse
import pandas as pd

MARKET_CODE_DICT = {
    'kospi': 'stockMkt',
    'kosdaq': 'kosdaqMkt',
    'konex': 'konexMkt'
}
NO_MATCHING_DATA = "no matching data"

DOWNLOAD_URL = 'https://kind.krx.co.kr/corpgeneral/corpList.do'

class queryCodeList:
    status = 0
    def __init__(self):
        self.stocks = pd.DataFrame()
        #self.status = 0 # 코드 활성화시 status는 static객체가 아니라 instance 객체로 "별도" 취급
    def zeroFill(self, columnValue):
        columnValue = str(columnValue)
        outValue = columnValue.zfill(6)
        return outValue

    def get_stock_info(self, market=None, delisted=False):
        params = {'method': 'download'}

        if market.lower() in MARKET_CODE_DICT:
            ## marketType 키 추가
            params['marketType'] = MARKET_CODE_DICT[market]
            print(market.lower()+" market key is exist")
        else:
            #params['searchType'] = 13
            print("invalid market")

        # make url  key=value & key = value
        params_string = urllib.parse.urlencode(params)
        request_url = DOWNLOAD_URL+"?"+params_string

        df = pd.read_html(request_url, header=0)[0]
        df["종목코드"] = df.종목코드.apply(self.zeroFill)
        self.stocks = df
        return df

    def get_code_list(self, market=None):
        if len(self.stocks) == 0:
            self.get_stock_info('kospi')
        # ['005560', '101380', '114140', '064900', '028780', '085450', '000470', '000980', '028930',
        return self.stocks["종목코드"].tolist()

    def get_codename_by_codenum(self, codenum):
        retStr:String = None

        if codenum is None:
            retStr = "code num was not given"
            return retStr
        if len(self.stocks) == 0:
            self.get_stock_info('kospi')
        try:
            retStr = self.stocks.loc[self.stocks['종목코드'] == codenum]['회사명'].iloc[0]
        except:
            print("<<EXCEPTION>> no matching data #001")

        return retStr if retStr is not None else NO_MATCHING_DATA

    @staticmethod
    def isEqualCode(code1, code2):
        return code1 == code2

    @classmethod
    def getStockInfo(cls):
        print(cls.status)

    def getStockInfo2(self):
        print(self.status)

tc = queryCodeList()
print(tc.get_code_list())
tc2 = queryCodeList()
# print(queryCodeList.isEqualCode("1010","1010"))
'''
queryCodeList.status = 1
queryCodeList.getStockInfo() # 1
queryCodeList.status = -1
tc.getStockInfo()  # -1
queryCodeList.status = -2
tc2.getStockInfo() # -2

tc3 = queryCodeList()
tc3.getStockInfo2() # 생성자에 status = 0 을 넣으면 0, 없으면 -2;;; 
# 생성자에서 self.status = 0로 쓰는 의미->status는 이제부터 정적객체가 아니라 인스턴스 객체로 다룬다는 의미

queryCodeList.getStockInfo() # -2 # 파이썬 클래스의 정적영역은 동적생성과 무관하게 상태를 유지
'''

# stocks = tc.get_stock_info('kospi')
# print(stocks.head(100))

# stocks1 = tc.get_code_list('kospi')
# print(stocks1)
# print(len(stocks1)) # 1388

#print(tc.get_codename_by_codenum("005560")) # JS전선