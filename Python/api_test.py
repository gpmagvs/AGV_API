from  AGVSMiddleware import AgvsMiddleware,AGVS_EVENT_HANDLERS
from agvs_classes import AGV_STATUS, TASK_STATUS, clsCoordination, clsTaskDownload, clsTaskFeedback,clsDriverStates,clsAGVSatus,clsCancelTask,ACTION_TYPE
import json
import threading
import time
from datetime import datetime
import multiprocessing
import sys

global AGVS_Middleware

agv_states= clsAGVSatus()
taskStatus = clsTaskFeedback('init','init',0,0, TASK_STATUS.NO_MISSION)

                
            
if __name__=='__main__':
    
    print('start-Yuntech AGV Simulator')
    agv_flask_host = '127.0.0.1'
    agv_flask_port = 12345
    agv_name = 'AGV_001'
    init_tag =7
    init_coordination= clsCoordination(2.623 ,3.17,0)
    if len(sys.argv) >=5:
        agv_flask_host = sys.argv[1]
        agv_flask_port = sys.argv[2]
        agv_name = sys.argv[3]
        init_tag = sys.argv[4]
        init_coordination.X= float( sys.argv[5])
        init_coordination.Y= float(sys.argv[6])
        print(agv_flask_host,agv_flask_port,agv_name,init_tag)
        print(init_coordination)
    
    def OnlineReqHandler(arg):
        agv_states.AGV_Status= AGV_STATUS.IDLE
        #Please Check AGV Can ONLINE Rightnow, if not, ReturnCode is equal some alarm code. 
        return  {'ReturnCode':0,'Message':''}

    def OfflineReqHandler(arg):
        global agv_states
        agv_states.AGV_Status= AGV_STATUS.IDLE
        #Please Check AGV Can OFFLINE Rightnow, if not, ReturnCode is equal some alarm code. 
        return  {'ReturnCode':0,'Message':''}

    def CancelTaskReqHandler(request:clsCancelTask):
        
        global agv_states
        print(request)
        agv_states.AGV_Status= AGV_STATUS.IDLE
        return  {'ReturnCode':0,'Message': ''}
    
    def TaskExecuteReqHandler(request:clsTaskDownload):
        print(request.Task_Name)
        #Please Check AGV Can Run This Task Request, if not, ReturnCode is equal some alarm code. 
        move_thread=threading.Thread(target=simulation_move,args=[request])
        move_thread.start();
        
        return  {'ReturnCode':0,'Message': request.Task_Name+' recieved'}
    def getActionType(action_int):
        if action_int ==0:
            return ACTION_TYPE.Move;
        if action_int ==1:
            return ACTION_TYPE.Unload;
        if action_int ==2:
            return ACTION_TYPE.LoadAndPark;
        if action_int ==7:
            return ACTION_TYPE.Load;
        if action_int ==8:
            return ACTION_TYPE.Charge;
        if action_int ==10:
            return ACTION_TYPE.Discharge;
        if action_int ==12:
            return ACTION_TYPE.Park;
        if action_int ==13:
            return ACTION_TYPE.Unpark;
        
        return ACTION_TYPE.Move
    def simulation_move(taskDownload:clsTaskDownload):
            global agv_states,taskStatus
            time.sleep(1)
            taskName= taskDownload.Task_Name
            taskSimp =taskDownload.Task_Simplex
            tskSeq = taskDownload.Task_Sequence
            index=0
            agv_states.AGV_Status = AGV_STATUS.RUN
            _traj= None
            action = getActionType(taskDownload.Action_Type) 
            
            if action == ACTION_TYPE.Load or action == ACTION_TYPE.Unload:
                _traj=taskDownload.Homing_Trajectory
                _traj=_traj+[_traj[0]]
            else:
                if action == ACTION_TYPE.Move:
                    _traj=taskDownload.Trajectory
                else :
                    _traj=taskDownload.Homing_Trajectory
                
            for pt in _traj:
                agv_states.Electric_Volume[0]=agv_states.Electric_Volume[0]-0.1;
                agv_states.Last_Visited_Node=pt['Point ID']
                agv_states.Coordination.X = pt["X"]
                agv_states.Coordination.Y = pt["Y"]
                agv_states.Coordination.Theta = pt["Theta"]
                
                taskStatus.task_name=taskName
                taskStatus.task_seq=tskSeq
                taskStatus.task_simplex=taskSimp
                taskStatus.point_index = index
                taskStatus.status = TASK_STATUS.NAVIGATING
                index+=1
                
                if index== len(_traj)-1:
                    if action== ACTION_TYPE.Load:
                        agv_states.Cargo_Status= 0
                    else:
                        agv_states.Cargo_Status= 1
                time.sleep(.5)
                
           
            print(f'模擬移動完成_抵達 Tag {agv_states.Last_Visited_Node}')
            time.sleep(.1)
            taskStatus.task_name=taskName
            taskStatus.task_seq=tskSeq
            taskStatus.task_simplex=taskSimp
            taskStatus.status = TASK_STATUS.ACTION_FINISH
            
            AGVS_Middleware.TaskFeedback(taskStatus)
            

            if action== ACTION_TYPE.Charge :
                agv_states.AGV_Status = AGV_STATUS.Charging;
                agv_states.Electric_Volume[0] = 99
            else:
                agv_states.AGV_Status = AGV_STATUS.IDLE

    def ReportStatusWorker():
        while True:
            try:
               return_=AGVS_Middleware.AGVStatusReport(agv_states)
               #print(f'{datetime.now()}-Status Report, ReturnCode =',return_.ReturnCode)
            except Exception as ex:
                pass
            time.sleep(0.1)

    def AliveCHeckWorker():
        while True:
            try:
                return_ = AGVS_Middleware.AGVOnlineModeQuery()
                #print(f'{datetime.now()}-AGV 上線狀態詢問 , RemoteMode =',return_.RemoteMode)
            except Exception as ex:
                print(ex)
                pass
            
            time.sleep(0.5)
            
    def TaskFeedbackThreadWorker():
        lastTaskStat=clsTaskFeedback('init','init',0,0, TASK_STATUS.NO_MISSION)
        
        global agv_states,taskStatus
        while True:
            time.sleep(0.5)
            try:
                if((lastTaskStat.task_simplex!=taskStatus.task_simplex) &( lastTaskStat.point_index!=taskStatus.point_index)):
                    AGVS_Middleware.TaskFeedback(taskStatus)
                lastTaskStat = taskStatus
            except Exception as ex:
                print(ex)
            
            
            
            
    agv_states.Last_Visited_Node=1
    agv_states.AGV_Status= AGV_STATUS.IDLE
    agv_states.Electric_Volume=[65,77]
    agv_states.Last_Visited_Node=init_tag
    driver=clsDriverStates()
    driver.Speed=1.1
    driver.Status=3
    agv_states.DriversStatus=[]
    agv_states.DriversStatus.append(driver)
    agv_states.Coordination=init_coordination
    agv_states.Cargo_Status=1
    events = AGVS_EVENT_HANDLERS()
    events.ONLINE_HANDLER = OnlineReqHandler;
    events.OFFLINE_HANDLER = OfflineReqHandler;
    events.TASK_EXECUTE_HANDLER= TaskExecuteReqHandler;
    events.CANCEL_TASK_HANDLER = CancelTaskReqHandler;
    
    AGVS_Middleware = AgvsMiddleware(agv_name,0,events,AGVS_Host='http://127.0.0.1:5036',Host=agv_flask_host,Port=agv_flask_port)
    
    
    ReportStatusthread=threading.Thread(target=ReportStatusWorker)
    AliveCheckThread=threading.Thread(target=AliveCHeckWorker)
    TaskFeedbackThread=threading.Thread(target=TaskFeedbackThreadWorker)

    try:
        ReportStatusthread.start()
        AliveCheckThread.start()
        TaskFeedbackThread.start()
        while True:
            time.sleep(1)
        pass
            
    except KeyboardInterrupt :
        pass
