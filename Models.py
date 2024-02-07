import streamlit as st
import pandas as pd
import numpy as np
import datetime
import joblib
from viz import *
# from streamlit_autorefresh import st_autorefresh
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
        "hod_model_cv":"models/hod_model_cv_spx.joblib",
        "lod_model_cv":"models/lod_model_cv_spx.joblib",
        "gd_model_cv":"models/gd_model_cv_spx.joblib",
        "suffix":"SPX"
    },
    "^NDX":{
        "hod_model":"models/hod_model_ndx.joblib",
        "lod_model":"models/lod_model_ndx.joblib",
        "gd_model":"models/gd_model_ndx.joblib",
        "hod_model_cv":"models/hod_model_cv_ndx.joblib",
        "lod_model_cv":"models/lod_model_cv_ndx.joblib",
        "gd_model_cv":"models/gd_model_cv_ndx.joblib",
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
        # "^RUT", # Removing, as there isn't a good realtime-ish datasource for it rn
        "^GSPC",
    ]
)

with st.sidebar:
    model_type_select = st.selectbox(label='Model Type', options=['Main', 'CV'])
    st.success(f'{model_type_select} loaded!')


# Function to convert time string to seconds past midnight
def convert_time_to_seconds(time_series):
    return time_series.apply(lambda x: x.hour * 3600 + x.minute * 60 + x.second)

def apply_convert_time_to_seconds(x):
    return x.apply(convert_time_to_seconds)


df_feats = create_features(ticker_select)

# Test
if model_type_select == 'Main':
    hod_model = joblib.load(ticker_dict[ticker_select]['hod_model'])
    lod_model = joblib.load(ticker_dict[ticker_select]['lod_model'])
    gd_model = joblib.load(ticker_dict[ticker_select]['gd_model'])

# elif model_type_select == 'CV':
#     hod_model = joblib.load(ticker_dict[ticker_select]['hod_model_cv'])
#     lod_model = joblib.load(ticker_dict[ticker_select]['lod_model_cv'])
#     gd_model = joblib.load(ticker_dict[ticker_select]['gd_model_cv'])

df_viz = create_preds_df(df_feats, hod_model, lod_model, gd_model)
viz_dates = sorted(set(df_viz.index.date))[::-1]
date_select = st.selectbox(
    label='Select date for view',
    options=viz_dates
)

bt = st.button("Manual Refresh")
if bt:
    st.rerun()


date_select_str = datetime.datetime.strftime(date_select, '%Y-%m-%d')
fig = create_viz(df_viz, date_select_str)
st.plotly_chart(fig, use_container_width=True)
df_res = df_viz[['highest_high','lowest_low','pred_hod','pred_lod']]
df_summary = df_res.loc[date_select_str:date_select_str]
df_summary['highest_high'] = df_summary['highest_high'].astype(int)
df_summary['lowest_low'] = df_summary['lowest_low'].astype(int)
df_summary = df_summary.loc[:,['lowest_low','highest_high','pred_lod','pred_hod']]
st.dataframe(df_summary[::-1])
# st.dataframe(df_viz.tail())