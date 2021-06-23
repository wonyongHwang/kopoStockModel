#####    Author: 김승현                         
#####    Created: 2021.06.16
#####    Description: crawling
#####    Prerequisite : conda install -c conda-forge fbprophet                                                                 
######    > kospi top50 기업의 정보, 재무제표 데이터 사용
######    > 선정 기업과 동일업종의 PER을 비교하여 저평가, 고평가 판단
######    > Bollinger Bands를 통해 상한선, 하한선 내 주가 기준 설정
######    > 선정 기업과 동일업종의 PBR을 비교하여 단기(매수/매도) 추천
######    > 'MA_5' > 'MA_20' (1.0, 0.0 -> sell buy) / GC & DC 시각화 