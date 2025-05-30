#file for db2json control
import mysql.connector
from mysql.connector import Error
import json
import random

class Db_conn:
    def __init__(self,db_user : str,db_pw : str):
        self.connection = None
        self.cursor = None
        self.connection = mysql.connector.connect(
            host='plainoldrock.duckdns.org',
            port="3306",
            database='DISCORD_SCHEDULE',
            user=str(db_user),
            password=str(db_pw),
            auth_plugin="mysql_native_password",
        )
        
        if self.connection is not None:
            self.cursor = self.connection.cursor(dictionary=True)
            print("MySQL connection is working")
        else:
            print("Error in MySQL Connection")
        
    def get_cursor(self):
        return self.cursor
    def get_connection(self):
        return self.connection

    def get_data(self,ex_props=True):
        cur = self.get_cursor()
        cur.execute("SELECT * FROM DISCORD_SCHEDULE.SCHEDULE_DATA")
        data_array = cur.fetchall()
        data_dict = {}
        for dd in data_array:
            if ex_props:
                data_dict[int(dd['ID'])] = {
                    "allDay":False,
                    "title":dd['TITLE'],
                    "start":dd['START'],
                    "end":dd['END'],
                    "id":dd["ID"],
                    "backgroundColor":dd["BGCOLOR"],
                    "extendedProps":{
                        "user":dd["USER"],
                        "game":dd["GAME"],
                        "created":dd["CREATED"]
                    }
                }
            else:
                data_dict[int(dd['ID'])] = {
                    "allDay":False,
                    "title":dd['TITLE'],
                    "start":dd['START'],
                    "end":dd['END'],
                    "id":dd["ID"],
                    "backgroundColor":dd["BGCOLOR"],
                    "user":dd["USER"],
                    "game":dd["GAME"],
                    "created":dd["CREATED"]
                }
        return data_dict

    def add_event(self,event_dict):
        cur = self.get_cursor()
        ex_str = (f"""INSERT INTO DISCORD_SCHEDULE.SCHEDULE_DATA (
            ALLDAY,
            TITLE,
            START,
            END,
            BGCOLOR,
            USER,
            GAME,
            CREATED
            ) 
            VALUES(
        0,
        '{event_dict['title']}',
        '{event_dict['start']}',
        '{event_dict['end']}',
        '{event_dict['backgroundColor']}',
        '{event_dict['user']}',
        '{event_dict['game']}',
        '{event_dict['created']}'
        )""")
        cur.execute(ex_str)
        ret = cur.fetchall()
        self.get_connection().commit()
        return True

    def update_all_event_colors(self,username : str, color : str):
        cur = self.get_cursor()
        cur.execute(f"UPDATE DISCORD_SCHEDULE.SCHEDULE_DATA SET BGCOLOR = '{color}' WHERE USER = '{username}' AND GAME != 'Work'")
        self.get_connection().commit()
        return True


    def del_event(self,id : int):
        cur = self.get_cursor()
        cur.execute(f"""DELETE FROM DISCORD_SCHEDULE.SCHEDULE_DATA WHERE ID = {id}""")
        self.get_connection().commit()
        return True

    def edit_event(self,id : int, field : str, new_val):
        cur = self.get_cursor()
        cur.execute(f"""UPDATE DISCORD_SCHEDULE.SCHEDULE_DATA SET {field} = '{new_val}' WHERE ID = {id}""")
        self.get_connection().commit()
        return True

    def get_event(self,id : int):
        cur = self.get_cursor()
        ex_str = f"SELECT * FROM DISCORD_SCHEDULE.SCHEDULE_DATA WHERE ID = '{id}'"
        print(ex_str)
        cur.execute(ex_str)
        raw_dict = cur.fetchone()
        if raw_dict is not None:
            event_dict = {}
            event_dict['id'] = id
            event_dict['allDay'] = raw_dict['ALLDAY']
            event_dict['title'] = raw_dict['TITLE']
            event_dict['start'] = raw_dict['START']
            event_dict['end'] = raw_dict['END']
            event_dict['backgroundColor'] = raw_dict['BGCOLOR']
            event_dict['extendedProps'] = {'user':raw_dict['USER'],'game':raw_dict['GAME'],'created':raw_dict['CREATED']}
        
            return event_dict
        else:
            return None
    def add_user(self,name, flag = ''):
        color = f"#{random.randint(1,16777215):06x}"

        cur = self.get_cursor()
        cur.execute(f"INSERT INTO DISCORD_SCHEDULE.USERS VALUE('{name}','{color}','{flag}')")
        self.get_connection().commit()
        return cur.fetchall()
    
    def check_user(self,name : str):
        cur = self.get_cursor()
        cur.execute(f"SELECT COUNT(*) U_CHECK FROM DISCORD_SCHEDULE.USERS WHERE USER = '{name}'")
        if cur.fetchone()['U_CHECK'] > 0:
            return True
        else:
            return False

    def set_user_color(self,name : str, color : str):
        cur = self.get_cursor()
        cur.execute(f"UPDATE DISCORD_SCHEDULE.USERS SET COLOR = '{color}' WHERE USER = '{name}'")
        self.get_connection().commit()

    def get_user_color(self,name : str):
        cur = self.get_cursor()
        cur.execute(f"SELECT COLOR FROM DISCORD_SCHEDULE.USERS WHERE USER = '{name}'")
        return cur.fetchone()['COLOR']

    def get_user_flag(self,name:str):
        cur = self.get_cursor()
        cur.execute(f"SELECT FLAG FROM DISCORD_SCHEDULE.USERS WHERE USER = '{name}'")
        return cur.fetchone()['FLAG']
    def close_conn(self):
        self.get_connection().commit()
        self.cursor.close()
        self.connection.close()
    def trunc_table(self,tb_name):
        cur = self.get_cursor()
        cur.execute(f"TRUNCATE DISCORD_SCHEDULE.{tb_name}")
        self.get_connection().commit()

def json_data_load(conn,file_name='data_load.json'):
    with open(file_name,'r') as fo:
        raw_json = json.load(fo)
    for event in raw_json.values():
        event['allDay'] = False
        event['extendedProps'] = {'user':event['user'],'game':event['game'],'created':event['created']}
        del event['id']
        conn.add_event(event)