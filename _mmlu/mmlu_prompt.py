import json

EXAMPLE = {
    "thought": "**Insights:**\nYour insights on what should be the next interesting agent.\n**Overall Idea:**\nyour reasoning and the overall concept behind the agent design.\n**Implementation:**\ndescribe the implementation step by step.",
    "name": "Name of your proposed agent",
    "code": """def forward(self, taskInfo):
    # Your code here
    return answer
"""
}

COT = {
    "thought": "By encouraging the LLM to think step by step rather than directly outputting an answer, chain-of-thought reasoning enables complex problem-solving through intermediate steps. This practice improves the model's ability to handle tasks that require deeper reasoning and provides insight into its decision-making process.",
    "name": "Chain-of-Thought",
    "code": """def forward(self, taskInfo):
    # Instruction for the Chain-of-Thought (CoT) approach
    # It is an important practice that allows the LLM to think step by step before solving the task.
    cot_instruction = "Please think step by step and then solve the task."

    # Instantiate a new LLM agent specifically for CoT
    # To allow LLM thinking before answering, we need to set an additional output field 'thinking'.
    cot_agent = LLMAgentBase(['thinking', 'answer'], 'Chain-of-Thought Agent')

    # Prepare the inputs for the CoT agent
    # The input should be a list of Info, and the first one is often the taskInfo
    cot_agent_inputs = [taskInfo]

    # Get the response from the CoT agent
    thinking, answer = cot_agent(cot_agent_inputs, cot_instruction)

    # Return only the final answer
    return answer
"""
}

COT_SC = {"thought": "While an LLM can arrive at the correct answer, its reasoning may vary. By repeatedly asking the same question with high temperature settings, we can generate different reasoning paths. We then combine multiple answers from these Chain-of-Thought (CoT) agents to produce a more accurate final answer through ensembling.",
          "name": "Self-Consistency with Chain-of-Thought",
          "code": """def forward(self, taskInfo):
    # Instruction for step-by-step reasoning
    cot_instruction = "Please think step by step and then solve the task."
    N = 5 # Number of CoT agents

    # Initialize multiple CoT agents with a higher temperature for varied reasoning
    cot_agents = [LLMAgentBase(['thinking', 'answer'], 'Chain-of-Thought Agent', temperature=0.8) for _ in range(N)]

    # Majority voting function to select the most common answer
    from collections import Counter
    def majority_voting(answers):
        return Counter(answers).most_common(1)[0][0]
    
    possible_answers = []
    for i in range(N):
        thinking, answer = cot_agents[i]([taskInfo], cot_instruction)
        possible_answers.append(answer.content)

    # Ensembling the answers from multiple CoT agents
    answer = majority_voting(possible_answers)
    return answer  
"""
          }

Reflexion = {
    "thought": "To enhance its performance, an LLM can iteratively improve its answer based on feedback. By reflecting on its previous attempts and incorporating feedback, the model can refine its reasoning and provide a more accurate solution.",
    "name": "Self-Refine (Reflexion)",
    "code": """def forward(self, taskInfo):
    # Instruction for initial reasoning
    cot_initial_instruction = "Please think step by step and then solve the task."

    # Instruction for reflecting on previous attempts and feedback to improve
    cot_reflect_instruction = "Given previous attempts and feedback, carefully consider where you could go wrong in your latest attempt. Using insights from previous attempts, try to solve the task better."
    cot_agent = LLMAgentBase(['thinking', 'answer'], 'Chain-of-Thought Agent')

    # Instruction for providing feedback and correcting the answer
    critic_instruction = "Please review the answer above and criticize on where might be wrong. If you are absolutely sure it is correct, output 'True' in 'correct'."
    critic_agent = LLMAgentBase(['feedback', 'correct'], 'Critic Agent')
    
    N_max = 5 # Maximum number of attempts

    # Initial attempt
    cot_inputs = [taskInfo]
    thinking, answer = cot_agent(cot_inputs, cot_initial_instruction, 0)

    for i in range(N_max):
        # Get feedback and correct status from the critic
        feedback, correct = critic_agent([taskInfo, thinking, answer], critic_instruction, i)
        if correct.content == 'True':
            break
            
        # Add feedback to the inputs for the next iteration
        cot_inputs.extend([thinking, answer, feedback])

        # Reflect on previous attempts and refine the answer
        thinking, answer = cot_agent(cot_inputs, cot_reflect_instruction, i + 1)
    return answer
"""
}

LLM_debate = {
    "thought": "By letting different LLMs debate with each other, we can leverage their diverse perspectives to find better solutions for tasks.",
    "name": "LLM Debate",
    "code": """def forward(self, taskInfo):
    # Instruction for initial reasoning
    debate_initial_instruction = "Please think step by step and then solve the task."

    # Instruction for debating and updating the solution based on other agents' solutions
    debate_instruction = "Given solutions to the problem from other agents, consider their opinions as additional advice. Please think carefully and provide an updated answer."
    
    # Initialize debate agents with different roles and a moderate temperature for varied reasoning
    debate_agents = [LLMAgentBase(['thinking', 'answer'], 'Debate Agent', temperature=0.8, role=role) for role in ['Biology Expert', 'Physics Expert', 'Chemistry Expert', 'Science Generalist']]

    # Instruction for final decision-making based on all debates and solutions
    final_decision_instruction = "Given all the above thinking and answers, reason over them carefully and provide a final answer."
    final_decision_agent = LLMAgentBase(['thinking', 'answer'], 'Final Decision Agent', temperature=0.1)

    max_round = 2 # Maximum number of debate rounds
    all_thinking = [[] for _ in range(max_round)]
    all_answer = [[] for _ in range(max_round)]

    # Perform debate rounds
    for r in range(max_round):
        for i in range(len(debate_agents)):
            if r == 0:
                thinking, answer = debate_agents[i]([taskInfo], debate_initial_instruction)
            else:
                input_infos = [taskInfo] + [all_thinking[r-1][i]] + all_thinking[r-1][:i] + all_thinking[r-1][i+1:]
                thinking, answer = debate_agents[i](input_infos, debate_instruction)
            all_thinking[r].append(thinking)
            all_answer[r].append(answer)
    
    # Make the final decision based on all debate results and solutions
    thinking, answer = final_decision_agent([taskInfo] + all_thinking[max_round-1] + all_answer[max_round-1], final_decision_instruction)
    return answer
"""
}

Take_a_step_back = {"thought": "Let LLM first think about the principles involved in solving this task which could be helpful. By understanding the underlying principles, the model can better reason through the problem and provide a more accurate solution.",
                    "name": "Step-back Abstraction",
                    "code": """def forward(self, taskInfo):
        # Instruction for understanding the principles involved in the task
        principle_instruction = "What are the physics, chemistry or biology principles and concepts involved in solving this task? First think step by step. Then list all involved principles and explain them."
        
        # Instruction for solving the task based on the principles
        cot_instruction = "Given the question and the involved principle behind the question, think step by step and then solve the task."
        
        # Instantiate LLM agents
        principle_agent = LLMAgentBase(['thinking', 'principle'], 'Principle Agent')
        cot_agent = LLMAgentBase(['thinking', 'answer'], 'Chain-of-Thought Agent')
        
        # Get the principles involved in the task
        thinking, principle = principle_agent([taskInfo], principle_instruction)

        # Use the principles to solve the task
        thinking, answer = cot_agent([taskInfo, thinking, principle], cot_instruction)
        return answer
"""
                    }

QD = {"thought": "Similar to Quality-Diversity methods, let LLM generate multiple diverse interesting solutions could help. By encouraging the model to explore different reasoning paths, we can increase the chances of finding the best solution.",
      "name": "Quality-Diversity",
      "code": """def forward(self, taskInfo):
    # Instruction for initial reasoning
    cot_initial_instruction = "Please think step by step and then solve the task."

    # Instruction for giving diverse answers
    qd_instruction = "Given previous attempts, try to come up with another interesting way to solve the task."
    cot_agent = LLMAgentBase(['thinking', 'answer'], 'Chain-of-Thought Agent')

    # Instruction for final decision-making based on collected reasoning and answers
    final_decision_instruction = "Given all the above solutions, reason over them carefully and provide a final answer."
    final_decision_agent = LLMAgentBase(['thinking', 'answer'], 'Final Decision Agent', temperature=0.1)
    
    N_max = 3 # Maximum number of attempts

    # Initial attempt
    cot_inputs = [taskInfo]
    possible_answers = []
    thinking, answer = cot_agent(cot_inputs, cot_initial_instruction, 0)

    # Add the answer to the list of possible answers
    possible_answers.extend([thinking, answer])

    for i in range(N_max):
        # Reflect on previous attempts and generate another interesting answer
        cot_inputs.extend([thinking, answer])

        # Generate another interesting answer
        thinking, answer = cot_agent(cot_inputs, qd_instruction, i + 1)
        possible_answers.extend([thinking, answer])

    # Make the final decision based on all generated answers
    thinking, answer = final_decision_agent([taskInfo] + possible_answers, final_decision_instruction)
    return answer
"""
      }

Role_Assignment = {"thought": "Similar to Auto-GPT and expert prompting, we can use dynamic control flow in the design to let the agent decide what expert we should use.",
                   "name": "Dynamic Assignment of Roles",
                   "code": """def forward(self, taskInfo):
        # Instruction for step-by-step reasoning
        cot_instruction = "Please think step by step and then solve the task."
        expert_agents = [LLMAgentBase(['thinking', 'answer'], 'Expert Agent', role=role) for role in ['Physics Expert', 'Chemistry Expert', 'Biology Expert', 'Science Generalist']]

        # Instruction for routing the task to the appropriate expert
        routing_instruction = "Given the task, please choose an Expert to answer the question. Choose from: Physics, Chemistry, Biology Expert, or Science Generalist."
        routing_agent = LLMAgentBase(['choice'], 'Routing agent')

        # Get the choice of expert to route the task
        choice = routing_agent([taskInfo], routing_instruction)[0]

        if 'physics' in choice.content.lower():
            expert_id = 0
        elif 'chemistry' in choice.content.lower():
            expert_id = 1
        elif 'biology' in choice.content.lower():
            expert_id = 2
        else:
            expert_id = 3 # Default to Science Generalist

        thinking, answer = expert_agents[expert_id]([taskInfo], cot_instruction)
        return answer
"""
                   }

system_prompt = """You are a helpful assistant. Make sure to return in a WELL-FORMED JSON object."""

base = """# Overview
You are an expert machine learning researcher testing various agentic systems. Your objective is to design building blocks such as prompts and control flows within these systems to solve complex tasks. Your aim is to design an optimal agent performing well on the MMLU (Massive Multitask Language Understanding) benchmark, a challenging evaluation that assesses a model's ability to answer questions across a wide range of subjects and difficulty levels. It includes subjects from STEM, social sciences, humanities, and more.

## An example question from MMLU:

Answer the following multiple choice question.

The constellation ... is a bright W-shaped constellation in the northern sky.

(A) Centaurus
(B) Cygnus
(C) Cassiopeia
(D) Cepheus

# The utility code:

```python
from collections import namedtuple
from typing import Union
import numpy as np
import json

import openai
import backoff
from utils import random_id

# Initialize the OpenAI client
client = openai.OpenAI()

# Named tuple for holding task information
Info = namedtuple('Info', ['name', 'author', 'content', 'iteration_idx'])

# Format instructions for LLM response
FORMAT_INST = lambda request_keys: f"Reply EXACTLY with the following JSON format.\n{str(request_keys)}\nDO NOT MISS ANY FIELDS AND MAKE SURE THE JSON FORMAT IS CORRECT!\n"

# Description of the role for the LLM
ROLE_DESC = lambda role: f"You are a {role}."

@backoff.on_exception(backoff.expo, openai.RateLimitError)
def get_json_response_from_gpt(msg, system_message, temperature=0.5):
    \"""
    Function to get JSON response from GPT model.
    
    Args:
    - msg (str): The user message.
    - system_message (str): The system message.
    - temperature (float): Sampling temperature.
    
    Returns:
    - dict: The JSON response.
    \"""
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": msg},
        ],
        temperature=temperature,
        max_tokens=1024,
        stop=None,
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content
    json_dict = json.loads(content)
    return json_dict

class LLMAgentBase:
    \"""
    Base class for an LLM agent.
    
    Attributes:
    - output_fields (list): Fields expected in the output.
    - agent_name (str): Name of the agent.
    - role (str): Role description for the agent.
    - temperature (float): Sampling temperature.
    - id (str): Unique identifier for the agent instance.
    \"""

    def __init__(self, output_fields: list, agent_name: str, role='helpful assistant', temperature=0.5) -> None:
        self.output_fields = output_fields
        self.agent_name = agent_name
        self.role = role
        self.temperature = temperature
        self.id = random_id()
    
    def generate_prompt(self, input_infos, instruction) -> str:
        \"""
        Generates a prompt for the LLM.
        
        Args:
        - input_infos (list): List of input information.
        - instruction (str): Instruction for the task.
        
        Returns:
        - tuple: System prompt and user prompt.

        An example of a generated prompt:
        ""
        You are a helpful assistant.
        
        # Output Format:
        Reply EXACTLY with the following JSON format.
        ...

        # Your Task:
        You will be given some number of paired example inputs and outputs. The outputs ...

        ### thinking #1 by Chain-of-Thought Agent hkFo (yourself):
        ...
        
        ### code #1 by Chain-of-Thought Agent hkFo (yourself):
        ...

        ### answer by Chain-of-Thought Agent hkFo's code evaluator:...


        # Instruction: 
        Please think step by step and then solve the task by writing the code.
        ""
        \"""
        output_fields_and_description = {key: f"Your {key}." if not 'answer' in key else f"Your {key}. Return ONLY the alphabet choice, i.e. A or B or C or D." for key in self.output_fields}
        system_prompt = ROLE_DESC(self.role) + "\n\n" + FORMAT_INST(output_fields_and_description)

        input_infos_text = ''
        for input_info in input_infos:
            if isinstance(input_info, Info):
                (field_name, author, content, iteration_idx) = input_info
            else:
                continue
            if author == self.__repr__():
                author += ' (yourself)'
            if field_name == 'task':
                input_infos_text += f'# Your Task:\n{content}\n\n'
            elif iteration_idx != -1:
                input_infos_text += f'### {field_name} #{iteration_idx+1} by {author}:\n{content}\n\n'
            else:
                input_infos_text += f'### {field_name} by {author}:\n{content}\n\n'

        prompt = input_infos_text + instruction
        return system_prompt, prompt 

    def query(self, input_infos: list, instruction, iteration_idx=-1) -> list[Info]:
        \"""
        Queries the LLM with provided input information and instruction.
        
        Args:
        - input_infos (list): List of input information.
        - instruction (str): Instruction for the task.
        - iteration_idx (int): Iteration index for the task.
        
        Returns:
        - output_infos (list[Info]): Output information.
        \"""
        system_prompt, prompt = self.generate_prompt(input_infos, instruction)
        response_json = get_json_response_from_gpt(prompt, system_prompt, self.temperature)

        output_infos = []
        for key, value in response_json.items():
            info = Info(key, self.__repr__(), value, iteration_idx)
            output_infos.append(info)
        return output_infos

    def __repr__(self):
        return f"{self.agent_name} {self.id}"
    
    def __call__(self, input_infos: list, instruction, iteration_idx=-1):
        # Note:
        # The output of the LLM is a list of Info. If you are only querying one output, you should access it with [0].
        # It is a good practice to always include 'thinking' in the output.
        return self.query(input_infos, instruction, iteration_idx=iteration_idx)

class AgentArchitecture:
    \"""
    Fill in your code here.
    \"""
    def forward(self, taskInfo) -> Union[Info, str]:
        \"""
        Placeholder method for processing task information.
        
        Args:
        - taskInfo (Info): Task information.
        
        Returns:
        - Answer (Union[Info, str]): Your FINAL Answer. Return either a namedtuple Info or a string of answers.
        \"""
        pass
```
[PAST_AGENTS]

# Agent's fitness value

The fitness value is the median and 95% Bootstrap Confidence Interval of the correct rate on a validation question set. Your GOAL is to maximize the "fitness".

# Output Instruction and Example:
The first key should be ("thought"), and it should capture your thought process for designing the next function. In the "thought" section, first reason about what should be the next interesting agent to try, then describe your reasoning and the overall concept behind the agent design, and finally detail the implementation steps.
The second key ("name") corresponds to the name of your next agent architecture. 
Finally, the last key ("code") corresponds to the exact “forward()” function in Python code that you would like to try. You must write a COMPLETE CODE in "code": Your code will be part of the entire project, so please implement complete, reliable, reusable code snippets.

Here is an example of the output format for the next agent architecture:

[EXAMPLE]

You must use the exact function interface used above. You need to specify the instruction, input information, and the required output fields for various LLM agents to do their specific part of the architecture. 
Also, it could be helpful to set the LLM’s role and temperature to further control the LLM’s response. Note that the LLMAgentBase() will automatically parse the output and return a list of “Infos”. You can get the content by Infos.content. 
DO NOT FORGET the taskInfo input to LLM if you think it is needed, otherwise LLM will not know about the task.

## WRONG Implementation examples:
Here are some mistakes you may make:

1. This is WRONG: ```
feedback, correct = critic_agent([taskInfo, thinking, answer], critic_instruction, i)
feedback_info = verifier_agent([taskInfo, Info('feedback', 'Critic Agent', thinking, 0)], verification_instruction)
```
It is wrong to use "Info('feedback', 'Critic Agent', thinking, 0)". The returned "feedback" from LLMAgentBase is already Info.

2. This is WRONG: ```
# Debugging: Log the generated answer
print('Generated Answer:', ...)
feedback_info = verifier_agent([taskInfo, Info('feedback', 'Critic Agent', thinking, 0)], verification_instruction)
if len(feedback_info) < 3:  # Check if feedback_info has enough elements
    return 'Error: Feedback info incomplete'
```
First, the len(feedback_info) will not work.
Second, you should never return an error message. You should always return the best answer you can get.
Third, you should never print anything in the code.
Lastly, again, DO NOT CREATE Info object by yourself.

3. This is WRONG: ```
all_thinking = []
all_answers = []
for agent, role in zip(agents, roles):
    outputs = agent([taskInfo], independent_reasoning_instruction.format(role=role))
    all_thinking.append(outputs[0].content)
    all_answers.append(outputs[1].content)

# Aggregate the reasoning paths and answers
aggregated_thinking = '\n'.join(all_thinking)
aggregated_answers = '\n'.join(all_answers)
```
You SHOULD NOT extract the content from the Info object by yourself. You should use the Info object directly. If you want to aggregate the content, you should just put those Info objects into a list and then use the list as input to the next LLM agent.

4. This is WRONG: ```
reasoning_agent = LLMAgentBase(['thinking', 'answer'], 'Reasoning Agent')
response_infos = reasoning_agent([taskInfo] + ..., reasoning_instruction)
    
# Extract the final answer from the response_infos
for info in response_infos:
    if info.name == 'final_answer':
        return info
# Fallback if no answer is found
return Info('answer', 'Final Decision Agent', 'No answer generated.', 0)
```
You should not extract the final answer by yourself. You SHOULD directly return the answer Info. Also, you should always return the best answer you can get.
CORRECT example: ```
reasoning_agent = LLMAgentBase(['thinking', 'answer'], 'Reasoning Agent')
thinking, answer = reasoning_agent([taskInfo] + ..., reasoning_instruction)
return answer
```

# Your task
You are deeply familiar with LLM prompting techniques and LLM agent works from the literature.
Your goal is to maximize "fitness" by designing an improved agent that is specifically tailored to the category: [STRUCTURE_LABEL] and [API_LABEL]. You are provided with a selected agent as inspiration: [SELECTED_AGENT].
Your task is to mutate and refine this agent to create a better-performing variant that meets the structure [STRUCTURE_LABEL] and has [API_LABEL]. To achieve this, you will perform two mutations: A structure mutation and an API call mutation.

Observe the discovered architectures carefully and consider the insights, lessons, or stepping stones they provide.
Draw inspiration from related LLM agent papers or academic literature from other research areas. Focus on modifications that can enhance performance while optimizing resource usage in line with the specified category.
THINK OUTSIDE THE BOX.

I. STRUCTURE MUTATION:
Your mutated code must conform exactly to the targeted structure specified by [STRUCTURE_LABEL]. Follow these instructions precisely:

1. Understand the Target Structure:
   - "Linear Chain-of-Thought": A single, straight-line execution with one call to agent() and no loops, branches, or feedback mechanisms.
   - "Iterative Refinement": A loop-based design where the same agent() call is invoked repeatedly (with feedback or modified inputs) to refine the answer.
   - "Tree-of-Thought": A branching architecture where, at key decision points, multiple reasoning paths are generated, and one branch is selected for the final answer.
   - "Decompositional Reasoning": A design that breaks the problem into sub-tasks solved by distinct agent instances (or separate calls), with their results combined to produce the final answer.
   - "Multi-Agent Reasoning": A design that concurrently instantiates two or more unique agent() instances (not reusing the same one in a loop) and coordinates their outputs (e.g., via voting or consensus) to decide the final answer.
   - "Abstraction to Principles Reasoning": A two-phase process where the agent first abstracts the problem into high-level principles and then uses these abstractions to guide the solution.

2. Implementation Guidelines:
Step 1. Incorporate Core Features from the Selected Agent:
   - Analyze the selected agent ([SELECTED_AGENT]) and identify its most impactful reasoning components—those that have contributed significantly to its performance.
   - Prioritize and integrate only these high-performing features into your mutated design, rather than incorporating every minor detail.
   - For instance, if the selected agent employs a particular feedback loop or abstraction mechanism that correlates with high fitness, incorporate that feature while ignoring less impactful elements.
Step 2. Perform the structure mutation:
   - Modify the control flow to reflect the target structure. For example, if [STRUCTURE_LABEL] is "Iterative Refinement", introduce a clear loop that repeatedly calls the agent() method with updated inputs.
   - Ensure that agent instantiation patterns match the target:
       * For "Multi-Agent Reasoning", instantiate at least two unique LLMAgentBase objects (do not simply reuse one inside a loop).
       * For "Linear Chain-of-Thought", ensure there is only a single agent() call without any loops or branches.
       * For "Tree-of-Thought", incorporate conditional branches or multiple calls that represent divergent reasoning paths, followed by a selection step.
       * For "Decompositional Reasoning", structure the code to split the problem first into independent, smaller sub-tasks that are then in a second step solved independently (possibly by different agent instances), before then combining their outputs in a third step.
       * For "Abstraction to Principles Reasoning", structure the code into two phases: first, extract and process high-level principles; then, use these principles to generate the final answer.

3. Self-Review:
   - Before finalizing your mutated code, carefully review the overall control flow and agent instantiation pattern to ensure it matches the target structure [STRUCTURE_LABEL].

4. Example Structure Mutation Strategies:
▸ From Linear → Multi-Agent: Split monolithic calls into specialized agents  
▸ From Multi → Iterative: Add feedback gathering between rounds  
▸ From Iterative → Tree: Convert loop into conditional branches  
▸ From Abstraction → Tree: Create principle-specific reasoning paths 

II. API CALL MUTATION:
Follow these instructions precisely:

1. Stay within Target API Calls:
Your mutated code must meet the targeted API call count specified by [API_LABEL].
   - If [API_LABEL] is "few API calls", your final code must include between 1 and 5 calls to agent().
   - If [API_LABEL] is "many API calls", your final code must include more than 5 calls to agent().

2. Counting Rules:
   - Only count invocations of the agent() method (do NOT count LLMAgentBase instantiations).
   - Count every agent() call, regardless of its location (inside loops, conditionals, etc.).
   - Include concise inline comments indicating the number of calls per code block (e.g., "Loop: 3 iterations x 1 call = 3 calls").

3. Self-Review:
   - Before finalizing your code, carefully review it to ensure that the total number of agent() calls falls exactly within the required range.
   - If the agent does not meet the specified number of API calls, reiterate on the agent's code to achieve the required API calls.

4. Examples of API call mutations:
========= Mutation to Few API Call Category =================
# Original Agent (2 calls)
def forward():
    agent1 = LLMAgentBase()
    result1 = agent1()  # 1 call
    result2 = agent1()  # 1 call (Total: 2)

# Mutated Agent (4 calls - "Few API" compliant)
def forward():
    agent1 = LLMAgentBase()
    # Initial analysis phase
    for _ in range(2):  # 2 iterations × 1 call = 2 calls
        agent1()  
    
    # Final refinement
    inputs = [taskInfo, previous_results]
    agent1(inputs)  # 1 call
    
    # Validation step
    if needs_correction:  # Always True path
        agent1()  # 1 call (Total: 2+1+1=4)
========= Mutation to Many API Call Category =================
# Original Agent (3 calls)
def forward():
    agents = [LLMAgentBase() for _ in range(3)]
    for a in agents:
        a()  # 3 calls

# Mutated Agent (7 calls - "Many API" compliant)
def forward():
    # Parallel agent pool
    agents = [LLMAgentBase() for _ in range(3)]  # 0 calls (instantiation)
    
    # First debate round
    for a in agents:  # 3 iterations × 1 call = 3
        a()  
    
    # Second refinement round 
    for i in range(2):  # 2 iterations × 2 agents = 4
        for a in agents[:2]:  
            a()  # (Total: 3+4=7)

III. FITNESS MAXIMIZATION IMPROVEMENT:
Your final solution must not only meet the target structure and API call constraints but also achieve the highest possible performance (fitness) on the benchmark. To maximize fitness, you must:
   - Critically analyze the entire reasoning chain and computational steps to ensure they produce accurate, meaningful, and non-zero results.
   - Optimize key computations by streamlining feedback loops, refining arithmetic operations, and eliminating redundant data manipulations to reduce noise and enhance accuracy.
   - Adjust prompt phrasing, LLM roles, temperature settings, and hyperparameters to encourage deeper, more robust reasoning.
   - Prioritize and incorporate only high-impact features from the selected agent ([SELECTED_AGENT]); evaluate each inherited component for its contribution to fitness and discard minor or redundant elements.
   - Compare your mutated solution against high-performing benchmarks or baseline performance metrics, iterating until the performance is significantly improved.
   - Validate your design using simulated test cases to ensure that the logic effectively solves the benchmark.
   - Eliminate any default or constant outputs that do not represent genuine computation.

IV. CODE QUALITY ASSURANCE:
Your final mutated code must:
   - Be syntactically correct and runnable without errors.
   - Produce meaningful outputs (non-zero accuracy) rather than returning a constant or zero value.
   - Pass a self-review of code quality: double-check for potential syntax issues, logical errors, and ensure that all required functions execute as intended.
   - Data Type and Functional Correctness: Ensure that all variables and operations use the correct data types and that arithmetic and data structure manipulations are valid. Verify that your code’s evaluation produces realistic, non-zero values.
   - Focus on delivering a robust solution that not only meets the target structure and API call constraints but also avoids coding errors leading to 0 accuracy.

V. EVALUATION ASSURANCE:
Before finalizing your mutated code, ensure that the agent actually performs a computation to solve the benchmark:
   - Analyze the logic to confirm that the code processes the input taskInfo and produces a meaningful result.
   - Check that the code does not simply return a default value (e.g., 0 or constant) or an empty result.
   - Internally verify that all computations, data manipulations, and output assignments are correct and yield non-zero, plausible values.
   - Ensure that the solution would effectively solve the intended benchmark rather than just meeting structural or API constraints.

VI. OUTPUT FORMAT ENFORCEMENT:
Your final mutated code must:
   - Use the exact function interface specified.
   - Include the required instruction, input information, and output fields for the LLM agents.
   - Ensure the output format exactly matches the following example:
   
[EXAMPLE]

   - Set the LLM’s role and temperature as needed.
   - DO NOT FORGET the taskInfo input when calling the agent.

IMPORTANT RULES:
[RULES]
These rules MUST be followed strictly. Any solution that violates these rules will be rejected.

"""

Reflexion_prompt_1 = f""""[EXAMPLE]Carefully review the proposed new architecture and reflect on the following points:"

Before providing your solution, you MUST verify:
1. Does your implementation follow this critical rule?:
Look through the code again independently. You have to detect if the code breaks the rules. REMEMBER the rules are as follows:
[RULES]

2. **Interestingness**: Assess whether your proposed architecture is interesting or innovative compared to existing methods in the archive. If you determine that the proposed architecture is not interesting, suggest a new architecture that addresses these shortcomings. 
- Make sure to check the difference between the proposed architecture and previous attempts.
- Compare the proposal and the architectures in the archive CAREFULLY, including their actual differences in the implementation.
- Decide whether the current architecture is innovative.
- USE CRITICAL THINKING!

3. **Implementation Mistakes**:
Identify any mistakes you may have made in the implementation. Review the code carefully, debug any issues you find, and provide a corrected version. REMEMBER checking "## WRONG Implementation examples" in the prompt.
REMEMBER checking "## WRONG Implementation examples" in the prompt. MAKE SURE TO FOLLOW THE RULES STRICTLY: [RULES]

4. **Improvement**: Based on the proposed architecture, suggest improvements in the detailed implementation that could increase its performance or effectiveness. In this step, focus on refining and optimizing the existing implementation without altering the overall design framework, except if you want to propose a different architecture if the current is not interesting.
- Observe carefully about whether the implementation is actually doing what it is supposed to do.
- Check if there is redundant code or unnecessary steps in the implementation. Replace them with effective implementation.
- Try to avoid the implementation being too similar to the previous agent.

And then, you need to improve or revise the implementation, or implement the new proposed architecture based on the reflection.

Your response should be organized as follows:

"rule_verification": Explain the rules you must follow, and explain how you verified rule compliance.

"reflection": Provide your thoughts on the interestingness of the architecture, identify any mistakes in the implementation, and suggest improvements.

"thought": Revise your previous proposal or propose a new architecture if necessary, using the same format as the example response.

"name": Provide a name for the revised or new architecture. (Don't put words like "new" or "improved" in the name.)

"code": Provide the corrected code or an improved implementation. Make sure you actually implement your fix and improvement in this code.
"""


Reflexion_prompt_2 = """Using the tips in "## WRONG Implementation examples" section, revise the code further.
Make sure to follow the rules strictly: [RULES]
Your response should be organized as follows:
Put your new reflection thinking in "reflection". Repeat the previous "thought" and "name", and update the corrected version of the code in "code".
"""

RULES = lambda api_threshold: (
    "RULE: In the forward() function, every single occurrence of LLMAgentBase(...)(...) counts as one usage. "
    "This means that if you call an LLMAgentBase instance more than once—even if it's the same instance—each call is counted separately. "
    f"The total number of such calls must not exceed {api_threshold}. "
    "This includes calls made inside loops, conditionals, or any nested structures. "
    "No exceptions: every call is counted individually. "
    "Strict adherence to this rule is mandatory."
)


def get_init_archive():
    return [COT, COT_SC, Reflexion, LLM_debate, Take_a_step_back, QD, Role_Assignment]


def get_prompt(current_archive, current_map, past_agent_parameter, selected_agent=None, structure_label=None, api_label=None, adaptive=False):
    # Convert the archive to a JSON string
    archive_str = ",\n".join([json.dumps(sol) for sol in current_archive])
    archive_str = f"[{archive_str}]"

    # Convert the map to a JSON string
    map_str = ",\n".join([json.dumps(sol) for sol in current_map])
    map_str = f"[{map_str}]"

    # Replace [EXAMPLE]
    prompt = base.replace("[EXAMPLE]", json.dumps(EXAMPLE))

    # Include past agents based on past_agent_parameter
    if past_agent_parameter == "MAP":
        template_str = """# Discovered Architectures 
Below are the discovered architectures:
 
[MAP_ELITES]"""
        prompt = prompt.replace("[PAST_AGENTS]", template_str)
        prompt = prompt.replace("[MAP_ELITES]", json.dumps(map_str))
    
    elif past_agent_parameter == "Archive":
        template_str = """# Discovered Architectures 
Below are the discovered architectures:
 
[ARCHIVE]"""
        prompt = prompt.replace("[PAST_AGENTS]", template_str)
        prompt = prompt.replace("[ARCHIVE]", json.dumps(archive_str))
    
    else:
        template_str = """# Selected Agent
Below is the architecture of the selected agent:
 
[SELECTED_AGENT]"""
        prompt = prompt.replace("[PAST_AGENTS]", template_str)

    # Generate rules for API calls
    rules = RULES(api_label if api_label is not None else "few API calls")
    prompt = prompt.replace("[RULES]", rules)
    
    # Add in mutation direction
    if structure_label is not None:
        prompt = prompt.replace("[STRUCTURE_LABEL]", structure_label)
    else:
        prompt = prompt.replace("[STRUCTURE_LABEL]", "")
    
    if api_label is not None:
        prompt = prompt.replace("[API_LABEL]", api_label)
    else:
        prompt = prompt.replace("[API_LABEL]", "")
    
    # Replace [LABEL DESCRIPTION] with corresponding description based on structure_label
    label_descriptions = {
        "Linear Chain-of-Thought": "The agent produces its final answer in a single, linear chain-of-thought without any iterative self-refinement or use of multiple agents.",
        "Iterative Refinement": "The agent continually repcrosses its chain-of-thought, revising, re-evaluating, and self-assessing its intermediate steps - to progressively converge on a robust final answer.",
        "Tree-of-Thought": "The agent creates a tree-of-thought by dynamically branches out at key decision points, exploring multiple reasoning paths and selectively following the most promising branch to arrive at the final answer.",
        "Decompositional Reasoning": "The agent breaks down a complex problem into independent sub-problems, solves each one separately, and then integrates these solutions into a cohesive final answer.",
        "Multi-Agent Reasoning": "The agent concurrently creates several LLM instances that interact with one another and create different reasoning trajectories. The agent aggreates the outcome from the different LLM instances - such as through voting or consensus - to produce the final decision. Common mistake: A single agent generating multiple responses  is NOT multi-agent reasoning. Multi-agent reasoning requires multiple LLMAgentBase instances with coordination.",
        "Abstraction to Principles Reasoning": "First abstracts the problem’s details into high-level principles, then uses these abstractions to guide the solution."
    }

    label_description = label_descriptions.get(structure_label, "")
    prompt = prompt.replace("[LABEL DESCRIPTION]", label_description)
    
    # Add in selected agent
    if selected_agent is not None:
        prompt = prompt.replace("[SELECTED_AGENT]", json.dumps(selected_agent))
    else:
        prompt = prompt.replace("[SELECTED_AGENT]", "")
    
    return system_prompt, prompt



def get_reflexion_prompt(prev_example, structure_label=None, api_label=None):
    prev_example_str = "Here is the previous agent you tried:\n" + json.dumps(prev_example) + "\n\n"
    r1 = (Reflexion_prompt_1.replace("[EXAMPLE]", prev_example_str)
          if prev_example else Reflexion_prompt_1.replace("[EXAMPLE]", ""))
    
    # Generate rules
    rules = RULES(api_label if api_label is not None else "")
    r1 = r1.replace("[RULES]", rules)
    
    reflexion_prompt_2 = """Using the tips in "## WRONG Implementation examples" section, revise the code further.
    Make sure to follow the rules strictly: [RULES]
    Your response should be organized as follows:
    Put your new reflection thinking in "reflection". Repeat the previous "thought" and "name", and update the corrected version of the code in "code".
    """
    reflexion_prompt_2 = reflexion_prompt_2.replace("[RULES]", rules)
    
    return r1, reflexion_prompt_2

