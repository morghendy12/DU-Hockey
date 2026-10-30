import streamlit as st

st.set_page_config(page_title="DU Hockey Dashboard", layout="wide")

pages = [st.Page("audience.py", title="Audience Profile", default=True),
         st.Page("partners.py", title="Partners")]
st.navigation(pages).run()
