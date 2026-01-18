# AgenticAI-A2A for Trip-Planning
An Agentic-AI framework with ADK-A2A and MCP for trip planning. This is an agentic AI system 
capable to search for accommodation, check the weather and propose sightseeing 
in a particular destination. 




Part of the code and ideas can be found [here](https://github.com/a2aproject/a2a-samples/tree/main/samples/python/agents/airbnb_planner_multiagent). 
However, original code has been modified to make it work in scenarios where users have multiple queries, 
where each query requires access to different remote agents. 
The proposed Agentic AI system has been enhanced with an additional agent 
that performs Google search to identify and propose venues to visit and activities to do in a city.

![alt text](assets/trip_agent.png)


![alt_text](assets/trip_agent_ui.png)



## Setup and Deployment
___

Before running the app locally, ensure you have the following:

1. Node.js: Required to run the MCP server
2. uv: The python package management tool. To create a virtual environment and 
   install all listed dependencies, run:
   ```shell
   uv install
   ```
3. python 3.13 is required to run a2a-sdk
4. set up .env
 * Create an `.env` file in airbnb_agents, weather_agents and search_agents with the following content:
 ```shell
GOOGLE_API_KEY="your_api_key_here" 
```

 * Create `.env` file in `host_agent/` folder with the following content:
 ```shell
 GOOGLE_API_KEY="your-api-key"

 GOOGLE_GENAI_MODEL="gemini-2.5-flash"
 GOOGLE_GENAI_USE_VERTEXAI=FALSE
 GOOGLE_CLOUD_LOCATION="global"
```

## 1. Run Airbnb Agent
___

```shell
cd src/airbnb_agent
uv run main.py
```


## 2. Run Weather Agent
___

```shell
cd src/weather_agent
uv run main.py
```

## 3. Run Search Agent
___

```shell
cd src/search_agent
uv run main.py
```

## 4. Run Host Agent
___

```shell
cd src/airbnb_agent
uv run main.py
```

### 5. Access and Test the agentic solution on the UI
___

```shell
http://localhost:8083/
```


## How SDK and A2A Operate
___
A good explanation on how A2A protocol works can be found [here](https://huggingface.co/blog/1bo/a2a-protocol-explained). 

In short, A2A is a open-source framework launched by Google to facilitate communication and interoperability among agents. 
It provides a standardized collaboration method for agents, regardless of their frameworks or vendors, this protocol 
enables AI agents to securely exchange information, coordintate actions, and operate across diverse applications.


### Why A2A is Needed

As AI agents become increasingly specialized, the need to collaborate on complex tasks grows. Imagine, a user trying 
to plan an international trip. As we show in this repo, this request might involve coordinating the capabilities of 
several specialized agents:

1. An Agent for airbnb reservations
2. An Agent for local tour recommendations
3. A weather agent and so on...


### Application Scenarios
___

#### Enterprise Automation
Also, A2A enable agents to work across siloed data systems and applications. For example, a supply chain planning agent can 
coordinate with inventory management, logistics and so ...

#### Cross-Platform Integration
For business applications, A2A allows AI agents to operate across an entire ecosystem of Enteprise applications. 
This means that agents can access and coordinate with other agents on various platforms, such as knowledge bases, 
project management tools and more.



### How it Works

A2A facilitates communication between "client" agents and "remote" agents. The client agent is responsible for 
formulating and conveying tasks, while the remote agent executes them. This interaction involves several key functions:

* **Capability Discovery:** Agents can expose their capabilities using a JSON-formatted `Agent Card`. 
  This allows client agents to identify the most suitable agent for a task and communicate with remote agents via A2A 


* **Task Management:** Communication between client and remote agents is task-oriented. The `Task` object, defined by the 
protocol, has a lifecycle. The output of a task is called an `Artifact`

* **Collaboration:** Agent can exchange messages to share context, responses, artifacts, or user instructions. 

* **Negotiation:** Each message includes a `parts` field, which contains fully formed content fragments such as 
  generated text or images. Each part has a specified content type, allowing client and remote agents to negotiate the
  correct format.
  
### Participants

___

First, we need to clarify the participants in the A2A protocol:

* **User:** The end user initiating a request or a goal that requires assistance from an agent

* **A2A Client (Client Agent):** An app, service or other AI agent that represents the user in requesting actions. The
client initiates communication using the A2A protocol.

* **A2A Server (Remote Agent):** An AI agent that exposes an HTTP endpoint implementing the A2A protocol. 


### Communication Elements

___
#### Agent Card

* A JSON metadata document, typically discoverable via the URL `/.well-known/agent.json`

* It details the agent's identity (name, description)

* Client uses the agent card to discover the agent 


#### Task

* When a client sends a message to an agent, the agent may detrmine that fulfilling the 
request requires completing a task
  
* Each task has a unique ID assigned be the agent and progresses through a defined lifecycle (e.g., 
  `submitted`, `working`, `input-required`, `completed`, `failed`). 

* Tasks are stateful and may involve multiple exchanges.

#### Message

* Represents a single turn or unit of communication between the client and the agent.

* A message has a `role` (messages sent by the client are labelled `user`, while those sent by the 
  server are labeled `agent`) and contains on or more `Part` objects that carry the actual content.
  The `messageID` field is a unique identifier set by the sender for each message.
  

#### Part

The fundamental content unit within a message or `Artifact`. Each part has a specific `type` and 
carry different kinds of data:

* `TextPart`: Contains plain text content
* `FilePart`: Represent a file
* `DataPArt`: Carries structured JSON data, suitable for forms, parameters


#### Artifact

* Represents the output results generated by the remote agent during task processing

* An `Artifact` consists of one or more `Part` objects and can be streamed incrementally. 


#### Artifact

* Used to convey instructions, context, questions, 



## The Trip Planning Agent

___

When we start our host agent, it reads the cards of the remote agents. For example, the Airbnb agent:

```python
INFO:a2a.client.card_resolver: Successfully fetched agent card data from
http://localhost:10002/.well-known/agent-card.json: 
{'capabilities': {'pushNotifications': True, 'streaming': True}, 
 'defaultInputModes': ['text', 'text/plain'], 
 'defaultOutputModes': ['text', 'text/plain'], 
 'description': 'Helps with searching accommodation', 
 'name': 'Airbnb Agent', 
 'preferredTransport': 'JSONRPC', 'protocolVersion': '0.3.0', 
 'skills': [{'description': 'Helps with accommodation search using airbnb', 
             'examples': ['Please find a room in LA, CA, April 15, 2025, checkout date is april 18, 2 adults'], 
             'id': 'airbnb_search', 'name': 'Search airbnb accommodation', 
             'tags': ['airbnb accommodation']}], 'url': 'http://0.0.0.0:10002', 'version': '1.0.0'}
```

We provide a question that requires the use of two different agent to generate an answer:

**Question**:`provide a list of airbnb accommodations in France, Paris. Check-in Date: 3 February 2026 and check-out day: 8 Feb 2026. Also, make some suggestion on exhibitions worth visiting there?`


The host agent breaks the question into two Parts:

* **Airbnb Agent Part**
  ```shell
  Part(
      function_call=FunctionCall(
        args={
          'agent_name': 'Airbnb Agent',
          'task': 'Provide a list of airbnb accommodations in France, Paris. Check-in Date: 3 February 2026 and check-out day: 8 Feb 2026.'
        },
        id='adk-6c66c046-54c5-4f40-97f8-0af885ed3527',
        name='send_message'
      ),
  )
  ```

* **Google Search Agent Part**

  ```shell
  Part(
      function_call=FunctionCall(
        args={
          'agent_name': 'Search Agent',
          'task': 'Suggest exhibitions worth visiting in Paris in February 2026.'
       },
       id='adk-febcd5a8-ccc6-4388-8a19-fab8a2189cbe',
       name='send_message'
      )
  )

  ```