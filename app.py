import streamlit as st
import pandas as pd
import numpy as np
import datetime
import joblib
from viz import *

st.set_page_config(
    page_title='Session Extrema Model',
    page_icon='⚡',
)

st.title('⚡ Session Extrema Model')

ticker_dict = {
    "^GSPC":{
        "hod_model":"models/hod_model_spx.joblib",
        "lod_model":"models/lod_model_spx.joblib"
    },
    "^NDX":{
        "hod_model":"models/hod_model_ndx.joblib",
        "lod_model":"models/lod_model_ndx.joblib"
    },
    "^RUT":{
        "hod_model":"models/hod_model_rut.joblib",
        "lod_model":"models/lod_model_rut.joblib"
    }
}

ticker_select = st.selectbox(
    label='Choose Ticker', 
    options=[
        "^NDX",
        "^RUT",
        "^GSPC",
    ]
)

# Function to convert time string to seconds past midnight
def convert_time_to_seconds(time_series):
    return time_series.apply(lambda x: x.hour * 3600 + x.minute * 60 + x.second)

def apply_convert_time_to_seconds(x):
    return x.apply(convert_time_to_seconds)


df_feats = create_features(ticker_select)

hod_model = joblib.load(ticker_dict[ticker_select]['hod_model'])
lod_model = joblib.load(ticker_dict[ticker_select]['lod_model'])

df_viz = create_preds_df(df_feats, hod_model, lod_model)
viz_dates = sorted(set(df_viz.index.date))[::-1]
date_select = st.selectbox(
    label='Select date for view',
    options=viz_dates
)
date_select_str = datetime.datetime.strftime(date_select, '%Y-%m-%d')
fig = create_viz(df_viz, date_select_str)
st.plotly_chart(fig, use_container_width=True)
# st.dataframe(df_viz.tail())