import streamlit as st
import requests
import json

# API endpoint
API_URL = "http://localhost:8000"

# Function to get JWT token
def get_token(username, password):
    response = requests.post(
        f"{API_URL}/token",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        st.error("Invalid username or password")
        return None

# Function to make authenticated API call
def api_call(endpoint, payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}{endpoint}", json=payload, headers=headers)
    return response.json()

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None

# Streamlit app
def main():
    st.title("PDF  URL DB Chatbot")

    # Login form
    if not st.session_state.token:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            token = get_token(username, password)
            if token:
                st.session_state.token = token
                st.success("Logged in successfully!")
                st.empty()  # Clear the success message
                st.rerun()  # Rerun the app to update the UI

    # Query form (only shown if logged in)
    if st.session_state.token:
        st.subheader("Query System")
        query = st.text_input("Enter your query")
        if st.button("Submit Query"):
            if query:
                response = api_call("/query", {"query": query}, st.session_state.token)
                if isinstance(response, dict):
                    if "answer" in response:
                        st.write("Response:", response["answer"])
                    elif "error" in response:
                        st.error(f"Error: {response['error']}")
                    elif "detail" in response:
                        st.error(f"Error: {response['detail']}")
                    else:
                        st.json(response)  # Display the full response as JSON
                        st.warning("Unexpected response format. Please check the API.")
                else:
                    st.error("Invalid response from server")
            else:
                st.warning("Please enter a query")

        # Logout button
        if st.button("Logout"):
            st.session_state.token = None
            st.rerun()  # Rerun the app to update the UI

if __name__ == "__main__":
    main()