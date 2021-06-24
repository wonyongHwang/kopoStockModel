###    Author: 김재현                           
###    Created: 2021.06.23
###    Description: MACD, OSC 값을 기준으로 판단한다.
##### 1. 기능
##### - seeAll = 4개월간 이동평균선이 상승국면에 있으나 1달간 단기 하락중인 종목 코드 리스트업
##### - search = 배당을 비롯한 세부정보 및 차트 제공 
##### 
##### 2. 제한사항
##### - 미국 주식의 경우에만 select 이용 가능
##### - 반복되는 코드, 잦은 전역변수 호출
##### - 코드 종료 시 검색한 차트 일괄 출현
##### 
##### 3. 참고링크
##### - https://md2biz.tistory.com/397 각종 지표별 의미
##### - https://nakyup.tistory.com/5 각종 지표 가공
##### - https://m.blog.naver.com/silvury/221312883764 배당정보 크롤링
       
###    Prerequisites : conda install -c anaconda pandas-datareader  
