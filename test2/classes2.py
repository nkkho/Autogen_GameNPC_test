from typing import Dict,List,Union
from collections import Counter

"""generate_prompt from @inproceedings{Park2023GenerativeAgents,  
author = {Park, Joon Sung and O'Brien, Joseph C. and Cai, Carrie J. and Morris, Meredith Ringel and Liang, Percy and Bernstein, Michael S.},  
title = {Generative Agents: Interactive Simulacra of Human Behavior},  
year = {2023},  
publisher = {Association for Computing Machinery},  
address = {New York, NY, USA},  
booktitle = {In the 36th Annual ACM Symposium on User Interface Software and Technology (UIST '23)},  
keywords = {Human-AI interaction, agents, generative AI, large language models},  
location = {San Francisco, CA, USA},  
series = {UIST '23}
}"""

def generate_prompt(curr_input, prompt_lib_file): 
  """
  Takes in the current input (e.g. comment that you want to classifiy) and 
  the path to a prompt file. The prompt file contains the raw str prompt that
  will be used, which contains the following substr: !<INPUT>! -- this 
  function replaces this substr with the actual curr_input to produce the 
  final promopt that will be sent to the GPT3 server. 
  ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file. 
  RETURNS: 
    a str prompt that will be sent to OpenAI's GPT server.  
  """
  if type(curr_input) == type("string"): 
    curr_input = [curr_input]
  curr_input = [str(i) for i in curr_input]

  f = open(prompt_lib_file, "r")
  prompt = f.read()
  f.close()
  for count, i in enumerate(curr_input):   
    prompt = prompt.replace(f"!<INPUT {count}>!", i)
  if "<commentblockmarker>###</commentblockmarker>" in prompt: 
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
  return prompt.strip()


class Player:
    def __init__(self, config,location:str):
        self.items: Dict[str,int] = {}
        self.agent = None
        self.config = config
        self.location = location
        self.strength = 10
    def updateItems(self,key:str,num:int) -> bool:
        if key == None:
            return True
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
    
    def moving(self, message):
        prompt = f"""You can go to following locations:
        VILLAGE A or GRASSLAND
        In VILLAGE A, you can talk to Blacksmith.
        In GRASSLAND, you can hunt and kill werewolf
        You are currently at {self.location}. Based on {message}, choose a location you want to go or stay.
        Reply 'VILLAGE A' if you want to go or stay at VILLAGE A, reply 'GRASSLAND' if you want to stay or go to GRASSLAND"""
        self.location = self.agent.generate_reply({"content":prompt, "role":'user'})

    
class Villager:
    def __init__(self,config,request_item:str,reward:Dict[str,int],location:str):
        self.agent = None
        self.quest_state = "NOT GIVEN"
        self.config = config
        self.request = request_item
        self.reward = reward
        self.reward_state = 1
        self.location = location
    
    def update_system_message(self, filepath, cur_input):
        message = generate_prompt(cur_input,filepath)
        self.agent.update_system_message(message)
        

    def quest_completion(self,items: Dict[str,int]):
        if self.request in items.keys():
            self.quest_state = "completed"

    

class Monster:
    def __init__(self, strength) -> None:
        self.strength = strength

class GameMaster:
    def __init__(self,villagers:List[Villager],player:Player) -> None:
        self.agent = None
        self.villagers = villagers
        self.player = player

    def fight(self,player:int,monster:int):
        prompt = f"""You are the game master of this game. Now Player and Werewolf are Fighting. 
        Player's strength is {player}. Werewolf's strength is {monster}.
        Based on their strength, determines who wins. If player wins, reply 'WIN', else reply 'LOSE'"""

        self.agent.update_system_message(prompt)
        return self.agent.generate_reply({"content":prompt, "role":'user'})

    def broadcasting(self, agents:List,message):
        for agent in agents:
            self.agent.send(message,agent, request_reply=False, silent=True)

    def conversation_initiation(character1:Union[Villager,Player], character2:Union[Villager,Player],message):
        if character1.location == character2.location:
            character1.agent.initiate_chat(recipient=character2.agent, clear_history=False, message=message)
        else:
            print(f"Not in same location. \n {character1.config['name']} in {character1.location}. {character2.config['name']} in {character2.location}")
    
