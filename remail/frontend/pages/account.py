import streamlit as st
import re

st.title("Account Management")

st.subheader("Profile Information")
# example for editing account information
with st.form("profile_form"):
    st.text_input("First Name", value="Max")
    st.text_input("Last Name", value="Mustermann")
    st.text_input(
        "Email", value="max.mustermann@example.com", disabled=True
    )  # E-Mail is not editable
    st.date_input("Date of Birth", value=None)

    # Submit-Button for the formula
    submitted_profile = st.form_submit_button("Update Profile")
    if submitted_profile:
        st.success("Your profile has been updated!")

st.markdown("---")

st.subheader("Change Password")
with st.form("password_form"):
    old_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    submitted_password = st.form_submit_button("Change Password")
    if submitted_password:
        if new_password == old_password:
            st.error("The new password must be different from the current password.")
        elif new_password != confirm_password:
            st.error("Passwords do not match. Please try again.")
        elif not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]+$", new_password):
            st.error(
                "The password must contain at least one letter and one number, and no special characters."
            )
        else:
            st.success("Your password has been changed!")

st.markdown("---")

st.subheader("Account Actions")
# example button for logging out
if st.button("Log Out"):
    st.info("You have been logged out. See you next time!")
# example button for deleting account
if st.button("Delete Account"):
    st.warning(
        "Are you sure you want to delete your account? This action cannot be undone."
    )
