import json
import os
import random

class usersDB:
    
    def init():
        if os.path.exists("users.json"):
            with open("users.json","r") as fo:
                try:
                    user_dict = json.load(fo)
                except:
                    user_dict = {}
        else:
            with open("users.json","w") as fo:
                user_dict = {}
        return user_dict

    def create_new_user(name:str):
        user_dict[name] = {"color":f"#{(str(hex(random.randint(1,16777215)):06d)[2:].upper())}"}
        with open("users.json","w") as fp:
            fp.write(json.dumps(user_dict))

    def change_user_color(name:str,color):
        user_dict[name]["color"] = color
        with open("users.json","w") as fp:
            fp.write(json.dumps(user_dict))

    def get_user(name : str):
        return user_dict[name]

    def check_user_exists(name : str):
        return name in user_dict.keys()
    
    def set_color(name,color):
        user_dict[name]["color"] = color
        with open("users.json","w") as fo:
            fo.write(json.dumps(user_dict))

    global user_dict
    user_dict = init()

