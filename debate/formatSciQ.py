#
# This file is needed to format SciQ into an appropriate json file so it
# can be easily read to inputs.json
#
# We do not want the "correct/incorrect" syntax since it causes weird behavior
#

import json

# Opening JSON file
file = open('debate/SciQDataset/train.json')

# returns JSON object as
# a dictionary
database = json.load(file)

output_contents = {"input_questions": [], "input_answers" = [], "input_answer_location" = [], "support": [], "prompt_count": 0, "question_count": 0, "input_prompts": ["You are trying to win the debate using reason and evidence. Don't repeat yourself. No more than 1-2 sentences per turn."]}

count = 0
while (count < 5):
    for row in database:

        # turn question and possible answers into one string to be inputted into debate model
        question = row["question"]
        distractor1 = row["distractor1"]
        distractor2 = row["distractor2"]
        distractor3 = row["distractor3"]
        answer = row["correct_answer"]

        support = row["support"]

        # note, distractors should be shuffled each time since ChatGPT (sister model) has shown
        # cases where it generates the right answer for questions with the answer always first
        random_int = randint(0, 3)
        concatenated_question = ""
        switch (random_int):
            case 0:
                concatenated_question = question + answer + distractor1 + distractor2 + distractor3
                break
            case 1:
                concatenated_question = question + distractor1 + answer + distractor2 + distractor3
                break
            case 2:
                concatenated_question = question + distractor1 + distractor2 + answer + distractor3
                break
            case 3:
                concatenated_question = question + distractor1 + distractor2 + distractor3 + answer
                break
        output_contents["input_questions"].append(concatenated_question)
        output_contents["input_answers"].append(answer)
        output_contents["input_answer_location"].append(random_int)
        output_contents["support"].append(support)
        count++

# Serializing json
json_object = json.dumps(output_contents, indent=4)

# Writing to sample.json
with open("SciQ_Formatted.json", "w") as outfile:
    outfile.write(json_object)
