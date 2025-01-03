import streamlit as st

st.title("Settings")

st.write("Manage your application settings here.")

# examples for settings
st.subheader("General")
dark_mode = st.checkbox("Enable Dark Mode")
notifications = st.checkbox("Enable Notifications")

st.subheader("Privacy")
data_sharing = st.radio(
    "Allow data sharing:", ("Allow all", "Allow essential only", "Do not allow")
)

st.subheader("Appearance")
font_size = st.slider("Select font size for emails:", 10, 30, 14)
