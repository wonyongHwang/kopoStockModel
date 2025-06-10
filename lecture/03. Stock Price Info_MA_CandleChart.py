import FinanceDataReader as fdr
import matplotlib.pyplot as plt
from datetime import date, timedelta
import platform
from matplotlib import font_manager, rc

# 한글 폰트 설정
if platform.system() == 'Windows':
    font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
    rc('font', family=font_name)
elif platform.system() == 'Darwin':
    rc('font', family='AppleGothic')

# 1. 코스피 종목 불러오기
stocks = fdr.StockListing('KOSPI')

# 컬럼 목록 확인 (디버깅용)
print("컬럼 목록:", stocks.columns)


samsung = stocks[stocks['Name'] == '삼성전자']
samsung_code = stocks.loc[stocks['Name'] == '삼성전자', 'Code'].values[0]

# 결과 확인


stock_code = samsung_code
# 2. 가격 데이터 불러오기
start = date.today() - timedelta(days=50)
end = date.today()

stock_data = fdr.DataReader(stock_code, start, end)

# 3. 시세 및 지표 그리기
stock_data['MA_5'] = stock_data['Close'].rolling(window=5).mean()
stock_data['MA_20'] = stock_data['Close'].rolling(window=20).mean()
stock_data['diff'] = stock_data['MA_5'] - stock_data['MA_20']

plt.figure(figsize=(16,10))

# Close price and MAs
plt.subplot(3, 1, 1)
plt.plot(stock_data.index, stock_data['Close'], label='Close')
plt.plot(stock_data.index, stock_data['MA_5'], label='MA 5')
plt.plot(stock_data.index, stock_data['MA_20'], label='MA 20')
plt.title(f"{samsung} 분석")
plt.legend()

# Volume
plt.subplot(3, 1, 2)
plt.bar(stock_data.index, stock_data['Volume'], color='gray')
plt.title('거래량')

# diff
plt.subplot(3, 1, 3)
plt.plot(stock_data.index, stock_data['diff'], color='green')
plt.axhline(y=0, color='red', linestyle='--')
plt.title('MA 차이 (5일 - 20일)')

plt.tight_layout()
plt.show()
