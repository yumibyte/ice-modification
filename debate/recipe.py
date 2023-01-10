
# import pdb
# pdb.set_trace()

from ice.agents.base import Agent
from ice.recipe import recipe
from prompt import *

import testDebates

async def turn(debate: Debate, agent: Agent, agent_name: Name, turns_left: int):


    prompt = render_debate_prompt(agent_name, debate, turns_left)
    answer = await agent.complete(prompt=prompt, stop="\n")
    return (agent_name, answer.strip('" '))


async def debate(question: str):

    agents = [recipe.agent(), recipe.agent()]
    agent_names = ["Alice", "Bob"]
    debate = initialize_debate(question)
    turns_left = 8
    while turns_left > 0:
        for agent, agent_name in zip(agents, agent_names):
            response = await turn(debate, agent, agent_name, turns_left)
            debate.append(response)
            turns_left -= 1

    # write out the full debate to the current file
    # print("FULL DEBATE" + str(debate))
    # compile a new row of a generated prompt to be outputted to the csv
    # format: question, prompt, responses

    test_debates_instance = testDebates.TestDebates("debate/inputs.json")

    # generate instance of TestDebates to append results to a csv file
    generated_debate = [test_debates_instance.get_current_question(), test_debates_instance.get_current_prompt(), debate]
    test_debates_instance.write_results("debate/outputs.csv", generated_debate)

    return render_debate(debate)

recipe.main(debate)
