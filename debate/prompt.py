
import testDebates

from utils import *

def render_debate_prompt(agent_name: str, debate: Debate, turns_left: int) -> str:

    test_debates_instance = testDebates.TestDebates("debate/inputs.json")
    # retrieve correct prompt
    current_prompt = test_debates_instance.get_current_prompt()
    # print("CURRENT: " + current_prompt)

    prompt = f"""
    You are {agent_name}. There are {turns_left} turns left in the debate. {current_prompt}

    {render_debate(debate, agent_name)}
    You: "
    """.strip()

    return prompt
# print(render_debate_prompt("Bob", my_debate, 5, test_debates_instance.get_))
