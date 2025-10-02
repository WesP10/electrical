# components.py
from dash import dcc
def callback_store():
    return dcc.Store(id='callback-store', storage_type='session')