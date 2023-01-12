import os
import json
import csv

# needed to check if the output file exists
from pathlib import Path

import pdb

class TestDebates:
    def __init__(self, file_name):
        JSON_loaded = open(file_name)
        self.file_name = file_name
        self.input_data = json.load(JSON_loaded)

    def reset_prompt_count(self):

        self.input_data["prompt_count"] = 0
        with open(self.file_name, "w") as outfile:
            json.dump(self.input_data, outfile)

    def reset_question_count(self):

        self.input_data["question_count"] = 0
        with open(self.file_name, "w") as outfile:
            json.dump(self.input_data, outfile)

    def get_prompts(self):
        return self.input_data["input_prompts"]

    # getters
    def get_current_prompt(self):
        prompts_list = self.get_prompts()
        prompt_count = self.input_data["prompt_count"]
        return prompts_list[prompt_count]

    def get_current_question(self):
        questions_list = self.get_questions()
        question_count = self.input_data["question_count"]
        return questions_list[question_count]

    def increment_current_prompt(self):
        prompt_count = self.input_data["prompt_count"]
        self.input_data["prompt_count"] = prompt_count + 1
        with open(self.file_name, "w") as outfile:
            json.dump(self.input_data, outfile)

    def increment_current_question(self):
        prompt_count = self.input_data["question_count"]
        self.input_data["question_count"] = prompt_count + 1
        with open(self.file_name, "w") as outfile:
            json.dump(self.input_data, outfile)

    def get_questions(self):

        return self.input_data["input_questions"]
        # "Should we legalize all drugs?",
        # "Is water wet?"

    def write_results(self, file_name, data):

        # check if the file exists. If it doesn't, ensure it has a proper header
        # before writing out results
        from pathlib import Path

        path = Path(file_name)

        # pdb.set_trace()
        if not path.is_file():

            with open(file_name, 'w', newline='') as file:

                # adding header
                headerList = ['Question', 'Prompt', 'Results']
                writer = csv.writer(file)
                writer.writerow(headerList)
                writer.writerow(data)
        else:
            with open(file_name,'a') as file:
                 writer = csv.writer(file)
                 writer.writerow(data)

                # data format: question, prompt, results
                # headerList = ['Question', 'Question_V', 'Prompt', 'Prompt_V' 'Results']
                # appends to existing csv



    # we need a bash prompt that will
    # execute recipe file with the above inputs
    def execute_debate(self):

        print(test_debates_instance)

        questions_list = test_debates_instance.get_questions()
        prompts_list = test_debates_instance.get_prompts()

        for prompt in prompts_list:

            for question in questions_list:

                command = f'python debate/recipe.py --question "{question}" '

                os.system(command)
                test_debates_instance.increment_current_question()

            test_debates_instance.reset_question_count()

            # increment our current prompt
            test_debates_instance.increment_current_prompt()

        # reset count variables for questions/prompts
        test_debates_instance.reset_prompt_count()

# Initialize our class of prompts/questions
if __name__ == "__main__":

    # initialize instance
    test_debates_instance = TestDebates("debate/inputs.json")

    # immediately start the program based on the prompts/questions
    test_debates_instance.execute_debate()

# [{"version": 1, "question": "Is a burger a hotdog?"}]
