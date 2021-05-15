#필요 라이브러리 정의
import numpy as np
import matplotlib.pyplot as plt

# 커맨드뷰에서 차트 시여
#%matplotlib inline
# 팝업 창 활용하여 차트 시연
# %matplotlib tk
size = 50
#사이즈만큰 랜덤한 데이터 생성 (정규분포: 평균0, 표준편차1)
y=np.random.standard_normal(size)
x=range(size)
plt.plot(x,y)
plt.show()