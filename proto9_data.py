from proto9_constants import *
import time
import copy

boards = []

####################################STRUCTS#####################################
class Message:
    def __init__(self, m_id, creator_id, subject, text):
        self.m_id    = m_id
        self.creator = creator_id
        self.created = time.time()
        self.subject = subject
        self.text    = text
    
    def __eq__(self, other):
        if not isinstance(other, Message):
            return False
    
        for attribute in dir(self): #State made up of primitives, so this much is fine.
            if getattr(self,attribute) != getattr(other, attribute):
                return False
        return True
    
    def __repr__(self):
        return "\nid: {}, by: {}, when: {}\nsubj: {:10s},msg: {:20s}\n".format(
            self.m_id, self.creator, self.created, self.subject, self.text)
    
class Board:
    def __init__(self, b_id, creator_id):
        self.b_id     = b_id
        self.creator  = creator_id
        self.messages = []
        self.m_id_ctr = 1
        self.msgs_map = {}
    
    def next_id(self):
        self.m_id_ctr += 1
        return self.m_id_ctr - 1
        
    def __repr__(self):
        return "\nid: {}, by: {}, next: {}\nmessages: {}\nmap: {}\n".format(
            self.b_id, self.creator, self.m_id_ctr, 
            self.messages, self.msgs_map)
####################################HELPER#####################################
def get_board_by_id(b_id):
    #https://stackoverflow.com/a/3785811
    return next((b for b in boards if b.b_id == b_id), None)
    
def get_message_by_id(board, m_id):
    return next((m for m in board.messages if m.m_id == m_id), None)
####################################BOARDS######################################   
def create_b(b_id, u_id):
    if get_board_by_id(b_id):
        return (False,[BOARDDNE])
        
    boards.append(Board(b_id, u_id))
    return (True,[])
    
def delete_b(b_id, u_id):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return (False,[BOARDDNE])
    elif board.creator != u_id: #User does not have permission
        return (False,[UNOPERMS])
       
    boards.remove(board)
    return (True,[])
#############################BOARD INFORMATION##################################    
def get_m_ct(b_id):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return (False,[BOARDDNE])
    return (True,len(board.messages))
    
def getnewct(b_id, u_id):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return (False,[BOARDDNE])

    '''
    A new message, in the context of a user's ID, must satisfy ALL of the following properties:
        Was created on a board after the user's most recent 'All' query for the board
        Does not exist in the board's uID -> new Message mapping
    '''
    try: #Are we keeping track of unread messages for this user?
        return (True,len(board.msgs_map[u_id]))
    except KeyError: #If not, they've read *none* of them!  
        return (True,len([msg for msg in board.messages if msg.creator != u_id]))
    
##############################MESSAGE INPUT#####################################   
def post_msg(b_id, u_id, subject, msg_text):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return (False,[BOARDDNE])
    
    #get and autoincrement post counter
    m_id = board.next_id()
    
    message = Message(m_id, u_id, subject, msg_text)
    board.messages.append(message)
    return (True,[])
    
def delt_msg(b_id, u_id, m_id):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return (False,[BOARDDNE])
        
    message = get_message_by_id(board, m_id)
    if message.creator != u_id:
        return (False,[UNOPERMS])
    
    board.messages.remove(message)
    
    #REMOVE ID FROM ALL UNREAD LISTS
    for m_id_list in board.msgs_map.values():
        try:
            m_id_list.remove(m_id)
        except KeyError:
            pass
    return (True,[])
##############################MESSAGE OUTPUT####################################
'''
@param b_id The ID of the board to target
@param m_ids An optional list of message ids' to specifically include
@param subjects_only Flag to determine if only subjects (not message contents) should be returned
@param new_only False to ignore, or a specific user ID to return the 'new' messages on the board
@return False if the board doesn't exist, or the board has no messages
'''
def get_msgs(b_id, u_id, m_ids, subjects_only=False, new_only=False):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return (False,[BOARDDNE])
    elif not board.messages:
        return (False,[RESEMPTY])

    msgs = copy.deepcopy(board.messages) #this can be avoided.

    if len(m_ids):
        msgs = [msg for msg in msgs if msg.m_id in m_ids]
    if new_only:
        try:
            msgs = [msg for msg in msgs if msg.m_id in board.msgs_map[u_id]]
        except KeyError:
            board.msgs_map[u_id] = [msg.m_id for msg in board.messages if msg.creator != u_id]
            msgs = [msg for msg in msgs if msg.m_id in board.msgs_map[u_id]]

    #optimize and update unread messages for a user
    #however, requesting the subject lines certainly does not count as 'reading' the message!
    if not subjects_only:
        for msg in msgs:
            try:
                if msg.m_id in board.msgs_map[u_id]:
                    board.msgs_map[u_id].remove(msg.m_id)
            except KeyError: #no such map for the given user...create it!
                board.msgs_map[u_id] = [msg_.m_id for msg_ in board.messages if msg_.creator != u_id]
                if msg.m_id in board.msgs_map[u_id]:
                    board.msgs_map[u_id].remove(msg.m_id)

    if not subjects_only:
        ret = [False,[[msg.m_id, msg.creator, msg.created, msg.subject, msg.text] for msg in msgs]]
    else:
        ret = [True,[[msg.m_id, msg.creator, msg.created, msg.subject, "ignore"] for msg in msgs]]
        
    if not ret[1]:
        return (False, [RESEMPTY])
    else:
        return (True, ret)
##################################################################################
        
boards = [Board(0, -1)]

def EXECUTE_ARGS_SERVER(opcode, args):
    if opcode == "GET_M_CT":
        return get_m_ct(args[0])
    elif opcode == "GETNEWCT":
        return getnewct(args[0], args[1])
    elif opcode == "POST_MSG":
        return post_msg(args[0], args[1], args[2], args[3])
    elif opcode == "DELT_MSG":
        return delt_msg(args[0], args[1], args[2])
    elif opcode == "GET_MSGS":
        return get_msgs(args[0], args[1], args[2], subjects_only=args[3], new_only=args[4])
    elif opcode == "CREATE_B":
        return create_b(args[0], args[1])
    elif opcode == "DELETE_B":
        return delete_b(args[0], args[1])
        
def EXECUTE_ARGS_CLIENT(opcode, args):
    if opcode == "GET_M_CT":
        return "Messages on board: {:d}".format(args[0])
    elif opcode == "GETNEWCT":
        return "New messages on board: {:d}".format(args[0])
    elif opcode == "POST_MSG":
        return "Message posted successfully."
    elif opcode == "DELT_MSG":
        return "Message deleted successfully."
    elif opcode == "GET_MSGS":
        subjs_only = args[0]
        msgs = args[1]
        if not subjs_only:
            return ("\n" + "#"*80 + "\n").join("No. {:d}\nBy: {:d}\nAt: {}\nSubject: {}\nMessage:\n{}".format(
                                 msg[0], msg[1], time.asctime(time.localtime(msg[2])),
                                 msg[3], msg[4]) for msg in msgs)
        else:
            return ("\n" + "#"*80 + "\n").join("{:60s} (No. {:d}, By: {:d})".format(msg[3], msg[0], msg[1]) for msg in msgs)
    elif opcode == "CREATE_B":
        return "Board created successfully."
    elif opcode == "DELETE_B":
        return "Board deleted successfully."
    elif opcode == "ERRORENC":
        err = ord(args[0])
        if err in FAULT_CODES:
            return "Error! Server responded with 0x{:x}".format(err)
        else:
            if err == BOARDDNE:
                return "Specified board does not exist."
            elif err == MSGS_DNE:
                return "One or more of the specified message(s) do not exist."
            elif err == UNOPERMS:
                return "You do not have permission to do that!"
            elif err == RESEMPTY:
                return "Result is empty."
            else:
                return "Server responded with unexpected (impossible?) status of 0x{:x}".format(err)
        return "Error: {:d}".format(ord(args[0]))
    else:
        return "Unknown Opcode: {}".format(opcode)

