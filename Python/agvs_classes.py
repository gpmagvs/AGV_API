from enum import Enum
import json
from datetime import datetime
from dataclasses import dataclass,asdict
from typing import List

def serialize_enum(obj):
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")



@dataclass
class SerilizebleCalss:
    def __init__(self,_self):
        self =_self
        
    def to_json(self)->str:
        return json.dumps(asdict(self))


class TASK_STATUS(Enum):
    """
    任務狀態列舉    
    """
    NO_MISSION = 0
    NAVIGATING = 1
    REACH_POINT_OF_TRAJECTORY = 2
    ACTION_START = 3
    ACTION_FINISH = 4
    WAIT=5
    FAILUR=6
    
class AGV_STATUS(Enum):
    IDLE = 1
    RUN=2
    DOWN=3
    Charging=4
    Unknow=5

class ONLINE_MODE(Enum):
    Offline = 0 
    Online  = 1

class ACTION_TYPE(Enum): 
        Move=0
        Unload=1
        LoadAndPark=2
        Forward=3
        Backward=4
        FaB=5
        Measure=6
        Load=7
        Charge=8
        Carry=9
        Discharge=10
        Escape=11
        Park=12
        Unpark=13
        ExchangeBattery=14
        Hold=15
        Break=16
class STATION_TYPE(Enum):
       Normal = 0
       EQ = 1
       STK = 2
       Charge = 3
       Buffer = 4
       Charge_Buffer = 5
       Charge_STK = 6
       Escape = 8
       EQ_LD = 11
       STK_LD = 12
       EQ_ULD = 21
       STK_ULD = 22
       Fire_Door = 31
       Fire_EQ = 32
       Auto_Door = 33
       Elevator = 100
       Elevator_LD = 201
       Elevator_ULD = 221
       Unknown = 9999


@dataclass
class clsCoordination:
    X:float=0
    Y:float=0
    Theta:float=0

@dataclass
class clsAlarmCode:
    Alarm_ID:int =0
    Alarm_Level:int =0
    Alarm_Category:int=0 
    Alarm_Description:str=''
    
    
@dataclass
class clsAGVSatus(): 
    """
    AGV 狀態物件    
    """
    Time_Stamp:str='0000.0000' 
    Coordination: clsCoordination = None
    Last_Visited_Node:int =0
    AGV_Status:AGV_STATUS = AGV_STATUS.DOWN
    Escape_Flag:bool=False
    AGV_Reset_Flag:bool=False
    Sensor_Status:dict =None
    CPU_Usage_Percent:float=0.00
    RAM_Usage_Percent:float=0.00
    Signal_Strength:float=0.00
    Odometry:float=0.00
    Fork_Height:float=0.00
    Cargo_Status:int=0
    CSTID :List[str]= None
    Electric_Volume :List[float]= None
    Alarm_Code:List[clsAlarmCode]=None
    
    def __post_init__(self):
        if self.Coordination is None:
            self.Coordination=clsCoordination()
        if self.Sensor_Status is None:
            self.Sensor_Status={}
        if self.CSTID is None:
            self.CSTID=[]
        if self.Electric_Volume is None:
            self.Electric_Volume=[0.0]
        if self.Alarm_Code is None:
            self.Alarm_Code=[]
    
    def to_json(self) -> str:
        return json.dumps(asdict(self),default=serialize_enum)
 
        
        
@dataclass
class clsTaskFeedback:
    """
    任務狀態物件    
    """
    def __init__(self,task_name:str,task_simplex:str,task_seq:int,point_index:int,taskStatus:'TASK_STATUS'):
        self.timestamp=datetime.now().strftime("%Y%m%d %H:%M:%S")
        self.task_name=task_name
        self.task_simplex=task_simplex
        self.task_seq = task_seq
        self.point_index = point_index
        self.status = taskStatus
        

class TaskFeedbackEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, clsTaskFeedback):
            return {
                'TimeStamp': obj.timestamp,
                'TaskName': obj.task_name,
                'TaskSimplex': obj.task_simplex,
                'TaskSequence': obj.task_seq,
                'PointIndex': obj.point_index,
                'TaskStatus': obj.status.value
            }
        return super().default(obj)



class AGVStatusEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, clsAGVSatus):
            return {
                'Time_Stamp': obj.Time_Stamp,
                'Coordination': obj.Coordination,
            }
        return super().default(obj)

@dataclass
class clsVMSReturn:
        ReturnCode :int
        Message:str
        
        
@dataclass
class clsOnlineModeQueryAck:
        RemoteMode : ONLINE_MODE
        TimeStamp:str



class clsAutoDoor:
        Key_Name:str
        Key_Password:str
        
class clsControlMode:
       Dodge :int
       Spin :int
        

class clsPoint:
       Point_ID : int
       X :float
       Y:float
       Theta:float
       Laser:int
       Speed:float 
       UltrasonicDistance:float 
       Map_Name:str 
       Auto_Door:clsAutoDoor 
       Control_Mode:clsAutoDoor 

class clsCST:
       CST_ID:str
       CST_Type:int

class clsTaskDownload:
       Task_Name:str
       Task_Simplex:str
       Task_Sequence:int
       Trajectory:List[clsPoint]
       Homing_Trajectory:List[clsPoint]
       Action_Type:ACTION_TYPE
       CST:clsCST
       Destination:int
       Height:int
       Escape_Flag:bool
       Station_Type:STATION_TYPE
       
