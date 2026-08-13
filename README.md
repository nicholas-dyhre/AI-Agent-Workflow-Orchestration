### Purpose

This project is a proof of concept created to gain experience and insight into multi-agent collaboration, information parsing, automated workflows, tool execution, and skill discovery, and agent work cycles. **It is not intended for production use**. 

---

### AI Orchestrator

The AI Orchestrator is a flexible framework designed to coordinate the execution of AI skills and tools, with a primary focus on running local autonomous agents. It also features experimental support for remote agents. 

Built using Python and Pydantic, the orchestrator provides a Command Line Interface (CLI) for user input. It is designed specifically for developers looking to build, test, and expand AI applications that interact with local development environments. 

---

### Setup & Usage

#### 1. Installation

Clone the repository, navigate to the project directory, and install the required dependencies:

`pip install -r ./requirements.txt`

#### 2. Running the Orchestrator

Execute the main script by providing your project location and an initial prompt:

`python main.py --project_location /path/to/project --prompt "Hello world"`

#### 3. Configuring and Changing Agents

To change the LLM provider or model for specific agent roles, update the agent definitions inside main.py.First, instantiate a new LLM object with your desired configuration:

```python
my_LLM = LLM(
    LLMProvider.OLLAMA | LLMProvider.OPENAI | LLMProvider.LOCAL,
    "MODEL_NAME",
    isStream=True,
    endpoint="PROVIDER_URL",
    cache=LLMCache(),
)
```

Then, assign the new LLM instance to the desired agent role within the orchestration mapping:

```python

agents = {
    AgentName.DEVELOPER: DeveloperAgent(
        llm=my_LLM,
        tool_selector=toolSelector,
        skill_selector=skillSelector,
    ),
    AgentName.PROJECT_PLANNER: ProjectPlannerAgent(
        llm=my_other_LLM,
        tool_selector=toolSelector,
        skill_selector=skillSelector,
    ),
}
```

> **NOTE:** While LLMProvider.OPENAI is listed as an option, API key authentication is not currently implemented.

---

### Installation

Clone the repository, navigate to the project directory, and install the required dependencies: 

bash

pip install -r ./requirements.txt

Use code with caution.

### Running the Orchestrator

Execute the main script by providing your project location and an initial prompt: 

bash

python main.py --project_location /path/to/project --prompt "Hello world"

Use code with caution.

---

### Core Capabilities

- **Multi-Agent Workflow Orchestration:** State-machine-driven agent handoffs.
- **Task Management:** File-system-based tracking using structured JSON.
- **Hierarchical Skill System:** Tree-structured skill discovery to minimize context bloat.
- **Extensible Tool System:** Custom tool abstractions with automatic parameter injection.
- **LLM Caching:** Token-saving cache with an integrated execution circuit breaker.

---

### Architecture & Systems

### 1. Multi-Agent Workflow Orchestration

The orchestration engine uses a finite state machine to map task states to specific agent roles. The default workflow follows a structured development pipeline: 

Project Planner ⟶ Planner ⟶ Developer ⟶ Reviewer

 

- **Project Planner:** Breaks the user's high-level prompt down into granular tasks (similar to Scrum features) and saves them as files in the project path.
- **Planner:** Breaks individual tasks down into actionable "plan steps" (similar to Scrum user stories) and appends them to the active task.
- **Developer:** Acts as the software engineer. It reads the plan steps sequentially and writes code until all steps within a task are complete.
- **Reviewer:** Evaluates the implementation by reading Git diffs and comparing them against the task description. It executes the code and tests to ensure functionality, and can reject tasks—sending them back to the Developer if issues are found.

### 2. Task Management

Agents use structured tasks to parse information and persist their work. Every task is stored locally as an independent, readable JSON file. 

### 3. Hierarchical Skill System

To maximize efficiency and reduce LLM context window bloat, skills are organized in a tree structure. Agents use a discovery tool to navigate branches by name or keyword. 

Instead of dumping every available skill into the system prompt, the agent only loads the specific branch relevant to its immediate task. This drastically reduces context bloat and keeps the agent focused. 

### 4. Extensible Tool System

Agents invoke custom tools using specific input parameters. The system leverages abstractions and reflection, meaning the orchestrator automatically detects new tools and injects their schemas into agent prompts. 

Additionally, the system features **parameter injection** to automatically fill in environmental variables, reducing the amount of boilerplate data an agent needs to generate to trigger Git, file system, or code execution actions. 

### 5. LLM Cache & Circuit Breaker

The system caches full LLM prompts and responses to serve two primary functions: 

- **Debugging:** Easily review exact inputs and outputs.
- **Cost & Speed Optimization:** Detect and skip duplicate prompts.

_Note on Known Limitations:_ To prevent infinite agent loops where identical prompts are generated consecutively, an integrated **circuit breaker** will automatically terminate the program if too many consecutive cache hits are detected.
