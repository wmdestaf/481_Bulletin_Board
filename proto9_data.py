from proto9_constants import *
import time
import copy
from threading import Semaphore
from rwlock import RWLock

boards = None
GLOBAL_BOARD_LOCK = None

####################################STRUCTS#####################################
class Message:
    '''
        Constructs a new message
        @param m_id The message id
        @param creator_id The u_id of the creator
        @param subject The message subject
        @param text The message text
    '''
    def __init__(self, m_id, creator_id, subject, text):
        self.m_id    = m_id
        self.creator = creator_id
        self.created = time.time()
        self.subject = subject
        self.text    = text
    
    '''
        A message is equal to another message if its primitive fields are the same
        @param other The message to compare
        @return True if self == other, else False
    '''   
    def __eq__(self, other):
        if not isinstance(other, Message):
            return False
    
        for attribute in dir(self): #State made up of primitives, so this much is fine.
            if getattr(self,attribute) != getattr(other, attribute):
                return False
        return True
    
    '''
        Debug, prints message in most concise format
    '''
    def __repr__(self):
        return "\nid: {}, by: {}, when: {}\nsubj: {:10s},msg: {:20s}\n".format(
            self.m_id, self.creator, self.created, self.subject, self.text)
    
class Board:
    '''
        Creates a new 'board'
        @param b_id The board's ID
        @param creator_id The board's creator's u_id
    '''
    def __init__(self, b_id, creator_id):
        self.b_id     = b_id
        self.creator  = creator_id
        self.messages = []
        self.m_id_ctr = 1
        self.msgs_map = {}
        self.lock     = RWLock()
    
    '''
        Returns the id of the next message in the board, auto-incremented
        @return The id of the next message
    '''
    def next_id(self):
        self.m_id_ctr += 1
        return self.m_id_ctr - 1
        
    '''
        Debug for efficient representation
    '''
    def __repr__(self):
        return "\nid: {}, by: {}, next: {}\nmessages: {}\nmap: {}\n".format(
            self.b_id, self.creator, self.m_id_ctr, 
            self.messages, self.msgs_map)
####################################HELPER#####################################
'''
    Returns a board with the given b_id, or None, should one not exist
    @param b_id The id of the board to search for
    @return The board with ID b_id, or None, if no such board exists
'''
def get_board_by_id(b_id):
    #https://stackoverflow.com/a/3785811
    return next((b for b in boards if b.b_id == b_id), None)
  
'''
    Returns a message with the given m_id, or None, should one not exist
    @param m_id The id of the message to search for
    @return The message with ID m_id, or None, if no such message exists
'''  
def get_message_by_id(board, m_id):
    return next((m for m in board.messages if m.m_id == m_id), None)
####################################BOARDS######################################  
'''
    Attempts to create a board with the given ID
    @param b_id The board ID to create
    @param u_id The user ID of the creator
    @return (False,[BOARDDNE]) if such a board exists, or (True,[]) if
    the board was successfully created
'''
def create_b(b_id, u_id):
    with GLOBAL_BOARD_LOCK.w_locked():
        if get_board_by_id(b_id):
            return (False,[BOARDDNE])
            
        boards.append(Board(b_id, u_id))
        return (True,[])
   
'''
    Attempts to delete a board with the given ID
    @param b_id The board ID to delete
    @param u_id The user ID of the user trying to delete the board
    @return (False,[BOARDDNE]) if such a board doesn't exist
    @return (False,[UNOPERMS]) if the user is not the board's creator
    @return (True,[]) if the board was successfully deleted
'''   
def delete_b(b_id, u_id):
    with GLOBAL_BOARD_LOCK.w_locked():
        board = get_board_by_id(b_id)
        if not board: #Board does not exist
            return (False,[BOARDDNE])
        elif board.creator != u_id: #User does not have permission
            return (False,[UNOPERMS])
           
        boards.remove(board)
        return (True,[])
#############################BOARD INFORMATION##################################
'''
    Attempts to return the total number of messages on the board with the given ID
    @param b_id The board to check
    @return (False,[BOARDDNE]) if no such board exists, otherwise (True, message_count)
'''
def get_m_ct(b_id):
    with GLOBAL_BOARD_LOCK.r_locked():
        board = get_board_by_id(b_id)
        if not board: #Board does not exist
            return (False,[BOARDDNE])
            
        with board.lock.r_locked():
            return (True,len(board.messages))
  
'''
    Attempts to return the total number of new messages on a board with the given b_id
    for the user with the given u_id. Should the board have no record of the user,
    it considers all messages on the board to be 'new'.
    @param b_id The board id to check
    @param u_id The id of the user to consider
    @return (False,[BOARDDNE]) if no such board exists, otherwise (True, unread_message_count)
'''
def getnewct(b_id, u_id):
    with GLOBAL_BOARD_LOCK.r_locked():
        board = get_board_by_id(b_id)
        if not board: #Board does not exist
            return (False,[BOARDDNE])
        
        with board.lock.r_locked():
            try: #Are we keeping track of unread messages for this user?
                return (True,len(board.msgs_map[u_id]))
            except KeyError: #If not, they've read *none* of them!  
                return (True,len([msg for msg in board.messages if msg.creator != u_id]))
        
##############################MESSAGE INPUT#####################################   
'''
    Attempts to post a message to the given board
    @param b_id The board to post on
    @param u_id The user ID of the message
    @param subject The subject of the message
    @param msg_text The text of the message
    @return (False, [BOARDDNE]) If the board specified by b_id does not exist
    @return (True, []) on success
'''
def post_msg(b_id, u_id, subject, msg_text):
    with GLOBAL_BOARD_LOCK.r_locked():
        board = get_board_by_id(b_id)
        if not board: #Board does not exist
            return (False,[BOARDDNE])
        
        with board.lock.w_locked():
            #get and autoincrement post counter
            m_id = board.next_id()
            
            message = Message(m_id, u_id, subject, msg_text)
            board.messages.append(message)
            return (True,[])
    
'''
    Attempts to delete a message with the given id on the board of the given id
    @param b_id The board to delete the message from
    @param u_id The user whom is deleting the message
    @param m_id The id of the message to delete
    @return (False, [BOARDDNE]) If the board does not exist
    @return (False, [MSGS_DNE]) If the message specified by m_id does not exist
    @return (False, [UNOPERMS]) If the user does not have permissions to delete the
    message - that is, the user did not post the message
    @return (True, []) If the message was deleted successfully
'''
def delt_msg(b_id, u_id, m_id):
    with GLOBAL_BOARD_LOCK.r_locked():
        board = get_board_by_id(b_id)
        if not board: #Board does not exist
            return (False,[BOARDDNE])
            
        with board.lock.w_locked():
            message = get_message_by_id(board, m_id)
            if not message:
                return (False, [MSGS_DNE])
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
    Get messages according to the given parameters
    @param b_id The board to get messages from
    @param u_id The user getting the messages
    @param m_ids Specific message ids to return. If empty, ignored.
    @param subjects_only Flag to return only message subjects
    @param new_only Flag to return only new messages
    @return (False, [BOARDDNE]) If the board does not exist
    @return (False, [MSGS_DNE]) If one or more messages specified by m_ids does not exist
    @return (False, [RESEMPTY]) If the resultant query after flags is empty
    @return (True, messages) If the query returns one or more messages. 'messages'
    in the 2-tuple is nothing but a list of "messages", where a "message is of the format:
    [messageID, messageCreator, messageTimestamp, messageSubject, messageBody]
    and naturally, creator is the u_id of the creator.
'''
def get_msgs(b_id, u_id, m_ids, subjects_only=False, new_only=False):
    with GLOBAL_BOARD_LOCK.r_locked():
        board = get_board_by_id(b_id)
        if not board: #Board does not exist
            return (False,[BOARDDNE])
        
        with board.lock.w_locked(): #Write necessary, as reading a message may constitute 
                                      #adjusting someone's 'new messages' list
            if not board.messages:
                return (False,[RESEMPTY])

            msgs = copy.deepcopy(board.messages) #this can be avoided.

            if len(m_ids): #If searching for specific ID's, filter by them
                msgs = [msg for msg in msgs if msg.m_id in m_ids]
                if len(msgs) != len(m_ids):
                    return (False, [MSGS_DNE])
            if new_only: #If searching for new messages only, filter by them
                try:
                    msgs = [msg for msg in msgs if msg.m_id in board.msgs_map[u_id]]
                except KeyError:
                    board.msgs_map[u_id] = [msg.m_id for msg in board.messages if msg.creator != u_id]
                    msgs = [msg for msg in msgs if msg.m_id in board.msgs_map[u_id]]

            #filter and update unread messages for a user
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
        
boards = [Board(0, -1)] #List of boards. Public board is board '0', with illegal user id '-1' as owner (nobody can delet)
GLOBAL_BOARD_LOCK = RWLock()

'''
    Execute the operation from the server's context
    @param opcode The opcode to execute
    @param args The arguments to execute
    @return The result of the execution
'''
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
      
'''
    Execute the operation from the client's context
    @param opcode The opcode to execute
    @param args The arguments to execute
    @return The result of the execution
'''      
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