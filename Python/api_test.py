from  AGVSMiddleware import AgvsMiddleware,AGVS_EVENT_HANDLERS
from agvs_classes import AGV_STATUS, TASK_STATUS, clsTaskDownload, clsTaskFeedback,clsAGVSatus
import json
import threading
import time
from datetime import datetime
import multiprocessing
import sys

global AGVS_Middleware

agv_states= clsAGVSatus()

def simulation_move(taskDownload:clsTaskDownload):
            global AGVS_Middleware
            time.sleep(1)
            taskName= taskDownload.Task_Name
            taskSimp =taskDownload.Task_Simplex
            tskSeq = taskDownload.Task_Sequence
            index=0
            agv_states.AGV_Status = AGV_STATUS.RUN
            
            for pt in taskDownload.Trajectory:
                agv_states.Electric_Volume[0]=agv_states.Electric_Volume[0]-0.1;
                agv_states.Last_Visited_Node=pt['Point ID']
                agv_states.Coordination.X = pt["X"]
                agv_states.Coordination.Y = pt["Y"]
                agv_states.Coordination.Theta = pt["Theta"]
                AGVS_Middleware.TaskFeedback(clsTaskFeedback(taskName,taskSimp,tskSeq,index, TASK_STATUS.NAVIGATING))
                index+=1
                time.sleep(1)
                
            print(f'模擬移動完成_抵達 Tag {agv_states.Last_Visited_Node}')
            agv_states.AGV_Status = AGV_STATUS.IDLE
            AGVS_Middleware.TaskFeedback(clsTaskFeedback(taskName,taskSimp,tskSeq,index, TASK_STATUS.ACTION_FINISH))
            
if __name__=='__main__':
    
    print('start-Yuntech AGV Simulator')

    agv_flask_host = '127.0.0.1'
    agv_flask_port = 12345
    agv_name = 'forklift'
    init_tag =3
    
    if len(sys.argv) >=5:
        agv_flask_host = sys.argv[1]
        agv_flask_port = sys.argv[2]
        agv_name = sys.argv[3]
        init_tag = sys.argv[4]
        print(agv_flask_host,agv_flask_port,agv_name,init_tag)
    
    def OnlineReqHandler(arg):
        agv_states.AGV_Status= AGV_STATUS.IDLE
        #Please Check AGV Can ONLINE Rightnow, if not, ReturnCode is equal some alarm code. 
        return  {'ReturnCode':0,'Message':''}

    def OfflineReqHandler(arg):
        global agv_states
        agv_states.AGV_Status= AGV_STATUS.DOWN
        #Please Check AGV Can OFFLINE Rightnow, if not, ReturnCode is equal some alarm code. 
        return  {'ReturnCode':0,'Message':''}

    def TaskExecuteReqHandler(request:clsTaskDownload):
        print(request.Task_Name)
        #Please Check AGV Can Run This Task Request, if not, ReturnCode is equal some alarm code. 
        move_thread=multiprocessing.Process(target=simulation_move,args=[request])
        move_thread.start();
        
        return  {'ReturnCode':0,'Message': request.Task_Name+' recieved'}
    

    def ReportStatusWorker():
        while True:
            try:
               return_=AGVS_Middleware.AGVStatusReport(agv_states)
               #print(f'{datetime.now()}-Status Report, ReturnCode =',return_.ReturnCode)
            except Exception as ex:
                pass
            time.sleep(0.2)

    def AliveCHeckWorker():
        while True:
            try:
                return_ = AGVS_Middleware.AGVOnlineModeQuery()
                #print(f'{datetime.now()}-AGV 上線狀態詢問 , RemoteMode =',return_.RemoteMode)
            except Exception as ex:
                print(ex)
                pass
            
            time.sleep(0.5)

    agv_states.Last_Visited_Node=1
    agv_states.AGV_Status= AGV_STATUS.IDLE
    agv_states.Electric_Volume=[99,99]
    agv_states.Last_Visited_Node=init_tag
    
    events = AGVS_EVENT_HANDLERS()
    events.ONLINE_HANDLER = OnlineReqHandler;
    events.OFFLINE_HANDLER = OfflineReqHandler;
    events.TASK_EXECUTE_HANDLER= TaskExecuteReqHandler;
    
    AGVS_Middleware = AgvsMiddleware(agv_name,1,events,AGVS_Host='http://127.0.0.1:5036',Host=agv_flask_host,Port=agv_flask_port)
    
    
    ReportStatusthread=threading.Thread(target=ReportStatusWorker)
    AliveCheckThread=threading.Thread(target=AliveCHeckWorker)

    try:
        ReportStatusthread.start()
        AliveCheckThread.start()
        while True:
            time.sleep(1)
        pass
            
    except KeyboardInterrupt :
        pass
