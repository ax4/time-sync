from socketIO_client import SocketIO, LoggingNamespace
import win32api, win32con
from datetime import datetime
from threading import Thread
import time

t1 = 0
trigger_action = '422' ##change this to your action number
scheduled_time = None
offset = None

def UTC_timestamp():
    epoch = datetime(1970,1,1)
    d = datetime.utcnow()
    t = (d-epoch).total_seconds()
    return round(t*1000) ##fixed to match the return timestamp from server

def MouseClick(x,y):
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)

def MousePosition():
    return win32api.GetCursorPos() 

def on_sync_response(args):
    ##print('on_sync_response', args)
    t2 = UTC_timestamp()
    ##print('on_recv_response', t2)
    res = args
    ##timeout
    if (t2-t1>2000):
        print("emit timeout")
        return 
    newoffset = (t1+t2)/2 -res; 
    ##print("update with newoffset: ", newoffset)
    global offset
    if (offset==None):
        offset = round(newoffset)
    else: 
        offset = round(0.8*offset+0.2*newoffset)
    print("updated offset: ", offset)

def on_broadcast_response(args):
    wrap = args
    print ("on_broadcast_response", args)
    print("action: ", args['action'])
    print("timestamp: ", args['timestamp'])
    if (args['action']==trigger_action): 
        global scheduled_time
        if (scheduled_time==None):
            scheduled_time = args['timestamp']

def thread1(threadname):
    with SocketIO('your-host.net', 23333, LoggingNamespace) as socketIO:
        i = 0 
        while True:
            global t1
            t1 = UTC_timestamp()
            ##print('on_emit_response',t1)
            socketIO.emit('sync', None, on_sync_response)
            socketIO.wait_for_callbacks(seconds=0.01)
            socketIO.on('broadcast',on_broadcast_response)
            socketIO.wait(seconds=0.01)

def thread2(threadname):
    ##fixme: use multi-thread
    while True: 
        time.sleep(0.005)
        global scheduled_time
        if (offset==None):
            continue
        if (scheduled_time==None):
            continue
        if (UTC_timestamp()+offset>=scheduled_time):
            print('Mouse Triggered on Action ',trigger_action)
            x,y = MousePosition()
            MouseClick(x,y)
            scheduled_time=None

thread1 = Thread( target=thread1, args=("Thread-1", ) )
thread2 = Thread( target=thread2, args=("Thread-2", ) )

thread1.start()
thread2.start()