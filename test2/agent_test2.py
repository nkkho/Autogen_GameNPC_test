import autogen
import json
from classes2 import Player, Villager, Monster

config_list = autogen.config_list_from_json(env_or_file="config.json")
llm_config = {"config_list": config_list, "temperature": 0.3,"cache_seed": 42, "timeout": 120,}

try:
    with open('test2/agent_settings2.json', 'r') as json_file:
        agent1_config = json.load(json_file)
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")

#character initialization
blacksmith = Villager(agent1_config[0],"WEREWOLF CLAW", {"WEAPON":1, "VILLAGE A BLACKSMITH LETTER":1},"VILLAGE A")
player = Player(agent1_config[1],"VILLAGE A")
#merchant = Villager(agent1_config[2],None,{"COIN":100},"VILLAGE A")
werewolf = Monster(5)

blacksmith.agent = autogen.AssistantAgent(name = blacksmith.config["name"], system_message=blacksmith.config["system_message1"],llm_config={"config_list":config_list})
player.agent = autogen.UserProxyAgent(name = player.config["name"], system_message=player.config["system_message"], llm_config={"config_list":config_list},
                                      code_execution_config={"work_dir": "groupchat", "timeout":120, "last_n_messages":2,"use_docker": False})
#merchant.agent = autogen.AssistantAgent(name = merchant.config["name"], system_message=merchant.config["system_message1"],llm_config={"config_list":config_list})


