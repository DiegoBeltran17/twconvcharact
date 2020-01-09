import pandas as pd
from datetime import timedelta


def set_timestamp(ds):
    ds['timestamp'] = pd.to_datetime(ds['created_at'])
    #ds.timestamp.head()
    print('converted to datetime!')