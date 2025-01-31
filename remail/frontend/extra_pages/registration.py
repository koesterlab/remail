import streamlit as st
import re  # Für Regex-Validierung


# CSS-Styles für Buttons
st.markdown(
    """
    <style>
    .custom-text {
        font-size: 130px;
        color: green;
        font-weight: bold;
        text-align: center
    }
    .custom-text2 {
        text-align: center;
        color:orange;
    }
    .custom-button {
        background-color: #4CAF50; /* Grün */
        border: none;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }
    .register-button {
        color: white;
        padding: 10px 20px;
        text-align: center;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
        <p class= custom-text> ReMail </p>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
        <p class= custom-text2><i> Welcome to our new EMail App </i></p>
        <br>
        <br>
        <br>
        <br>
    """,
    unsafe_allow_html=True,
)


# text_Input

address= st.text_input ("Enter your E-Mail adress ","")

address2= st.text_input ("Repeat your E-Mail adress ","")

password = st.text_input(
    "Create a password",
    type="password",
    help="At least 1 letter and 1 number, no special characters.",
)

password2 = st.text_input("Repeat password", type="password")


# Validierungslogik und Registrierung
if st.button("Register"):
    errors = []

    if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]+$", password):
        errors.append(
            "Your password must contain at least one letter, one number, and no special characters."
        )

    if adress != adress2:
        errors.append("The email addresses should match.")
    if password != password2:
        errors.append("The passwords should match.")

    if errors:
        for error in errors:
            st.error(error)
        if adress != adress2:
            adress2 = ""
        if password != password2:
            password2 = ""
    else:
        st.success("Registration successful!")
        # Neue Seite simulieren
        st.experimental_set_query_params(page="home")
        st.markdown(
            """
            <meta http-equiv="refresh" content="0; url=/home" />
            """,
            unsafe_allow_html=True,
        )
