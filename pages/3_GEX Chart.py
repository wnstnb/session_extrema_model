from data import cboe_model as cboe
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from st_aggrid import AgGrid,ColumnsAutoSizeMode


st.set_page_config(
    page_title = 'GEX Chart',
    page_icon = '📊'
    )
st.title('📊 GEX Chart')

st.markdown('Data is delayed by at least 15 minutes. Backend powered by [CBOEDashboard](https://github.com/deeleeramone/CBOEDashboard).')
with st.form(key='GEXChart'):
    col1, col2, col3 = st.columns(3)
    t = col1.text_input(label='Ticker', value=None, placeholder='Enter Ticker', label_visibility='collapsed')
    col_select = col2.selectbox(label='Metric', index=None, options=['NetGEX','Vol','OI'], placeholder='Choose a metric', label_visibility='collapsed')
    show_chart = col3.form_submit_button(label='Show Chart')
    if show_chart:
        if not t or not col_select:
            col_error = 'Choose a metric.' if not col_select else ''
            t_error = 'Enter a Ticker.' if not t else ''
            err_msg = ' '.join([t_error, col_error])
            st.error(body = err_msg, icon = '🚨')

        else:
            x = cboe.get_ticker_chains(t)
            x1 = x.reset_index()
            x1 = x1.fillna(0)
            # Round GEX to M
            # x1['GEX'] = x1['GEX'] / 1000000
            x1.loc[x1['Type'] == 'Call', 'NetGEX'] = x1['GEX']
            x1.loc[x1['Type'] == 'Put', 'NetGEX'] = x1['GEX'] * -1
            x1.loc[x1['Type'] == 'Call', 'CallGEX'] = x1['GEX']
            x1.loc[x1['Type'] == 'Put', 'PutGEX'] = x1['GEX']
            x1.loc[x1['Type'] == 'Put', 'Vol'] = x1['Vol'] * -1

            df_stats = x1.groupby('Expiration')[['NetGEX', 'GEX', 'CallGEX', 'PutGEX', 'Vol', 'OI']].sum()
            df_stats['Vol/OI'] = df_stats['Vol'] / df_stats['OI']
            x1.loc[x1['Type'] == 'Put', 'OI'] = x1['OI'] * -1

            # df_stats = df_stats.reset_index()
            df_stats['Expiration'] = [f'{y.year}-{y.month:02}-{y.day:02}' for y in df_stats.index]
            # for c in ['GEX', 'NetGEX', 'CallGEX', 'PutGEX']:
            #     # Format for the table
            #     df_stats[c] = [f'{v:.01f}' for v in df_stats[c]]
            df_stats = df_stats[[
                'Expiration', 'GEX', 'NetGEX', 'CallGEX', 'PutGEX', 'Vol', 'OI', 'Vol/OI'
            ]]
            with st.expander(label='Summary Table by Expiry'):
                st.dataframe(df_stats, use_container_width=True, hide_index=True)
                # AgGrid(
                #     df_stats, 
                #     update_mode="Value_changed", 
                #     # fit_columns_on_grid_load = True,
                #     columns_auto_size_mode = ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW
                # )

            total_gamma = x1[col_select].sum()
            x2 = x1.groupby('Strike')[[col_select]].sum()
            x3 = x1.sort_values('Expiration', ascending=False).groupby('Expiration')[[col_select]].sum()
            last_df = cboe.get_ticker_info(t)[0]
            last_price = last_df.loc['Current Price'].iloc[0]
            last_trade_time = last_df.loc['Last Trade Time'].iloc[0]        
            st.text(f'NetGEX ($M): {total_gamma:,.0f}\nAs of: {last_trade_time}')

            fig = px.bar(x2, orientation='h')
            fig.add_hline(y=last_price, line_dash="dot", line_color="cyan", name='test')

            # fig.update_traces(marker=dict(color=np.where(x2['GEX'] > 0, '#3399ff', '#ff5f5f')))
            fig.update_traces(
                marker=dict(color=np.where(x2[col_select] > 0, '#3399ff', '#ff5f5f'), 
                            line=dict(color=np.where(x2[col_select] > 0, '#3399ff', '#ff5f5f'))
                            )
            )
            fig.update_layout(
                title_text=f'Ticker: {t}',
                template='plotly_dark',
                font_color='#ffffff',
                width=600,
                height=800,
                yaxis_tickformat=',',
                xaxis=dict(showgrid=True, gridcolor='#2f2f2f')
            )

            top_3_strikes = x2.nlargest(3, col_select)
            bottom_3_strikes = x2.nsmallest(3, col_select)

            for i in top_3_strikes.index:
                fig.add_annotation(
                    x=top_3_strikes.loc[i, col_select],
                    y=i,
                    text=f'{i:.0f}',
                    showarrow=True,
                    arrowhead=1,
                    ax=20,
                    ay=-20
                )

            for i in bottom_3_strikes.index:
                fig.add_annotation(
                    x=bottom_3_strikes.loc[i, col_select],
                    y=i,
                    text=f'{i:.0f}',
                    showarrow=True,
                    arrowhead=1,
                    ax=-20,
                    ay=20
                )

            st.plotly_chart(fig)
