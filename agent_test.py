import autogen
import json
from classes import Player, Villager

config_list = autogen.config_list_from_json(env_or_file="config.json")
llm_config = {"config_list": config_list, "temperature": 0.1,"cache_seed": 42, "timeout": 120,}

try:
    with open('agent_settings1.json', 'r') as json_file:
        agent1_config = json.load(json_file)
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")

#global variable used for state transition 

weapon:int = 0
reward = 1

blacksmith = Villager(agent1_config[0],"WEREWOLF CLAW", {"WEAPON":1, "VILLAGE A BLACKSMITH LETTER":1})
player = Player(agent1_config[1],"VILLAGE A")

blacksmith.agent = autogen.AssistantAgent(name = blacksmith.config["name"], system_message=blacksmith.config["system_message1"],llm_config={"config_list":config_list})
player.agent = autogen.UserProxyAgent(name = player.config["name"], system_message=player.config["system_message"], llm_config={"config_list":config_list},
                                      code_execution_config={"work_dir": "groupchat", "timeout":120, "last_n_messages":2,"use_docker": False})

def state_transition(last_speaker, groupchat):
    global weapon, reward

    messages = groupchat.messages

    if len(messages) <= 1:
        return blacksmith.agent
    if player.location == "VILLAGE A":
        if last_speaker is player.agent:
            if "GRASSLAND" in messages[-1]["content"]:
                print("At Grassland")
                player.location = "GRASSLAND"
                return player.agent
            elif blacksmith.quest_state == 2:
                if "REWARD" in messages[-1]["content"]:
                    player.mergeDict(blacksmith.reward)
                    player.updateItems(blacksmith.request, -1)
                    blacksmith.reward_state = 0
                    print("reward given")
                    if "WEREWOLF CLAW" in player.items.keys():
                        print("num_claws: "+str(player.items["WEREWOLF CLAW"]))
                    else:
                        print("num_claws: 0")
                    print("player_item:" + str(player.items))
                return blacksmith.agent
            return blacksmith.agent
        else:
            if blacksmith.quest_state == 0:
                if "werewolf claw" in messages[-1]["content"]:
                    blacksmith.quest_state = 1
                    blacksmith.agent.update_system_message(blacksmith.config["system_message2"])
            elif blacksmith.quest_state == 2 and blacksmith.reward_state == 0:
                #reactivate mission
                blacksmith.reward_state = 1
                blacksmith.quest_state = 0
                blacksmith.agent.update_system_message(blacksmith.config["system_message1"])
                
            return player.agent
    elif player.location == "GRASSLAND":
        if "WEREWOLF CLAW" in player.items.keys():
            blacksmith.quest_state = 2
            blacksmith.agent.update_system_message(blacksmith.config["system_message3"])
        if messages[-1]["content"] == "KILL WEREWOLF":
            player.updateItems("WEREWOLF CLAW",1)
            print("num_claw: "+ str(player.items["WEREWOLF CLAW"]))
        if "VILLAGE A" in messages[-1]["content"]:
            player.location = "VILLAGE A"
            print ("At Village A")
        return player.agent
    else:
        return None
        
            

groupchat = autogen.GroupChat(agents=[player.agent,blacksmith.agent],messages=[], max_round=20,speaker_selection_method=state_transition)
manager = autogen.GroupChatManager(groupchat=groupchat,llm_config=llm_config)

#original as recipient=blacksmith_agent

print("At Village A")
player.agent.initiate_chat(recipient=manager,message="Hi, nice to meet you. Do you need any help?")