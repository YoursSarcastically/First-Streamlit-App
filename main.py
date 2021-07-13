# Import streamlit and pandas
import streamlit as st
import pandas as pd

# Reading files
df=pd.read_csv("my_data.csv")
df2=pd.read_csv("state_level_latest.csv")

# Define cols as beta_columns before you use them 5,5 means a square type
col1, col2 = st.beta_columns([5,5])

# Col 1
with col1:
    st.header("Covid 19 India Analysis")
    st.line_chart(df)

# Col2
with col2:
    st.header("State wise Data Analysis")
    st.dataframe(df2)




# Form type in streamlit
st.write("Tell us your feedback")

name=st.text_input('Enter your name')
feedback= st.text_area('Your feedback goes here!')
feed_but=st.button('Send Feedback!')


st.text('Made by Suraj Sharma with ❤️')