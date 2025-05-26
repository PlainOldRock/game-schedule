import streamlit as st
from streamlit_calendar import calendar
import authlib as auth
import webbrowser
from requests_oauthlib import OAuth2Session
import json
import os
import user_cntl
import db_control
from datetime import date
from datetime import timedelta
from datetime import datetime

scope = ['identify']

client_id = st.secrets["discord"]["client_id"]
client_secret = st.secrets["discord"]["client_secret"]
redirect_uri = st.secrets["discord"]["redirect_uri"]
db_conn = db_control.Db_conn(st.secrets['db_conn']['db_user'],st.secrets['db_conn']['db_pw'])


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
    if query_params['code'] == 'test_user':
        user_info = {'username':'tester'}
        st.info("logged in as Test User")
    else:
        user_info = fetch_user_info(query_params['code'])
        st.success(f"Logged in as {user_info['username']}")
        st.image(f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png")

        
    if user_info["username"] == "plainoldrock":
        
        admin_mode = st.toggle("Admin Mode",value=False)
        if admin_mode:
            reset_button = st.button("Reset")
            if reset_button:
                empty_dict = {}
                with open("data.json","w") as fd:
                    fd.write("{}")
                with open("users.json","w") as fd:
                    fd.write("")
            #id_arr = []
            #for event in st.session_state["events"]:
            #    id_arr.append(event['id'])
            #id_sel = st.select_box("id to edit",value=None)
            #if id_sel is not None:
            #    del st.session_state["events"][int(id_sel)]
            # WOrk pls
    else:
        admin_mode = False
    if user_cntl.usersDB.check_user_exists(user_info["username"]):
        mouse = 1
    else:
        user_cntl.usersDB.create_new_user(user_info["username"])
else:
    auth_url = get_discord_auth_url()
    admin_mode = False
    st.link_button("Log in to Save",auth_url)


st.title("Gaming Week Part 2 Schedule")

def update_colors(username : str, color):
    for event in st.session_state["events"].values():
        if event["user"] == username:
            event["backgroundColor"] = color
    st.rerun()

@st.dialog("Settings")
def user_setting():
    set_color = st.color_picker("Pick Your Color", value = user_cntl.usersDB.get_user(user_info["username"])["color"])
    if st.button("Apply"):
        user_cntl.usersDB.set_color(user_info["username"],set_color)
        update_colors(user_info["username"],set_color)

if user_info is not None:
    editable="true"
    setting_button = st.button("settings")
    if setting_button:
        user_setting()
else:
    editable="false"

cal_start = "2025-05-26"
cal_end = "2025-05-31"
calendar_options = {
    "editable": "false",
    "navLinks": "true",
    "selectable": "true",
    "initialView": "timeGridWeek",
    "start": cal_start,
    "end": cal_end,
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
    dic = db_conn.get_data(ex_props=False)
    global admin_mode
    if admin_mode:
        st.write(dic)
    return dic

# Use cached events as default
if "events" not in st.session_state:
    st.session_state["events"] = get_initial_events()


def run_cal():
    state = calendar(
        events=list(st.session_state["events"].values()),
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

def get_new_id():
    if os.path.exists("increment.txt"):
        with open("increment.txt","r") as fo:
            inc = int(fo.read())
        with open("increment.txt","w") as fp:
            fp.write(str(inc + 1))
    else:
        inc = 1
        with open("increment.txt","w") as fp:
            fp.write(str(inc))
    return str(inc)

def check_today_entries():
    num_entry = 0
    global user_info
    
    for event in st.session_state["events"].values():
        #st.write(f"{event["created"]} == {date.today()}")
        if user_info["username"] == event["user"]:
            if event["created"] == str(date.today()):
                num_entry += 1
    return num_entry

def check_time_inv(check_time_str,start_time_str,end_time_str):
    str_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    check_time = datetime.strptime(check_time_str,str_format)
    start_time = datetime.strptime(start_time_str,str_format)
    end_time = datetime.strptime(end_time_str,str_format)
    if (check_time < end_time) and (check_time > start_time):
        return True
    else:
        return False

#added comment
def check_three_hour_limit(start_time,end_time):
    str_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    return abs(datetime.strptime(start_time,str_format) - datetime.strptime(end_time,str_format)).total_seconds() <= (3 * 3600)

def replace_time_on_date(date,time):
    return date[:11] + time + ".000Z"

@st.dialog("Add Event Select")
def add_event(state):
    event_title = st.text_input("Event Title")
    event_game = st.text_input("Game")
    event_start = replace_time_on_date(state["select"]["start"],str(st.time_input("Start Time", value=state["select"]["start"])))
    
    event_end = replace_time_on_date(state["select"]["end"],str(st.time_input("End Time", value=state["select"]["end"])))
    global admin_mode
    if st.button("Add Event"):
        if check_today_entries() < 2 or admin_mode:
            if check_three_hour_limit(event_start,event_end) or admin_mode:
                flag = False
                for event in st.session_state["events"].values():
                    if check_time_inv(event_start,event["start"],event["end"]):
                        flag = True
                        break
                    elif check_time_inv(event_end,event["start"],event["end"]):
                        flag = True
                        break
                if flag == False:
                    my_id = get_new_id()
                    db_conn.add_event({
                        "start": event_start,
                        "end":event_end,
                        "title": event_title + f"\n{user_info['username']}\n{event_game}",
                        "user": user_info['username'],
                        "game": event_game,
                        "created":str(date.today()),
                        "backgroundColor":user_cntl.usersDB.get_user(user_info["username"])["color"]
                    })
                    get_initial_events()
                    st.rerun()
                else:
                    st.error("Events Can't Overlap")
            else:
                st.error("Event Can't be longer than 3 hours!")
        else:
            st.error("You can only add 2 events per day!")
        
@st.dialog("Add Event Button")
def add_event_button():
    event_title = st.text_input("Event Title")
    event_game = st.text_input("Game")
    
    event_date = str(st.date_input("Day",min_value=cal_start,max_value=cal_end,format="YYYY-MM-DD"))
    
    #"%Y-%m-%dT%H:%M:%S.%fZ"
    start_time = st.time_input("start time",value="17:00")
    end_time = st.time_input("end time",value="20:00")
    event_start = f"{event_date}T{start_time.hour:02d}:{start_time.minute:02d}:00.000Z"
    event_end = f"{event_date}T{end_time.hour:02d}:{end_time.minute:02d}:00.000Z"
    global admin_mode
    if st.button("Add Event"):
        if check_today_entries() < 2 or admin_mode:
            if check_three_hour_limit(event_start,event_end) or admin_mode:
                flag = False
                for event in st.session_state["events"].values():
                    if check_time_inv(event_start,event["start"],event["end"]):
                        flag = True
                        break
                    elif check_time_inv(event_end,event["start"],event["end"]):
                        flag = True
                        break
                if flag == False:
                    my_id = get_new_id()
                    db_conn.add_event({
                        "start": event_start,
                        "end":event_end,
                        "title": event_title + f"\n{user_info['username']}\n{event_game}",
                        "user": user_info['username'],
                        "game": event_game,
                        "created":str(date.today()),
                        "backgroundColor":user_cntl.usersDB.get_user(user_info["username"])["color"]
                    })
                    get_initial_events()
                    st.rerun()
                else:
                    st.error("Events Can't Overlap")
            else:
                st.error("Event Can't be longer than 3 hours!")
        else:
            st.error("You can only add 2 events per day!")

def replace_time(date_time_str,newtime):
    return date_time_str[:11] + str(newtime) + ".000Z"

@st.dialog("Edit Event")
def edit_event(state,id,user_name):
    global admin_mode
    if admin_mode:
        st.info(f"admin mode {admin_mode}")
    if (user_name == st.session_state["events"][id]["user"]) or admin_mode == True:  
        edit_title = st.text_input("title",value=st.session_state["events"][id]["title"])
        start_val = st.time_input("start time",value=st.session_state["events"][id]["start"])
        end_val = st.time_input("end time",value=st.session_state["events"][id]["end"])
        save_button = False
        delete_button = False

        flag = False
        for event in st.session_state["events"].values():
            
            if check_time_inv(replace_time(event["start"],start_val),event["start"],event["end"]):
                flag = True
                break
            elif check_time_inv(replace_time(event["end"],end_val),event["start"],event["end"]):
                flag = True
                break
        if flag == True and admin_mode==False:
            st.error("Events Can't Overlap")
        elif start_val > end_val:
            st.error("Start Time must be before end night")
        elif (check_three_hour_limit(st.session_state["events"][id]["start"][:11] + str(start_val) + ".000Z",st.session_state["events"][id]["end"][:11] + str(end_val) + ".000Z") == False) and admin_mode == False:
            st.error("Max 3 Hour Reservation")
        else:
            edit_start = str(start_val)
            edit_end = str(end_val)
            edit_game = st.text_input("Game",value=st.session_state["events"][id]["game"])
    
            save_button = st.button("Save Changes")
            delete_button = st.button("Delete Event")
        if save_button:
            st.session_state["events"][id]["title"] = edit_title
            st.session_state["events"][id]["start"] = st.session_state["events"][id]["start"][:11] + edit_start + ".000Z"
            st.session_state["events"][id]["end"] = st.session_state["events"][id]["end"][:11] + edit_end + ".000Z"
            st.session_state["events"][id]["game"] = edit_game
            st.rerun()
        elif delete_button:
            del st.session_state["events"][id]
            st.rerun()
    else:
        st.write("You can only edit your own events!")
if user_info is not None:
    if "callback" in state:
        add_event_called = st.button("Add New Event")
        if add_event_called:
            add_event_button()
        elif state["callback"] == 'select':
            add_event(state)
            st.toast("Save your changes with 'Save Events'!")
        elif state["callback"] == 'eventClick':
           #st.write(state)
            edit_event(state,int(state["eventClick"]["event"]["id"]),user_info["username"])
    if st.button("Save Events"):
        with open("data.json", "w") as fo:
            json.dump(st.session_state['events'], fo)
        st.success("Events saved successfully!")
if admin_mode:
    st.write(state)
    st.json(st.session_state["events"])