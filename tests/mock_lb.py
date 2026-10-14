import pandas as pd
import numpy as np
import os

os.makedirs('data/raw', exist_ok=True)
dm = pd.read_csv('data/raw/dm.csv')
usubjids = dm['USUBJID'].unique()

lb_data = []
np.random.seed(42)

for u in usubjids:
    for test in ['GLUCOSE', 'HEMOGLOBIN', 'CHOLESTEROL']:
        for day in [1, 15, 30, 45, 60, 90]:
            if test == 'GLUCOSE':
                val = np.random.normal(100, 15)
            elif test == 'HEMOGLOBIN':
                val = np.random.normal(14, 1.5)
            else:
                val = np.random.normal(180, 25)
                
            lb_data.append({
                'USUBJID': u,
                'LBTESTCD': test[:3],
                'LBTEST': test,
                'LBDTC': f'2014-01-{str((day%28)+1).zfill(2)}',
                'LBSTRESN': val,
                'LBSTRESU': 'mg/dL' if test != 'HEMOGLOBIN' else 'g/dL'
            })

pd.DataFrame(lb_data).to_csv('data/raw/lb.csv', index=False)
print('Created lb.csv')
