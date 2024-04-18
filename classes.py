from typing import Dict
from collections import Counter

class Player:
    def __init__(self, config,location:str):
        self.items: Dict[str,int] = {}
        self.agent = None
        self.config = config
        self.location = location
    def updateItems(self,key:str,num:int) -> bool:
        if key in self.items.keys():
            cur = self.items[key]
            if cur+num < 0:
                return False
            self.items[key] += num
        else:
            if (num <= 0):
                return False
            self.items[key]=num
        if self.items[key] == 0:
            self.items.pop(key)
        return True
    def mergeDict(self, other:Dict[str,int]):
        self.items = dict(Counter(self.items) + Counter(other))

    
class Villager:
    def __init__(self,config,request_item:str,reward:Dict[str,int]):
        self.agent = None
        self.quest_state = 0
        self.config = config
        self.request = request_item
        self.reward = reward
        self.reward_state = 1