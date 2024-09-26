# Challenges Data Schema of Benchmark

## General challenges

Input:

- **name** (str): Name of the challenge.
- **category** (str[]): Category of the challenge such as 'basic', 'retrieval', 'comprehension', etc. _this is not currently used. for the future it may be needed_
- **task** (str): The task that the agent needs to solve.
- **dependencies** (str[]): The dependencies that the challenge needs to run. Needs to be the full node to the test function.
- **ground** (dict): The ground truth.
  - **answer** (str): The raw text of the ground truth answer.
  - **should_contain** (list): The exact strings that are required in the final answer.
  - **should_not_contain** (list): The exact strings that should not be in the final answer.
  - **files** (list): Files that are used for retrieval. Can specify file here or an extension.
- **mock** (dict): Mock response for testing.
  - **mock_func** (str): Function to mock the agent's response. This is used for testing purposes.
  - **mock_task** (str): Task to provide for the mock function.
- **info** (dict): Additional info about the challenge.
  - **difficulty** (str): The difficulty of this query.
  - **description** (str): Description of the challenge.
  - **side_effects** (str[]): Describes the effects of the challenge.

Example:

```json
{
  "category": ["basic"],
  "task": "Print the capital of America to a .txt file",
  "dependencies": ["TestWriteFile"], // the class name of the test
  "ground": {
    "answer": "Washington",
    "should_contain": ["Washington"],
    "should_not_contain": ["New York", "Los Angeles", "San Francisco"],
    "files": [".txt"],
    "eval": {
      "type": "llm" or "file" or "python",
      "scoring": "percentage" or "scale" or "binary", // only if the type is llm
      "template": "rubric" or "reference" or "custom" // only if the type is llm
    }
  },
  "info": {
    "difficulty": "basic",
    "description": "Tests the writing to file",
    "side_effects": ["tests if there is in fact an LLM attached"]
  }
}
```

## Evals

This is the method of evaluation for a challenge.

### file

This is the default method of evaluation. It will compare the files specified in "files" field to the "should_contain" and "should_not_contain" ground truths.

### python

This runs a python function in the specified "files" which captures the print statements to be scored using the "should_contain" and "should_not_contain" ground truths.

### llm

This uses a language model to evaluate the answer.

- There are 3 different templates - "rubric", "reference", and "custom". "rubric" will evaluate based on a rubric you provide in the "answer" field. "reference" will evaluate based on the ideal reference response in "answer". "custom" will not use any predefined scoring method, the prompt will be what you put in "answer".
- The "scoring" field is used to determine how to score the answer. "percentage" will assign a percentage out of 100. "scale" will score the answer 1-10. "binary" will score the answer based on whether the answer is correct or not.
- You can still use the "should_contain" and "should_not_contain" fields to directly match the answer along with the llm eval.

## Add files to challenges:

### artifacts_in

This folder contains all the files you want the agent to have in its workspace BEFORE the challenge starts

### artifacts_out

This folder contains all the files you would like the agent to generate. This folder is used to mock the agent.
This allows to run agbenchmark --test=TestExample --mock and make sure our challenge actually works.

### custom_python

This folder contains files that will be copied into the agent's workspace and run after the challenge is completed.
For example we can have a test.py in it and run this file in the workspace to easily import code generated by the agent.
Example: TestBasicCodeGeneration challenge.