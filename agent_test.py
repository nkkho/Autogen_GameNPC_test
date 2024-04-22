import autogen
import json
from classes import Player, Villager

config_list = autogen.config_list_from_json(env_or_file="config.json")
llm_config = {"config_list": config_list, "temperature": 0.3,"cache_seed": 42, "timeout": 120,}

try:
    with open('agent_settings1.json', 'r') as json_file:
        agent1_config = json.load(json_file)
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")


blacksmith = Villager(agent1_config[0],"WEREWOLF CLAW", {"WEAPON":1, "VILLAGE A BLACKSMITH LETTER":1},"VILLAGE A")
player = Player(agent1_config[1],"VILLAGE A")
merchant = Villager(agent1_config[2],None,{"COIN":100},"VILLAGE A")

blacksmith.agent = autogen.AssistantAgent(name = blacksmith.config["name"], system_message=blacksmith.config["system_message1"],llm_config={"config_list":config_list})
player.agent = autogen.UserProxyAgent(name = player.config["name"], system_message=player.config["system_message"], llm_config={"config_list":config_list},
                                      code_execution_config={"work_dir": "groupchat", "timeout":120, "last_n_messages":2,"use_docker": False})
merchant.agent = autogen.AssistantAgent(name = merchant.config["name"], system_message=merchant.config["system_message1"],llm_config={"config_list":config_list})

target = "BLACKSMITH"
def state_transition(last_speaker, groupchat):
    global target
    messages = groupchat.messages
    if len(messages) <=1:
        return blacksmith.agent if target == "BLACKSMITH" else merchant.agent
    if "VILLAGE A BLACKSMITH LETTER" in player.items.keys() and merchant.quest_state == 0:
        merchant.quest_state = 1
        merchant.agent.update_system_message(merchant.config["system_message2"])
    if player.location == "VILLAGE A":
        if last_speaker is player.agent:
            if "GRASSLAND" in messages[-1]["content"]:
                print("At Grassland")
                if merchant.quest_state == 2 and merchant.location != "GRASSLAND":
                    merchant.location = "GRASSLAND"
                    merchant.agent.update_system_message(merchant.config["system_message4"])
                player.location = "GRASSLAND"
                target = ""
                return player.agent
            elif "VILLAGE B" in messages[-1]["content"]:
                print("Have to pass through Grassland to go to Village B")
                return player.agent
            elif "BLACKSMITH" == messages[-1]["content"]:
                print("Talking to blacksmith")
                target = "BLACKSMITH"
                return player.agent
            elif "MERCHANT" == messages[-1]["content"]:
                print("Talking to merchant")
                target = "MERCHANT"
                return player.agent
            elif target == "BLACKSMITH":
                if blacksmith.quest_state == 2:
                    if "REWARD" in messages[-1]["content"]:
                        blacksmith.agent.update_system_message(blacksmith.config["system_message3"])
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
            elif target == "MERCHANT":
                return merchant.agent
            return player.agent
        elif last_speaker == blacksmith.agent:
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
        elif last_speaker == merchant.agent:
            if merchant.quest_state == 1 and ("Village B" in messages[-1]["content"] or "VILLAGE B" in messages[-1]["content"]):
                merchant.quest_state = 2
                merchant.agent.update_system_message(merchant.config["system_message3"])
            return player.agent
    #Grassland
    elif player.location == "GRASSLAND":
        if "WEREWOLF CLAW" in player.items.keys() and blacksmith.quest_state == 1:
            blacksmith.quest_state = 2
        if last_speaker == player.agent:
            if "VILLAGE A" in messages[-1]["content"]:
                if merchant.quest_state == 2 and merchant.location != "VILLAGE A":
                    merchant.location == "VILLAGE A"
                    merchant.agent.update_system_message(merchant.config["system_message3"])
                player.location = "VILLAGE A"
                target = ""
                print ("At Village A")
            if "VILLAGE B" in messages[-1]["content"]:
                target == ""
                player.location = "VILLAGE B"
                print("At Village B")
                if merchant.location != "VILLAGE B" and merchant.quest_state == 2:
                    merchant.location = "VILLAGE B"
                    merchant.quest_state = 3
                    merchant.agent.update_system_message(merchant.config["system_message5"])
            if "MERCHANT" == messages[-1]["content"]:
                print("Talking to merchant")
                target = "MERCHANT"
                return player.agent
            if merchant.location == player.location and target== "MERCHANT":
                if "LEAVE TALK" in messages[-1]["content"]:
                    target = ""
                    return player.agent
                return merchant.agent
            if messages[-1]["content"] == "KILL WEREWOLF":
                player.updateItems("WEREWOLF CLAW",1)
                print("num_claw: "+ str(player.items["WEREWOLF CLAW"]))
            return player.agent
        else:
            return player.agent  
    elif player.location == "VILLAGE B":
        if last_speaker == player.agent:
            if "MERCHANT" == messages[-1]["content"]:
                print("Talking to merchant")
                target = "MERCHANT"
                return player.agent
            if "MERCHANT" == target:
                if merchant.location == "VILLAGE B":
                    if "REWARD" in messages[-1]["content"] and merchant.quest_state == 3:
                            player.mergeDict(merchant.reward)
                            player.updateItems(merchant.request, -1)
                            merchant.reward_state = 0
                            print("reward given")
                            print("player_item:" + str(player.items))
                    return merchant.agent
                else:
                    print("merchant not in VILLAGE B")
                return player.agent
            if "BLACKSMITH" == messages[-1]["content"]:
                print("blacksmith not in VILLAGE B")
                return player.agent
        else:
            return player.agent
    return None
        
            

groupchat = autogen.GroupChat(agents=[player.agent,blacksmith.agent,merchant.agent],messages=[], max_round=40,speaker_selection_method=state_transition)
manager = autogen.GroupChatManager(groupchat=groupchat,llm_config=llm_config)

#original as recipient=blacksmith_agent

print("At Village A")
print("Talking to Blacksmith")
player.agent.initiate_chat(recipient=manager,message="Hi, nice to meet you. Do you need any help?")
