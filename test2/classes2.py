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

class Villager:
    def __init__(self,config,request_item:str,reward:Dict[str,int],location:str):
        self.agent = None
        self.quest_state:str = "NOT GIVEN"
        self.config = config
        self.request = request_item
        self.reward = reward
        self.reward_state = 1
        self.location = location
        self.prompt_input = {"name":self.config["name"],"living":self.config["living"],"location":self.location,
                                "quest":self.config["quest"],"quest_state":self.quest_state,"personality":self.config["personality"],"job":self.config["job"],"reward":self.reward}
    def update_system_message(self, filepath):
        message = generate_prompt(list(self.prompt_input.values()),filepath)
        self.agent.update_system_message(message)

    def switchqueststate(self,newState:str):
        if newState == self.quest_state:
            return
        self.quest_state = newState
        self.prompt_input["quest_state"]= newState
        self.update_system_message(self.config["message_path"])

    def broadcasting(self, agents:List,message):
        for agent in agents:
            self.agent.send(message,agent, request_reply=False, silent=True)
        
    def rewardGiving(self): 
        prompt = f"""current quest state is {self.quest_state}. Based on the chat_messages, decide whether to give player the reward or not.
        Only give the reward when quest state is completed and when player request.
        Reply 'REWARD' if you will give reward to the user. Reply 'NO' if you are not giving reward to the user."""
        return self.agent.generate_reply([{"content":prompt,"role":"assistant"}],sender=self,silent=True)


class Player:
    def __init__(self, config,location:str):
        self.items: Dict[str,int] = {}
        self.agent = None
        self.config = config
        self.location = location
        self.strength = 10
        self.quest: Dict[str,str] = {}
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
    
    def action(self):
        prompt = f""" There are two location that you can go: VILLAGE A and GRASSLAND. You can perform different action in different location.
        In VILLAGE A, you can talk to Blacksmith.
        In GRASSLAND, you can hunt and kill werewolf.
        You have to go to VILLAGE A to talk to Blacksmith.
        You have to go to GRASSLAND to kill werewolf.

        You are currently at {self.location}. You have receive some quest as follows:
        {'\n'.join(f"{key}: {value}" for key, value in self.quest.items())}

        Action list:
        Reply 'TALK' if you want to talk to Blacksmith
        Reply 'FIGHT' if you want to fight with werewolf
        Reply 'VILLAGE A' if you want to go to VILLAGE A
        Reply 'GRASSLAND' if you want to go to GRASSLAND

        Question: What action do you want to take from Action List based on above information and chat_history?"""
        return self.agent.generate_reply([{"content":prompt, "role":"user"}])
    
    def add_quest(self,villager:Villager):
        if villager.config["job"] in self.quest.keys():
            return
        newquest:str = villager.config["quest"]
        self.quest[villager.config["job"]] = newquest
    
    def broadcasting(self, agents:List,message):
        for agent in agents:
            self.agent.send(message,agent, request_reply=False, silent=True)

class Monster:
    def __init__(self, strength) -> None:
        self.strength = strength

class GameMaster:
    def __init__(self) -> None:
        self.agent = None
        self.conversation:Dict[str,str] = {}
    def joinConversation(self, player:Player,villager:Villager, message:str):
        key = f"{player.config['name']} {villager.config['job']}"
        if key in self.conversation.keys():
            '\n'.join([self.conversation[key],message])
        else:
            self.conversation[key] = message
    def fight(self,player:int,monster:int):
        prompt = f"""Now Player and Werewolf are Fighting. 
        Player's strength is {player}. Werewolf's strength is {monster}.

        Question: Based on their strength, who will win?
        
        If player wins, reply 'WIN', else reply 'LOSE'"""

        return self.agent.generate_reply([{"content":prompt, "role":'user'}],silent=True)

    def broadcasting(self, agents:List,message):
        for agent in agents:
            self.agent.send(message,agent, request_reply=False, silent=True)

    def quest_state(self, villager:Villager,player:Player):
        prompt = f"""Villager ({villager.config["name"]}) with agent({villager.agent}) states are as follows:
        quest: {villager.config["quest"]}, current location: {villager.location}, current quest state: {villager.quest_state}, reward to be given: {villager.reward}
        
        Player with agent ({player.agent}) states are as follows:
        item player have: {player.items}, current location:{player.location}

        Their conversation:
        {self.conversation[f'{player.config["name"]} {villager.config["job"]}'] if f'{player.config["name"]} {villager.config["job"]}' in self.conversation.keys() else ''}

        Condition of switching of Villager quest state as follows:
        'NOT GIVEN' to 'GIVEN' if Villager have given player the quest but player not yet finish the quest;;
        'GIVEN' to 'SUCCESS' if player collect Villager's required item;;
        'SUCCESS' to 'COMPLETE' if player receive reward from Villager;;
        Stay at 'COMPLETE'

        Question: Based on above information, what is Villager's new quest state?
        Reply one of the following option:
        'NOT GIVEN' or 'GIVEN' or 'SUCCESS' or 'COMPLETE'
        """
        return self.agent.generate_reply([{"content":prompt, "role":"assistant"}],silent=True)
