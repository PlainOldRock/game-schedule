import json
import os
import random


def init():
    if os.path.exists("users.json"):
        with open("users.json") as fo:
            user_dict = json.loads(fo)
    else:
        with open("users.json","w") as fo:
            user_dict = {}
    return user_dict

def create_new_user(user_dict:dict,name:str):
    user_dict[name] = {"color":hex(random.randint(1,16777215))}
    with open("users.json","w") as fp:
        fp.write(json.dumps(user_dict))

def change_user_color(user_dict:dict,name:str,color):
    user_dict["name"]["color"] = color
    with open("users.json","w") as fp:
        fp.write(json.dumps(user_dict))

