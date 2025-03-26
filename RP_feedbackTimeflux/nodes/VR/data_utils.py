import importlib
import pandas as pd
import json
from timeflux.core.node import Node
from timeflux.helpers.clock import now

class DataframeMerge(Node):
    def __init__(self, df1, df2):
        self.df1 = df1 
        self.df2 = df2
        self.axis = 1  
        self.ignore_index = False  
        self.round = 0

    def update(self):
        self.o.data =pd.DataFrame({
                "calibration_codes":[str(self.df1)],
                "task_codes":[str(self.df2)]})
        if self.round == 0:
            self.round+=1

class StringToDictionary_epochs(Node):
    def __init__(self):
        self.strArray = None    

    def update(self):
        if self.i.ready():
            index_value = self.i.data.index[0] 
            i_label = str(self.i.data["label"].iloc[0]) 
            i_data = str(self.i.data["data"].iloc[0]).replace(" ", "") 

            params = i_data.split(";")

            o_data = {}
            for param in params:
                if ":" in param:
                    key, value = param.split(":")
                    if key == "bits":
                        o_data[key] = [int(x) for x in value.strip('[]').split(',')]
                    else:
                        o_data[key] = int(value) 
                else:
                    o_data[param] = "" 

            o_data_json = json.dumps(o_data)  

            self.o.data = pd.DataFrame([[i_label, o_data_json]], columns=["label", "data"], index=[index_value])
            self.o.meta = self.i.meta


class StringToDictionary_targetChange(Node):
    def __init__(self):
        self.strArray = None    

    def update(self):
        if self.i.ready():
            index_value = self.i.data.index[0] 
            i_label = str(self.i.data["label"].iloc[0]) 
            i_data = str(self.i.data["data"].iloc[0]).replace(" ", "")  

            self.o.data = pd.DataFrame([[i_label, i_data]], columns=["label", "data"], index=[index_value])
            self.o.meta = self.i.meta