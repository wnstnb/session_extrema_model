# from dbConn import engine
import yfinance as yf
import numpy as np
import pandas as pd
import datetime
import plotly.graph_objects as go
import lightgbm

def create_features(ticker_str):
    '''
    Function to create dataframe of features for top/bottom model.
    '''
    ticker = yf.Ticker(ticker_str)
    df = ticker.history(period='5d',interval='5m')
    df = df.loc[
        (df.index.time >= datetime.time(9,30)) &\
        (df.index.time < datetime.time(16,0)),
    ['Open','High','Low','Close']]
    df.columns = ['open','high','low','close']

    df['time'] = df.index.time
    df['eod_close'] = df.groupby(df.index.date)['close'].tail(1)
    df['prev_close'] = df['eod_close'].shift(1)
    df['prev_close'] = df['prev_close'].ffill()
    df['eod_close'] = df['eod_close'].bfill()
    df['green_day'] = df['eod_close'] > df['prev_close']

    df['eod_close_pts'] = df['eod_close'] - df['prev_close']
    df['eod_close_pct'] = df['eod_close_pts'] / df['prev_close']

    for day in sorted(set(df.index.date)):
        day_str = datetime.datetime.strftime(day, '%Y-%m-%d')
        day_open = df.loc[day_str, 'open'].iloc[0]
        df.loc[day_str, 'lod'] = df.loc[day_str, 'low'].min()
        df.loc[day_str, 'label_lod'] = (df.loc[day_str, 'low'] == df.loc[day_str, 'lod']).astype(int)
        
        df.loc[day_str, 'hod'] = df.loc[day_str, 'high'].max()
        df.loc[day_str, 'label'] = (df.loc[day_str, 'high'] == df.loc[day_str, 'hod']).astype(int)
        df.loc[day_str, 'day_open'] = day_open
        df.loc[day_str, 'day_open_pts'] = df.loc[day_str, 'close'] - df.loc[day_str, 'day_open']
        df.loc[day_str, 'day_open_pct'] = df.loc[day_str, 'day_open_pts'] / df.loc[day_str, 'day_open']
        df.loc[day_str, 'prev_close_pts'] = df.loc[day_str, 'close'] - df.loc[day_str, 'prev_close']
        df.loc[day_str, 'prev_close_pct'] = df.loc[day_str, 'prev_close_pts'] / df.loc[day_str, 'prev_close']

        # Lowest low
        df.loc[day_str, 'lowest_low'] = df.loc[day_str, 'low'].expanding().min()
        df.loc[day_str, 'lowest_low'] = df.loc[day_str, 'lowest_low'].shift(1)
        df.loc[day_str, 'lowest_low'] = df.loc[day_str, 'lowest_low'].ffill()
        df.loc[day_str, 'lowest_low_mag'] = (df.loc[day_str, 'close'] / df.loc[day_str, 'lowest_low']) - 1

        # Highest high
        df.loc[day_str, 'highest_high'] = df.loc[day_str, 'high'].expanding().max()
        df.loc[day_str, 'highest_high'] = df.loc[day_str, 'highest_high'].shift(1)
        df.loc[day_str, 'highest_high'] = df.loc[day_str, 'highest_high'].ffill()
        df.loc[day_str, 'highest_high_mag'] = (df.loc[day_str, 'close'] / df.loc[day_str, 'highest_high']) - 1

        # Shifted
        df.loc[day_str, 'prev_close_pct_n1'] = df.loc[day_str, 'prev_close_pct'].shift(1)
        df.loc[day_str, 'prev_close_pct_n2'] = df.loc[day_str, 'prev_close_pct'].shift(2)
        df.loc[day_str, 'prev_close_pct_n3'] = df.loc[day_str, 'prev_close_pct'].shift(3)

        df.loc[day_str, 'day_open_pct_n1'] = df.loc[day_str, 'day_open_pct'].shift(1)
        df.loc[day_str, 'day_open_pct_n2'] = df.loc[day_str, 'day_open_pct'].shift(2)
        df.loc[day_str, 'day_open_pct_n3'] = df.loc[day_str, 'day_open_pct'].shift(3)


    df['gap_open'] = df['day_open'] - df['prev_close']
    df['gap_open_pct'] = df['gap_open'] / df['prev_close']

    df = df.loc[
        (df.index.time >= datetime.time(9,45)) &\
        (df.index.time < datetime.time(16,0))
    ]

    return df.dropna(subset=[
        'prev_close_pct',
        'gap_open_pct',
        'day_open_pct_n3',
        'prev_close_pct_n3'
    ])

def create_preds_df(df_feats, hod_model1, lod_model1, gd_model1):
    predicted_proba_hod = hod_model1.predict_proba(df_feats)[:,-1]
    predicted_proba_lod = lod_model1.predict_proba(df_feats)[:,-1]
    predicted_proba_gd = gd_model1.predict_proba(df_feats)[:,-1]
    df_viz = df_feats.copy()
    df_viz['pred_hod'] = predicted_proba_hod
    df_viz['pred_lod'] = predicted_proba_lod
    df_viz['pred_gd'] = predicted_proba_gd
    return df_viz

def create_viz(df_viz, date_str):

    df_use = df_viz.loc[date_str:date_str]
    
    fig = go.Figure(data=[go.Candlestick(x=df_use.index,
                open=df_use['open'],
                high=df_use['high'],
                low=df_use['low'],
                close=df_use['close'])])

    fig.add_trace(go.Scatter(x=df_use.index, y=df_use['pred_hod'], mode='lines', name='pred_hod', yaxis='y2', line=dict(color='#ff5f5f')))
    fig.add_trace(go.Scatter(x=df_use.index, y=df_use['pred_lod'], mode='lines', name='pred_lod', yaxis='y2', line=dict(color='#3399cc')))
    fig.add_trace(go.Scatter(x=df_use.index, y=df_use['pred_gd'], mode='lines', name='pred_gd', yaxis='y2', line=dict(color='#9400d3')))

    fig.add_shape(
        type="line",
        x0=df_use.index.min(),
        x1=df_use.index.max(),
        y0=0.5,
        y1=0.5,
        yref='y2',
        line=dict(
            color="Red",
            width=1.5,
            dash="dash",
        )
    )

    max_high = df_use['high'].max()
    max_high_time = df_use['high'].idxmax()

    min_low = df_use['low'].min()
    min_low_time = df_use['low'].idxmin()

    fig.add_annotation(
        x=max_high_time,
        y=max_high,
        text=f"{str(int(max_high))}",
        showarrow=True,
        font=dict(
            family="Courier New, monospace",
            size=12,
            color="#ffffff"
        ),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=20,
        ay=-30,
        bordercolor="#c7c7c7",
        borderwidth=1,
        borderpad=1,
        bgcolor="#ff5f5f",
        opacity=0.8
    )

    fig.add_annotation(
        x=min_low_time,
        y=min_low,
        text=f"{str(int(min_low))}",
        showarrow=True,
        font=dict(
            family="Courier New, monospace",
            size=12,
            color="#ffffff"
        ),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=20,
        ay=30,  # Adjust the y offset for the annotation
        bordercolor="#c7c7c7",
        borderwidth=1,
        borderpad=1,
        bgcolor="#3399cc",
        opacity=0.8
    )

    latest_close_time = df_use.index[-1]
    latest_close = df_use['close'].iloc[-1]

    fig.add_annotation(
        x=latest_close_time,
        y=latest_close,
        text=f"{str(int(latest_close))}",
        showarrow=True,
        font=dict(
            family="Courier New, monospace",
            size=12,
            color="#ffffff"
        ),
        align="center",
        arrowhead=0,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=40,
        ay=0,
        # bordercolor="#c7c7c7",
        borderwidth=1,
        borderpad=1,
        bgcolor="#000000",
        opacity=0.8
    )

    fig.update_layout(
        template='plotly_dark',
        yaxis=dict(
            tickformat='.0f'
        ),
        yaxis2=dict(
            overlaying='y',
            side='right',
            tickformat=".0%",
            showgrid=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        title='OHLC vs Prediction Over Time',
        xaxis_rangeslider_visible=False
    )

    return fig