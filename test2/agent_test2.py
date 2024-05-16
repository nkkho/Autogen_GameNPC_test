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
gamemaster = GameMaster()
#merchant = Villager(agent1_config[2],None,{"COIN":100},"VILLAGE A")

gamemaster.agent = autogen.AssistantAgent(name="GameMaster",llm_config={"config_list":config_list},system_message="You are the game master of this game, you should make decision based on the chat_message and intruction given")
werewolf = Monster(5)
bsystem_message = generate_prompt(list(blacksmith.prompt_input.values()),blacksmith.config["message_path"])
blacksmith.agent = autogen.AssistantAgent(name = blacksmith.config["name"], system_message=bsystem_message,llm_config={"config_list":config_list})
player.agent = autogen.UserProxyAgent(name = player.config["name"], system_message=player.config["system_message1"], llm_config={"config_list":config_list},
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
        if player.location != "VILLAGE A":
            print("You are not at Village A, cannot talk to Blacksmith")
            continue
        print("talking to blacksmith")
        speaker = None
        message = None
        while round < max_round:
            if blacksmith.quest_state != "DONE" and blacksmith.quest_state != "COMPLETE":
                bquest_state=gamemaster.quest_state(blacksmith,player)
                print(f"master state answer: {bquest_state}")
                if "NOT GIVEN" in bquest_state:
                    blacksmith.switchqueststate("NOT GIVEN")
                elif "GIVEN" in bquest_state:
                    blacksmith.switchqueststate("GIVEN")
                    player.add_quest(blacksmith)
                    #player.agent.update_system_message(player.config["system_message2"])
                elif "COMPLETE" in bquest_state:
                    blacksmith.switchqueststate("COMPLETE")
            print(f"blacksmith queststate: {blacksmith.quest_state}")

            if speaker==None:
                message = input("Player: ")
                if message=="END":
                    speaker = None
                    break
                player.broadcasting([blacksmith.agent],message)
                gamemaster.joinConversation(player,blacksmith,f"Player: {message}")
                speaker = blacksmith
            elif speaker==player:
                message = player.agent.generate_reply(sender=blacksmith.agent)
                if type(message)!=str:
                    output = message["content"]
                else:
                    output = message
                print(f"{speaker.config['name']}: {output}")
                if message["content"]=="END":
                    speaker = None
                    break
                player.broadcasting([blacksmith.agent],message)
                gamemaster.joinConversation(player,blacksmith,f"{speaker.config['name']}: {message['content']}")
                
                speaker = blacksmith
            elif speaker==blacksmith:
                if blacksmith.quest_state=="COMPLETE" and blacksmith.reward_state > 0:
                    if type(message)!=str:
                        output = message["content"]
                    else:
                        output = message
                    rewardgiving=blacksmith.rewardGiving(output)
                    print("blacksmith decision on rewardgiving: ",rewardgiving[0])
                    if "YES" in rewardgiving[0]:
                        #blacksmith.broadcasting([blacksmith.agent],"Player complete the mission and brings you a WEREWOLF CLAW")
                        player.mergeDict(blacksmith.reward)
                        player.updateItems(blacksmith.request, -1)
                        blacksmith.reward_state = 0
                        blacksmith.switchqueststate("DONE")
                        if blacksmith.config["job"] in player.quest.keys():
                            player.quest.pop(blacksmith.config["job"])
                        print("reward given")
                        if "WEREWOLF CLAW" in player.items.keys():
                            print("num_claws: "+str(player.items["WEREWOLF CLAW"]))
                        else:
                            print("num_claws: 0")
                        print("player_item:" + str(player.items))
                    message = rewardgiving[1]
                else:
                    message = blacksmith.agent.generate_reply(sender=player.agent)
                print(f"{speaker.config['name']}: {message}")
                if message=="END":
                    speaker = None
                    break
                gamemaster.joinConversation(player,blacksmith,f"{speaker.config['name']}: {message}")
                blacksmith.broadcasting([player.agent],message)
                speaker = player
            print()
            round+=1
    elif action == "FIGHT":
        if player.location != "GRASSLAND":
            print("You are not at grassland, cannot fight with werewolf")
            continue
        result = gamemaster.fight(player.strength,werewolf.strength)
        if result == "WIN":
            player.updateItems("WEREWOLF CLAW",1)
            gamemaster.broadcasting([player.agent,blacksmith.agent],"Player kills a werewolf and collect a WEREWOLF CLAW")
            print("Player kills a werewolf")
            print("num_claw: "+ str(player.items["WEREWOLF CLAW"]))
    elif action == "VILLAGE A":
        print("At Village A")
        player.location = "VILLAGE A"
    elif action == "GRASSLAND":
        print("At Grassland")
        player.location = "GRASSLAND"
    else:
        break
    round+=1
