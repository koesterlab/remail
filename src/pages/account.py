import streamlit as st

st.title("Account Management")

st.subheader("Profile Information")
# example for editing account information
with st.form("profile_form"):
    st.text_input("First Name", value="John")
    st.text_input("Last Name", value="Doe")
    st.text_input("Email", value="john.doe@example.com", disabled=True)  # E-Mail nicht bearbeitbar
    st.date_input("Date of Birth", value=None)
    
    # Submit-Button for the formula
    submitted_profile = st.form_submit_button("Update Profile")
    if submitted_profile:
        st.success("Your profile has been updated!")

st.markdown("---")

st.subheader("Change Password")
# example for changing password
with st.form("password_form"):
    old_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    
    # submit-button for changing password
    submitted_password = st.form_submit_button("Change Password")
    if submitted_password:
        if new_password == confirm_password:
            st.success("Your password has been changed!")
        else:
            st.error("Passwords do not match. Please try again.")

st.markdown("---")

st.subheader("Account Actions")
# example button for logging out
if st.button("Log Out"):
    st.info("You have been logged out. See you next time!")
# example button for deleting account
if st.button("Delete Account"):
    st.warning("Are you sure you want to delete your account? This action cannot be undone.")
