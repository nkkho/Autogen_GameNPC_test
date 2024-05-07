import autogen
import json
from classes2 import Player, Villager, Monster, generate_prompt, GameMaster
from typing import Final

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
gamemaster = GameMaster([blacksmith],player)
#merchant = Villager(agent1_config[2],None,{"COIN":100},"VILLAGE A")

gamemaster.agent = autogen.AssistantAgent(name="GameMaster",llm_config={"config_list":config_list},system_message="You are the game master of this game, you should make decision based on the chat_message and intruction given")
werewolf = Monster(5)
bsystem_message = generate_prompt(list(blacksmith.prompt_input.values()),blacksmith.config["message_path"])
blacksmith.agent = autogen.AssistantAgent(name = blacksmith.config["name"], system_message=bsystem_message,llm_config={"config_list":config_list})
player.agent = autogen.UserProxyAgent(name = player.config["name"], system_message=player.config["system_message"], llm_config={"config_list":config_list},
                                      code_execution_config={"work_dir": "groupchat", "timeout":120, "last_n_messages":2,"use_docker": False})
#merchant.agent = autogen.AssistantAgent(name = merchant.config["name"], system_message=merchant.config["system_message1"],llm_config={"config_list":config_list})
max_round: Final[int] = 15
round = 0
while round < max_round:
    print("Action to do")
    print(round)
    action = player.action()
    if (type(action)!=str):
        action = action['content']
    if (action == "TALK"):
        print("talking to blacksmith")
        speaker = None
        message = None
        while round < max_round:
            bquest_state=gamemaster.quest_state(blacksmith,player)
            if "NOT GIVEN" in bquest_state:
                blacksmith.switchqueststate("NOT GIVEN")
            elif "GIVEN" in bquest_state:
                blacksmith.switchqueststate("GIVEN")
            elif "COMPLETE" in bquest_state:
                blacksmith.switchqueststate("COMPLETE")
            if speaker==None:
                message = input("Player: ")
                if message=="END":
                    speaker = None
                    break
                player.broadcasting([blacksmith.agent,gamemaster.agent],message)
                speaker = blacksmith
            elif speaker==player:
                message = player.agent.generate_reply(sender=blacksmith.agent)
                print(f"{speaker.config['name']}: {message['content']}")
                player.broadcasting([blacksmith.agent,gamemaster.agent],message)
                if message["content"]=="END":
                    print("breaking")
                    speaker = None
                    break
                speaker = blacksmith
            elif speaker==blacksmith:
                print(f"blacksmith queststate: {blacksmith.quest_state}")
                if blacksmith.quest_state=="COMPLETE":
                    rewardgiving=blacksmith.rewardGiving()
                    print(rewardgiving)
                    if rewardgiving=="REWARD":
                        player.mergeDict(blacksmith.reward)
                        player.updateItems(blacksmith.request, -1)
                        blacksmith.reward_state = 0
                        blacksmith.quest_state = "NOT GIVEN"
                        blacksmith.prompt_input["quest_state"] = blacksmith.quest_state
                        blacksmith.update_system_message(blacksmith.config["message_path"],list(blacksmith.prompt_input.values()))
                        print("reward given")
                        if "WEREWOLF CLAW" in player.items.keys():
                            print("num_claws: "+str(player.items["WEREWOLF CLAW"]))
                        else:
                            print("num_claws: 0")
                        print("player_item:" + str(player.items))
                message = blacksmith.agent.generate_reply(sender=player.agent)
                print(f"{speaker.config['name']}: {message}")
                blacksmith.broadcasting([player.agent,gamemaster.agent],message)

                if message=="END":
                    speaker = None
                    break
                speaker = player
                print()
            round+=1
    elif action == "FIGHT":
        result = gamemaster.fight(player.strength,werewolf.strength)
        if result == "WIN":
            player.updateItems("WEREWOLF CLAW",1)
            gamemaster.broadcasting([player.agent,blacksmith.agent],"Player kills a werewolf")
            print("Player kills a werewolf")
            print("num_claw: "+ str(player.items["WEREWOLF CLAW"]))
    elif action == "VILLAGE A":
        print("At village A")
        player.location = "VILLAGE A"
    elif action == "GRASSLAND":
        print("At grassland")
        player.location = "GRASSLAND"
    else:
        break
    round+=1
