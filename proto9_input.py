from proto9_constants import *

actions = '''
  1. Post Message
  2. Delete Message
  3. Get Messages
  4. Get Message Count
  5. Get New Message Count
  6. Create Board
  7. Delete Board
  8. Quit
'''
n_actions = 8

#to facilitate the addition of new options
options_string = ("Post Message","Delete Message","Get Messages","Get Message Count",
                          "Get New Message Count","Create Board","Delete Board","Quit")
actions = "\n".join("{:3d}. {}".format(idx, val) for idx, val in enumerate(options_string,start=1))

def get_bool(prompt):
    while True:
        x = input(prompt + " ").upper()
        if not x:
            print("Assumed [N]")
            return False
        elif x[0] == 'Y':
            return True
        elif x[0] == 'N':
            return False

def get_int_csv(prompt):
    while True:
        x = input(prompt + " ")
        if not x:
            return []
            
        try:
            ret = [int(y) for y in x.split(",")]
            if any(n < 0 for n in ret):
                raise ValueError
            return ret
        except ValueError:
            pass

def get_int(prompt):
    while True:
        try:
            x = int(input(prompt + " "))
            if x < 0:
                raise ValueError
        except ValueError:
            continue
            
        return x
    
def get_str(prompt):
    while True:
        s = input(prompt + " ")
        if not s or any(ASCII_REPR(control) in s for control in range(FIELDSEP,END + 1)):
            continue
        return s
    
user = -1
    
def get_user():
    return user
    
def set_user(prompt):
    global user
    user = get_int(prompt)

def get_client_input():
    print("What would you like to do?")
    
    #force the user to make a decision
    while True: 
        print(actions)
        try:
            choice = int(input(">> "))
            if choice < 1 or choice > n_actions:
                raise ValueError
        except ValueError:
            continue
        break
    
    if choice == 1:   #POST MESSAGE -> BOARD USER SUBJECT MESSAGE
        return ("POST_MSG",[get_int("Board?"), get_user(), get_str("Subject?"), get_str("Message?")])
    elif choice == 2: #DELETE MESSAGE -> BOARD USER MESSAGE
        return ("DELT_MSG",[get_int("Board?"), get_user(), get_int("Message ID?")])
    elif choice == 3: #GET MESSAGE -> BOARD USER (OPTIONAL MESSAGE IDS) SUBJECTS_ONLY NEW_ONLY
        return ("GET_MSGS",[get_int("Board?"), get_user(), get_int_csv("Message ID's? (comma-seperated, empty to ignore)"),
                get_bool("Subjects Only? [Y/N]"), get_bool("New Messages Only? [Y/N]")])
    elif choice == 4: #GET MESSAGE COUNT -> BOARD
        return ("GET_M_CT",[get_int("Board?")])
    elif choice == 5: #GET NEW MSG COUNT -> BOARD USER
        return ("GETNEWCT",[get_int("Board?"), get_user()])
    elif choice == 6: #CREATE BOARD -> BOARD USER
        return ("CREATE_B",[get_int("Board?"), get_user()])
    elif choice == 7: #DELETE BOARD -> BOARD USER
        return ("DELETE_B",[get_int("Board?"), get_user()])
    elif choice == 8: #EXIT
        return None
     
if __name__ == "__main__": 
    set_user("User?")
    
    while True:
        res = get_client_input()
        if not res:
            break
        print(res)