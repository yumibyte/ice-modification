# Modifications to the ICE repository

## Automatic prompt/question testing:
- To test out many prompts/questions the "testDebates.py" file takes an input of a JSON of prompts/questions and writes them to an output file with the generated debate
- For each question, the TestDebates class will run against every prompt (e.g. if there is 1 question and 3 prompts, 3 rows will be generated in the CSV)
- Instructions to generate debate:
  - Modify the input JSON within debate/testDebates.py and debate/recipe.py The lines to modify include the following:
```
# testDebates.py
test_debates_instance = TestDebates("debate/my_input_name.json")
```
```
# recipe.py
test_debates_instance = testDebates.TestDebates("debate/my_input_name.json")
```
  - Modify the output CSV in debate/recipe.py to a desired name (the file does not need to be created)
```
# recipe.py
test_debates_instance.write_results("debate/my_output_name.csv", generated_debate)
```

## Generating a new input file
Files like debate/formatSciQ.py format a given input file into an appropriate JSON. The general format for generating a debate (required parameters) only needs a set of questions, question answers, and prompts.
```
TODO: add a sample input JSON format here (this is subject to change)
```
 
## Future of the project:
- Create an interface for prompt/question inputting
  - On the same note, remove the need to modify input/output files in multiple locations
- Test out debates with IBM Debater datasets
