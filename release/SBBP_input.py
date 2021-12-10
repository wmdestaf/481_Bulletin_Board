from SBBP_constants import *

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
n_actions = len(actions.split('\n')) - 2 #multiline strings are weird...


'''
    Requests a user for a boolean [Y/N] until they provide one, with the given prompt.
    @param prompt the prompt to give
    @return True if the user's input starts with a 'y' of any case, or False if
    it begins with a 'n' of any case, or is empty.
'''
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

'''
    Requests a user to input a series of positive integers with the provided prompt,
    seperated by commas. Each integer must be positive. If nothing is provided,
    returns an empty list.
    @param prompt The prompt to provide to the user
    @return A list containing each provided integer (or an empty list, if none are)
'''
def get_int_csv(prompt):
    while True:
        x = input(prompt + " ")
        if not x:
            return []
            
        try:
            ret = [int(y) for y in x.split(",")]
            if any(n < 0 for n in ret): #no such thing as a negative msg id
                raise ValueError
            return ret
        except ValueError:
            pass

'''
    Requests a user to input an integer with the provided prompt.
    The integer must be positive.
    @param prompt The prompt to provide to the user
    @return The integer inputted by the user
'''
def get_int(prompt):
    while True:
        try:
            x = int(input(prompt + " "))
            if x < 0: #no such thing as a negative user id
                raise ValueError
        except ValueError:
            continue
            
        return x
    
'''
    Requests a user to input a string with the provided prompt.
    The string must not be empty, or contain the control characters 0xFC,0xFD,0xFE, or 0xFF
    @param prompt The prompt to provide to the user
    @return The string inputted by the user
'''
def get_str(prompt):
    while True:
        s = input(prompt + " ")
        if not s or any(ASCII_REPR(control) in s for control in range(FIELDSEP,END + 1)):
            continue
        return s
    
user = -1 #The 'User ID' to be returned on a call to get_user
    
'''
    Returns the current User ID
    @return The current User ID
'''
def get_user():
    return user
    
'''
    Sets the current user ID from an input with provided 'prompt'
    @param prompt The input to provide
'''
def set_user(prompt):
    global user
    user = get_int(prompt)

'''
    Main function to request client input.
    First, provides client with list of options, forced to select from
    Then, request client input parameters according to specific format respective 
    to the option selected.
    @return [The associated opcode selected, The associated operand selected]
    @return None if the user has chosen to 'exit'
'''
def get_client_input():
    print("What would you like to do, user [" + str(get_user()) + "]?")

    while True: 
        print(actions)
        
        #Force user to provide a valid selection
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
    
'''
    Small little interactive prompt for testing purposes.
'''
if __name__ == "__main__": 
    set_user("User?")
    
    while True:
        res = get_client_input()
        if not res:
            break
        print(res)