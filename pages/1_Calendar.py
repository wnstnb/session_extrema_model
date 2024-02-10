import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(
    page_title='Calendar',
    page_icon='📆',
)

st.title('📆 Economic Calendar')
st.text("Use this to see what significant events are scheduled. Don't be offsides.")

# HTML code
html_code = """
<iframe src="https://sslecal2.investing.com?columns=exc_flags,exc_currency,exc_importance,exc_actual,exc_forecast,exc_previous&importance=2,3&features=datepicker,timezone,filters&countries=5&calType=day&timeZone=8&lang=1" style="width:100vw; height:100vh;" frameborder="0" allowtransparency="true" marginwidth="0" marginheight="0"></iframe>
<div class="poweredBy" style="font-family: Arial, Helvetica, sans-serif;">
    <span style="font-size: 11px;color: #333333;text-decoration: none;">Real Time Economic Calendar provided by 
        <a href="https://www.investing.com/" rel="nofollow" target="_blank" style="font-size: 11px;color: #06529D; font-weight: bold;" class="underline_link">Investing.com</a>.
    </span>
</div>
"""

# Display the HTML code
html(html_code, height=750)