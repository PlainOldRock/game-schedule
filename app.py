import streamlit as st
from streamlit_calendar import calendar
import authlib as auth
import webbrowser
from requests_oauthlib import OAuth2Session
import json
import os
import user_cntl

scope = ['identify']

client_id = st.secrets["discord"]["client_id"]
client_secret = st.secrets["discord"]["client_secret"]
redirect_uri = st.secrets["discord"]["redirect_uri"]

authorization_base_url = f'https://discord.com/oauth2/authorize'
token_url = 'https://discord.com/api/oauth2/token'
user_info_url = 'https://discord.com/api/users/@me'

user_info = None

def get_discord_auth_url():
    discord = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = discord.authorization_url(authorization_base_url)
    st.session_state['oauth_state'] = state
    return authorization_url

@st.cache_data
def fetch_user_info(code):
    discord = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    token = discord.fetch_token(token_url, client_secret=client_secret, code=code)
    response = discord.get(user_info_url)
    return response.json()

query_params = st.query_params
if 'code' in query_params:
    user_info = fetch_user_info(query_params['code'])
    st.success(f"Logged in as {user_info['username']}")
    st.image(f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png")
else:
    auth_url = get_discord_auth_url()
    st.link_button("Log in to Save",auth_url)


st.title("Gaming Week Part 2 Schedule")


calendar_options = {
    "editable": "true",
    "navLinks": "true",
    "selectable": "true",
    "initialView": "timeGridWeek",
    "start": "2025-05-26",
    "end": "2025-05-31",
    "slotMinTime": "17:00:00",
    "slotMaxTime": "23:00:00",
    "firstDay": 1,
    "selectMirror": "true",
    "timeZone": "America/New_York",
    "headerToolbar": {
        "left": "today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay",
    },
    "validRange": {
        "start": "2025-05-26",
        "end": "2025-06-02"  # End is exclusive, so use the day after June 1st
    },
    "expandRows": True,
    "allDaySlot": False,
}

def get_initial_events():
    if os.path.exists("data.json"):
        with open("data.json","r") as fo:
            arr = json.load(fo)
    else:
        arr = []
    return arr

# Use cached events as default
if "events" not in st.session_state:
    st.session_state["events"] = get_initial_events()

def run_cal():
    state = calendar(
        events=st.session_state.get("events"),
        options=calendar_options,
        custom_css="""
        .fc-event-past {
            opacity: 0.8;
        }
        .fc-event-time {
            font-style: italic;
        }
        .fc-event-title {
            font-weight: 700;
        }
        .fc-toolbar-title {
            font-size: 2rem;
        }
        """,
    )
    return state

state = run_cal()
# Store selected range in session state

@st.dialog("Add Event")
def add_event(state):
    event_title = st.text_input("Event Title")
    event_game = st.text_input("Game")
    st.time_input("Start Time", value=state["select"]["start"])
    st.time_input("End Time", value=state["select"]["end"])

    if st.button("Add Event"):
        st.session_state['events'].append({
            "start": state["select"]["start"],
            "end":state["select"]["end"],
            "title": event_title,
            "user": user_info['username']
        })
        st.rerun()

if user_info is not None:
    if state["callback"] == 'select':
        add_event(state)
    if st.button("Save Events"):
        with open("data.json", "w") as fo:
            json.dump(st.session_state['events'], fo)
        st.success("Events saved successfully!")
    if user_info["username"] == "plainoldrock":
        del_on = st.toggle("Delete Events")
        if state["callback"] == 'eventClick' and del_on:
            for e in st.session_state['events']:
                if e["title"] == state["eventClick"]["event"]["title"]:
                    st.session_state['events'].remove(e)
                    st.write("Event removed")
                    st.rerun()
                    break

#st.write(st.session_state['events'])

