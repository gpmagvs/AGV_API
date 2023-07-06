import json
import requests
import threading
from agvs_classes import clsAGVSatus, clsTaskDownload , clsTaskFeedback,TASK_STATUS,TaskFeedbackEncoder ,clsVMSReturn,clsOnlineModeQueryAck
from flask import Flask , request



class AGVS_EVENT_HANDLERS:
    ONLINE_HANDLER =None
    OFFLINE_HANDLER =None
    TASK_EXECUTE_HANDLER =None

class AgvsMiddleware:
    
    app = Flask(__name__)
    
    headers = {'Content-Type': 'application/json'}
    vms_host_url = 'http://127.0.0.1:5036'
    api_route_AGVStatus ='/api/AGV/AGVStatus'
    api_route_TaskFeedback ='/api/AGV/TaskFeedback'
    api_route_OnlineModeQuery ='/api/AGV/OnlineMode'
    api_route_OnlineRequest ='/api/AGV/OnlineReq'
    api_route_OfflineRequest ='/api/AGV/OfflineReq'
    
    def __init__(self,AGV_Name,Model,Event_Handlers:AGVS_EVENT_HANDLERS,
                 Host:str='0.0.0.0',
                 Port:int=12345,
                 AGVS_Host:str='http://127.0.0.1:5036'):        
        self.AGV_Name = AGV_Name
        self.Model = Model
        self.Host =Host
        self.Port =Port
        self.Event_Handlers=Event_Handlers
        self.previous_task:clsTaskDownload=None
        self.vms_host_url = AGVS_Host
        self._RunFlaskApp()
    
    def _RunFlaskApp(self):
        thread=threading.Thread(target=self._Run)
        thread.start();
        # self._Run()
        
    def _Run(self):
        self.app.add_url_rule('/api/AGV/agv_online','/api/AGV/agv_online',self.API_ONLINE_REQ,methods=['GET'])
        self.app.add_url_rule('/api/AGV/agv_offline','/api/AGV/agv_offline',self.API_OFFLINE_REQ,methods=['GET'])
        self.app.add_url_rule('/api/TaskDispatch/Execute','/api/TaskDispatch/Execute',self.API_TASK_EXECTUE,methods=['POST'])
        self.app.run(host=self.Host,port=self.Port,debug=False)
        
        
    def AGVStatusReport(self,agv_states:'clsAGVSatus'):
        'AGV狀態上報'
        try:
            payload= agv_states.to_json()
            response = requests.post(self.vms_host_url+self.api_route_AGVStatus+f'?AGVName={self.AGV_Name}&Model={self.Model}',headers=self.headers,data=payload,verify=False)
            vms_return = clsVMSReturn(**json.loads(response.content))
            return vms_return
        except requests.exceptions.ConnectionError as ex:
            print('AGVS連線異常')
            raise ex
        except Exception as ex:
            print(ex)
            raise ex


    def TaskFeedback(self, task_feedback:clsTaskFeedback):
        'AGV任務回報'
        try:
            payload= json.dumps(task_feedback,cls=TaskFeedbackEncoder)
            response = requests.post(self.vms_host_url+self.api_route_TaskFeedback+f'?AGVName={self.AGV_Name}&Model={self.Model}',headers=self.headers,data=payload,verify=False)
            vms_return = clsVMSReturn(**json.loads(response.content))
            return vms_return    
        except requests.exceptions.ConnectionError as ex:
            print('AGVS連線異常')
            raise ex
        except Exception as ex:
            print(ex)
            raise ex
        
    
    def AGVOnlineModeQuery(self):
        '上線狀態詢問(Alive Check.)'
        try:
            response = requests.get(self.vms_host_url+self.api_route_OnlineModeQuery+f'?AGVName={self.AGV_Name}&Model={self.Model}',headers=self.headers,verify=False)
            vms_return = clsOnlineModeQueryAck(**json.loads(response.content))
            return vms_return
        except requests.exceptions.ConnectionError as ex:
            print('AGVS連線異常')
            raise ex
        except Exception as ex:
            print(ex)
            raise ex

    def AGVOnlineRequest(self):
        '上線請求'
        try:
            response = requests.post(self.vms_host_url+self.api_route_OnlineRequest+f'?AGVName={self.AGV_Name}&Model={self.Model}',headers=self.headers,verify=False)
            vms_return = clsVMSReturn(**json.loads(response.content))
            return vms_return
        except requests.exceptions.ConnectionError as ex:
            print('AGVS連線異常')
            raise ex
        except Exception as ex:
            print(ex)
            raise ex
    
    def AGVOfflineRequest(self):
        '下線請求'
        try:
            response = requests.post(self.vms_host_url+self.api_route_OfflineRequest+f'?AGVName={self.AGV_Name}&Model={self.Model}',headers=self.headers,verify=False)
            vms_return = clsVMSReturn(**json.loads(response.content))
            return vms_return
        except requests.exceptions.ConnectionError as ex:
            print('AGVS連線異常')
            raise ex
        except Exception as ex:
            print(ex)
            raise ex

    
    def RegistOnlineReq(self, handler):
        '註冊派車系統要求上線事件'
        self.Event_Handlers.ONLINE_HANDLER=handler
        
        
    def RegistOfflineReq(self, handler):
        '註冊派車系統要求下線事件'
        self.Event_Handlers.OFFLINE_HANDLER=handler
        
        
    def RegistTaskExecuteReq(self, handler):
        '註冊派車系統任務下載事件'
        self.Event_Handlers.TASK_EXECUTE_HANDLER=handler
        
    def API_ONLINE_REQ(self):
        return self.Event_Handlers.ONLINE_HANDLER('')
    
    def API_OFFLINE_REQ(self):
        return self.Event_Handlers.OFFLINE_HANDLER('')
    
    def API_TASK_EXECTUE(self):
         taskDownload=self.GetTaskDownloadData(request.json)
         
         if self.previous_task is not None:
             if taskDownload.Task_Name != self.previous_task.Task_Name:
                 pass
             else:
                 if taskDownload.Action_Type is not self.previous_task.Action_Type:
                     pass
                 else:
                    print('task expand')
                    lastPt= self.previous_task.Trajectory.pop()
                    index=taskDownload.Trajectory.index(lastPt)
                    newTraject= taskDownload.Trajectory[index:]
                    taskDownload.Trajectory=newTraject;
         
         self.previous_task=taskDownload;
         return self.Event_Handlers.TASK_EXECUTE_HANDLER(taskDownload)
     
    def GetTaskDownloadData(self,task_json):
         taskDownload= clsTaskDownload()
         taskDownload.Task_Name = task_json['Task Name']
         taskDownload.Task_Simplex = task_json['Task Simplex']
         taskDownload.Task_Sequence = task_json['Task Sequence']
         taskDownload.Trajectory = task_json['Trajectory']
         # taskDownload.Homing_Trajectory = task_download['Homing_Trajectory']
         taskDownload.Action_Type = task_json['Action Type']
         taskDownload.CST = task_json['CST']
         taskDownload.Destination = task_json['Destination']
         taskDownload.Height = task_json['Height']
         taskDownload.Escape_Flag = task_json['Escape Flag']
         taskDownload.Station_Type = task_json['Station Type']
         
         return taskDownload;      