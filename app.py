import streamlit as st
import pandas as pd
import numpy as np
import datetime
import joblib
from viz import *
from streamlit_autorefresh import st_autorefresh
import time


st.set_page_config(
    page_title='Session Extrema Model',
    page_icon='⚡',
)

st.title('⚡ Session Extrema Model')

ticker_dict = {
    "^GSPC":{
        "hod_model":"models/hod_model_spx.joblib",
        "lod_model":"models/lod_model_spx.joblib",
        "gd_model":"models/gd_model_spx.joblib",
        "suffix":"SPX"
    },
    "^NDX":{
        "hod_model":"models/hod_model_ndx.joblib",
        "lod_model":"models/lod_model_ndx.joblib",
        "gd_model":"models/gd_model_ndx.joblib",
        "suffix":"NDX"
    },
    "^RUT":{
        "hod_model":"models/hod_model_rut.joblib",
        "lod_model":"models/lod_model_rut.joblib",
        "gd_model":"models/gd_model_rut.joblib",
        "suffix":"RUT"
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
gd_model = joblib.load(ticker_dict[ticker_select]['gd_model'])

df_viz = create_preds_df(df_feats, hod_model, lod_model, gd_model)
viz_dates = sorted(set(df_viz.index.date))[::-1]
date_select = st.selectbox(
    label='Select date for view',
    options=viz_dates
)

col1, col2 = st.columns(2)
with col1:
    auto_refresh = st.toggle('Enable Auto-Refresh', value=False)
    if auto_refresh:
        st_autorefresh(interval=60*1000, key="autorefresh_data")

with col2:
    if auto_refresh:
        tn = datetime.datetime.now() + datetime.timedelta(seconds=60)
        bt = st.button(f"Next refresh at: {tn.hour}:{tn.minute}:{tn.second}", disabled=True)
    else:
        bt = st.button("Manual Refresh")
        if bt:
            st.rerun()


date_select_str = datetime.datetime.strftime(date_select, '%Y-%m-%d')
fig = create_viz(df_viz, date_select_str)
st.plotly_chart(fig, use_container_width=True)
df_res = df_viz[['time','high','low','pred_hod','pred_lod']]
df_summary = df_res.loc[date_select_str:date_select_str]
df_summary['session_low'] = df_summary['low'].expanding().min().round()
df_summary['session_high'] = df_summary['high'].expanding().max().round()
df_summary = df_summary.loc[:,['time','session_low','session_high','pred_lod','pred_hod']]
df_summary = df_summary[::-1]
df_summary = df_summary.set_index('time')
st.dataframe(df_summary)
# st.dataframe(df_viz.tail())