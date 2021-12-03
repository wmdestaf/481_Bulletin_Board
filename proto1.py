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
        return False
        
    boards.append(Board(b_id, u_id))
    return True
    
def delete_b(b_id, u_id):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return False
    elif board.creator != u_id: #User does not have permission
        return False
       
    boards.remove(board)
    return True
#############################BOARD INFORMATION##################################    
def get_m_ct(b_id):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return False
    return len(board.messages)
    
def getnewct(b_id, u_id):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return False

    '''
    A new message, in the context of a user's ID, must satisfy ALL of the following properties:
        Was created on a board after the user's most recent 'All' query for the board
        Does not exist in the board's uID -> new Message mapping
    '''
    try: #Are we keeping track of unread messages for this user?
        return len(board.msgs_map[u_id])
    except KeyError: #If not, they've read *none* of them!  
        return len([msg for msg in board.messages if msg.creator != u_id])
    
##############################MESSAGE INPUT#####################################   
def post_msg(b_id, u_id, subject, msg_text):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return False
    
    #get and autoincrement post counter
    m_id = board.next_id()
    
    message = Message(m_id, u_id, subject, msg_text)
    board.messages.append(message)
    return True
    
def delt_msg(b_id, u_id, m_id):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return False
        
    message = get_message_by_id(board, m_id)
    if message.creator != u_id:
        return False
    
    board.messages.remove(message)
    
    #REMOVE ID FROM ALL UNREAD LISTS
    for m_id_list in board.msgs_map.values():
        try:
            m_id_list.remove(m_id)
        except KeyError:
            pass
    return True
##############################MESSAGE OUTPUT####################################
'''
@param b_id The ID of the board to target
@param m_ids An optional list of message ids' to specifically include
@param subjects_only Flag to determine if only subjects (not message contents) should be returned
@param new_only False to ignore, or a specific user ID to return the 'new' messages on the board
@return False if the board doesn't exist, or the board has no messages
'''
def get_msgs(b_id, u_id, *m_ids, subjects_only=False, new_only=False):
    board = get_board_by_id(b_id)
    if not board: #Board does not exist
        return False
    elif not board.messages:
        return False

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
      
    strs = [time.asctime(time.localtime(msg.created)) + "\nNo.   " +
            str(msg.m_id) + "\nsubj: " + msg.subject + ( ("\nmsg:  "+msg.text) if not subjects_only else "") for msg in board.messages]
    return "\n\n".join(strs)
##################################################################################
        

boards = [Board(0, -1)]
play = [[1,0,1,1,1],[1,0,1,2,2],[1,0,2,3,3],[1,0,3,4,4]]
#flatten
play = [inp for loop in play for inp in loop]
while True: #Interactive mode
             
    if play:
        i = play.pop(0)
    else:
        print("Do what?\n1. Post Message\n2. Delete Message\n3. Get Messages\n" +
          "4. Get Message Count\n5. Get New Message Count\n6. Create Board\n7. Delete Board\n8. Exit")
        i = int(input())
        
    if i == 1:
        board = play.pop(0)      if play else int(input("Board? "))
        user  = play.pop(0)      if play else int(input("User? "))
        subj  = str(play.pop(0)) if play else input("Subject? ")
        text  = str(play.pop(0)) if play else input("Text? ")
        print(post_msg(board,user,subj,text))
    elif i == 2:
        board = play.pop(0) if play else int(input("Board? "))
        user  = play.pop(0) if play else int(input("User? "))
        ms_id = play.pop(0) if play else int(input("Message Id? "))
        print(delt_msg(board,user,ms_id))
    elif i == 3:
        board  = play.pop(0) if play else int(input("Board? "))
        user   = play.pop(0) if play else int(input("User? "))
        ms_raw = ",".join([str(x) for x in play.pop(0)]) if play else input("Message Ids? (comma seperated, blank to ignore) ")
        if ms_raw:
            ms_ids = [int(x) for x in ms_raw.split(",")]
        subjs = True if (play.pop(0) if play else input("Subjects only? (blank to decline) ")) else False
        new   = True if (play.pop(0) if play else input("New msgs only? (blank to decline) ")) else False
        if ms_raw:
            print(get_msgs(board, user, *ms_ids, subjects_only=subjs, new_only=new))
        else:
            print(get_msgs(board, user, subjects_only=subjs, new_only=new))
    elif i == 4:
        board = play.pop(0) if play else int(input("Board? "))
        print(get_m_ct(board))
    elif i == 5:
        board = play.pop(0) if play else int(input("Board? "))
        user  = play.pop(0) if play else int(input("User? "))
        print(getnewct(board, user))
    elif i == 6:
        board = play.pop(0) if play else int(input("Board? "))
        user  = play.pop(0) if play else int(input("User? "))
        print(create_b(board, user))
    elif i == 7:
        board = play.pop(0) if play else int(input("Board? "))
        user  = play.pop(0) if play else int(input("User? "))
        print(delete_b(board, user))
    elif i == 8:
        break

'''
WHERE AM I NOW?

get messages *gives* messages but does not *clear* them from the 'unread' list.
'''







