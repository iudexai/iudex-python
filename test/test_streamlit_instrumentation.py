import streamlit as st

from iudex import instrument, start_trace, end_trace
instrument(
    service_name="streamlit-app",
    env="prod",
    iudex_api_key="",
)

token = start_trace(name="streamlit-app")

st.write("""
# My first app
Hello *world!*
""")

number = st.slider("Pick a number", 0, 100)
st.write("number = ", number)
print("number:", number)

pet = st.radio("Pick a pet", ["cats", "dogs"])
print("pet:", pet)

color = st.color_picker("Pick a color")
print("color:", color)

end_trace(token)
