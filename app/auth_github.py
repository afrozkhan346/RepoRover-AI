import os
import requests
import streamlit as st
from urllib.parse import urlencode, urlparse, parse_qs
from . import roles

# --- Configuration ---
# Read from Streamlit secrets (or environment variables as fallback)
CLIENT_ID = st.secrets.get("GITHUB_CLIENT_ID") or os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("GITHUB_CLIENT_SECRET") or os.getenv("GITHUB_CLIENT_SECRET")
AUTH_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_API = "https://api.github.com/user"
SCOPES = "read:user user:email" # Scopes you requested

# --- Helper Functions ---

def get_auth_url(redirect_uri: str) -> str:
    """
    Generates the GitHub OAuth login URL.
    """
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "allow_signup": "true",
    }
    return f"{AUTH_URL}?{urlencode(params)}"

def exchange_code_for_token(code: str, redirect_uri: str) -> dict | None:
    """
    Exchanges the authorization code for an access token.
    """
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {"Accept": "application/json"}
    try:
        r = requests.post(TOKEN_URL, data=data, headers=headers, timeout=10)
        r.raise_for_status() # Raise an exception for bad status codes
        return r.json() # Contains 'access_token', 'scope', 'token_type'
    except requests.RequestException as e:
        print(f"Error exchanging code for token: {e}")
        st.error(f"Failed to get access token: {e}")
        return None

def fetch_github_user(access_token: str) -> dict | None:
    """
    Fetches the authenticated user's profile from GitHub.
    """
    headers = {"Authorization": f"token {access_token}", "Accept": "application/json"}
    try:
        r = requests.get(USER_API, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json() # user details: login, id, name, avatar_url, etc.
    except requests.RequestException as e:
        print(f"Error fetching user data: {e}")
        st.error(f"Failed to fetch user data: {e}")
        return None

def try_handle_oauth_flow(redirect_uri: str):
    """
    Call this early in your Streamlit app.
    It checks for the 'code' query param and, if found,
    completes the OAuth flow, setting st.session_state['user'].
    """
    q = st.query_params
    code = q.get("code")

    if code and not st.session_state.get("user"):
        print(f"OAuth callback: Found auth code: {code[:10]}...")
        with st.spinner("Authenticating with GitHub..."):
            try:
                token_resp = exchange_code_for_token(code, redirect_uri)
                if not token_resp or "access_token" not in token_resp:
                    st.error("Authentication failed: No access token received.")
                    st.query_params.clear()
                    return

                access_token = token_resp["access_token"]
                user = fetch_github_user(access_token)
                if not user:
                    st.error("Authentication failed: Could not fetch user profile.")
                    st.query_params.clear()
                    return

                # --- 2. FETCH AND ADD ROLES ---
                user_login = user.get("login")
                user_roles = roles.get_user_roles(user_login)
                print(f"Authentication successful for user: {user_login}, Roles: {user_roles}")

                # Store user info in session state
                st.session_state['user'] = {
                    "login": user.get("login"),
                    "name": user.get("name") or user.get("login"),
                    "id": user.get("id"),
                    "avatar": user.get("avatar_url"),
                    "access_token": access_token,
                    "roles": user_roles
                }

                # Clear the ?code=... from the URL bar
                st.query_params.clear()
                st.rerun() # Rerun to show the main app UI

            except Exception as e:
                print(f"Error during OAuth flow: {e}")
                st.error(f"Authentication error: {e}")
                st.query_params.clear() # Clear code on failure