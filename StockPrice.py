#!/usr/bin/env python
# coding: utf-8
# Create Date : 2020.07.14
# Author : 3기 이 상 민

# for removing warning's signs
import warnings
warnings.filterwarnings(action='ignore')

# for dataframe
import pandas as pd
import numpy as np

# for stockprice infomation
import FinanceDataReader as fdr

# for periods
from datetime import date, timedelta

# line regression
from scipy import stats



# variables for golden-cross
n1Gol = 5
n2Gol = 20
duration = 720
last_period = 50

# variables for bolingerband
nBol = 20

# variables for CCI
nCci = 20

# variables for MACD
n1Macd = 12
n2Macd = 26
n3Macd = 9

# variables for Stochastic
nStocastic = 5
tStocastic = 3

class StockPrice:
    def __init__(self, stock_code, startDay, endDay):
        self.stockDf = pd.DataFrame()
        today = date.today()
        if startDay >= today or endDay >= today or startDay > endDay:
            #         print("date Error #1")
            return None
        if stock_code is None:
            #         print("code Error #1")
            return None

        df = fdr.DataReader(stock_code, startDay, endDay)
        df["StockCode"] = stock_code
        self.stockDf = self.stockDf.append(df)
        self.stockDf.reset_index(inplace=True)

    # 골든 크로스 정보를 추출하여 반환
    def getDiffMAs(self, n1Gol, n2Gol):
        if n1Gol >= n2Gol:
            #         print("MA set error #1")
            return None
        if len(self.stockDf) == 0:
            #         print("dataFrame has no data - ",qc.get_codename_by_codenum(code))
            return None
        if len(self.stockDf) <= n1Gol:
            #         print("length of dataFrame is less than or equal to ma #1")
            return None
        #     과거로만 날개 펼침. 종가의 ma1, ma2 로 담음. request를 보내서 "close"라는 key로 종가값이 옴.

        latestData = self.stockDf.iloc[[len(stockPrice.stockDf) - 1]]

        # 거래중지가 아닌 경우
        if latestData["Volume"].values[0] > 0:
            self.stockDf["MA#1"] = np.round(self.stockDf["Close"].ewm(n1Gol).mean() ,2)
            self.stockDf["MA#2"] = np.round(self.stockDf["Close"].ewm(n2Gol).mean() ,2)
            self.stockDf["MA#Diff"] = self.stockDf["MA#1"] - self.stockDf["MA#2"]

            return self.stockDf

        return None

    # 볼린저 밴드 정보 추출하여 반환
    def getBolinger(self, nBol):
        latestData = self.stockDf.iloc[[len(stockPrice.stockDf) - 1]]

        # 거래중지가 아닌 경우
        if latestData["Volume"].values[0] > 0:
            self.stockDf["MA20"] = np.round(self.stockDf["Close"].rolling(window = nBol, center=False).mean() ,2)
            self.stockDf["BOL_UPPER"] = self.stockDf["MA20"] + 2 * self.stockDf["Close"].rolling(window = nBol, center=False).std()
            self.stockDf["BOL_LOWER"] = self.stockDf["MA20"] - 2 * self.stockDf["Close"].rolling(window = nBol, center=False).std()

            return self.stockDf

        return None

    # CCI(Commodity Channel Index) 정보 추출
    def getCCI(self, nCci):
        latestData = self.stockDf.iloc[[len(stockPrice.stockDf) - 1]]

        # 거래중지가 아닌 경우
        if latestData["Volume"].values[0] > 0:
            self.stockDf["M"] = (self.stockDf["High"] + self.stockDf["Low"] + self.stockDf["Close"]) / 3
            self.stockDf["MA"] = np.round(self.stockDf["M"].rolling(window =  nCci, center = False).mean() ,2)
            self.stockDf["ABS"] = abs(self.stockDf["M"] - self.stockDf["MA"])
            self.stockDf["D"] = np.round(self.stockDf["ABS"].rolling(window =  nCci, center = False).mean() ,2)
            self.stockDf["CCI"] = self.stockDf["M"] * self.stockDf["MA"] / (0.015 * self.stockDf["D"])

            return self.stockDf

        return None

    # MACD(Moving Average Convergence & Divergence) 정보 추출
    def getMACD(self, n1Macd, n2Macd, n3Macd):
        latestData = self.stockDf.iloc[[len(stockPrice.stockDf) - 1]]

        # 거래중지가 아닌 경우
        if latestData["Volume"].values[0] != 0:
            self.stockDf["MA12"] = np.round(self.stockDf["Close"].emw(n1Macd).mean() ,2)
            self.stockDf["MA26"] = np.round(self.stockDf["Close"].emw(n2Macd).mean() ,2)
            self.stockDf["MACD"] = self.stockDf["MA12"] - self.stockDf["MA26"]
            self.stockDf["SIGNAL"] = np.round(self.stockDf["MACD"].emw(n3Macd, center = False).mean() ,2)
            self.stockDf["Oscillator"] = self.stockDf["MACD"] - self.stockDf["SIGNAL"]

            return self.stockDf

        return None

    # OBV(On Balance Volume) 정보 추출
    def getOBV(self, n1Macd, n2Macd, n3Macd):
        latestData = self.stockDf.iloc[[len(stockPrice.stockDf) - 1]]

        # 거래중지가 아닌 경우
        if latestData["Volume"].values[0] != 0:
            self.stockDf["Obv"] = self.stockDf.iloc[[0]]["Volume"].values[0]

            for i in range(1, len(self.stockDf)):
                volume_prev = self.stockDf.iloc[[ i -1]].Volume.values[0]
                volume_curr = self.stockDf.iloc[[i]].Volume.values[0]

                if volume_prev > volume_curr:
                    self.stockDf.at[i, "Obv"] = volume_prev - volume_curr
                elif volume_prev < volume_curr:
                    self.stockDf.at[i, "Obv"] = volume_prev + volume_curr
                else:
                    self.stockDf.at[i, "Obv"] = volume_prev

            return self.stockDf

        return None

    # STOCHASTIC 정보 추출
    def getStochastic(self, nStocastic, tStocastic):
        latestData = self.stockDf.iloc[[len(stockPrice.stockDf) - 1]]

        # 거래중지가 아닌 경우
        if latestData["Volume"].values[0] != 0:
            self.stockDf["HighestPrice"] = np.round \
                (self.stockDf["Close"].rolling(window =  nStocastic, center = False).max() ,2)
            self.stockDf["LowestPrice"] = np.round(self.stockDf["Close"].rolling(window =  nStocastic, center = False).max()
                                                   ,2)
            self.stockDf["FastK"] = (self.stockDf['Close'] - self.stockDf["LowestPrice"]) / \
                        (self.stockDf["HighestPrice"] - self.stockDf["LowestPrice"]) * 100
            self.stockDf["SlowK"] = np.round(self.stockDf["FastK"].emw(nStocastic).mean(),2)
            self.stockDf["SlowD"] = np.round(self.stockDf["SlowK"].emw(tStocastic).mean(),2)

            return self.stockDf

        return None

    def showGoldenCross(self, last_period):
        if self.stockDf["MA#Diff"] is not None: # 마지막 ** 기간의 추세 확인. last_period 50?
            tempX = list(range(0,last_period))
            tempY = self.s tockDf["MA#Diff"].tolist()[-(last_period)-1:-1] # n -50에서 n까지 5일추세선과 20일 추세선의 값 차 이 를 가져옴
            try:
                #             grad는 기울기.
                grad, intercept, r_square, p_value, std_err = stats.linregress(tempX, tempY)
                # print(grad, intercept, r_square*r_square, p_value, std_err) # p_value <= 05, r^2 >=0..64
                #             날짜가 오늘과 가까워질수록 5일 추세선과 20일 추세선의 차이가 크다. 계속 올라갈 가능성 있다!
                #             그림 그린다
                if grad >= 0:
                    return self.stockDf
            except Exception as e:
                print("Error Occurs while trying to get lineregress X:", tempX)
                print("Error Occurs while trying to get lineregress Y:",tempY)
                print("Exception  e :",e)
        else:
            print("ma d iff gradient less than zero")

        return None