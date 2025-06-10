import FinanceDataReader as fdr
import matplotlib.pyplot as plt

# 1. 조회할 기간 설정
start_date = '2023-01-01'
end_date = '2024-12-31'

# 2. 데이터 불러오기
kospi = fdr.DataReader('KS11', start_date, end_date)  # KOSPI
dji = fdr.DataReader('DJI', start_date, end_date)     # Dow Jones Industrial Average

# 3. 차트 출력
plt.figure(figsize=(14, 6))

# KOSPI
plt.subplot(1, 2, 1)
plt.plot(kospi.index, kospi['Close'], label='KOSPI')
plt.title('KOSPI Index')
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.grid(True)

# DJI
plt.subplot(1, 2, 2)
plt.plot(dji.index, dji['Close'], label='DJI', color='orange')
plt.title('Dow Jones Industrial Average')
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.grid(True)

plt.tight_layout()
plt.show()
