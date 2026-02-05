from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain.messages import AIMessage
from app.core.config import settings

class LLMService:
	generate_text_agent = ChatOllama(
		model=settings.OLLAMA_GEN_MODEL,
		temperature=settings.AGENT_TEMPERATURE,
		base_url=settings.OLLAMA_BASE_URL,
	)
	
	classify_agent_llm = ChatOllama(
		model=settings.OLLAMA_CLASSIFY_MODEL,
		temperature=settings.AGENT_TEMPERATURE,
		base_url=settings.OLLAMA_BASE_URL,
	)

	def __init__(self):
		# action tools for the classify subagent
		self.action_tools = [
			self.action_move,
			self.action_look,
			self.action_take,
			self.action_attack,
			self.action_inventory,
			self.action_unknown,
		]
		
		# bind action tools to classify subagent (bind_tools returns a new instance)
		self.classify_agent = self.classify_agent_llm.bind_tools(self.action_tools)

	@tool
	def action_move(self, direction: str) -> dict:
		"""player wants to move in a direction. call this when the user wants to go north, south, east, or west."""
		return {"action": "move", "direction": direction.lower()}

	@tool
	def action_look(self) -> dict:
		"""player wants to examine their surroundings or look around the current room."""
		return {"action": "look"}

	@tool
	def action_take(self, item_name: str) -> dict:
		"""player wants to pick up or take an item. call this when the user wants to grab, get, or collect something."""
		return {"action": "take", "target": item_name}

	@tool
	def action_attack(self, target_name: str) -> dict:
		"""player wants to attack, fight, or engage in combat with an enemy or creature."""
		return {"action": "attack", "target": target_name}

	@tool
	def action_inventory(self) -> dict:
		"""player wants to check their inventory, items, or belongings."""
		return {"action": "inventory"}

	@tool
	def action_unknown(self) -> dict:
		"""call this when the player's intent doesn't match any known game action."""
		return {"action": "unknown"}

	async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
		"""
		generate narrative text using the llm.
		optionally accepts a system prompt to guide the generation.
		"""
		from langchain_core.messages import SystemMessage, HumanMessage
		
		# build message list with optional system prompt
		messages = []
		if system_prompt:
			messages.append(SystemMessage(content=system_prompt))
		messages.append(HumanMessage(content=prompt))
		
		# invoke the llm and return the generated text
		response = await self.generate_text_agent.ainvoke(messages)
		
		# ensure we return a string
		if isinstance(response.content, str):
			return response.content
		elif isinstance(response.content, list):
			# concatenate list items into a single string
			return " ".join(str(item) for item in response.content)
		else:
			return str(response.content)

	async def classify_intent(self, user_input: str) -> dict:
		"""
		classify user input into game actions using a subagent with action tools.
		returns a dict with 'action' and optional 'direction' or 'target' keys.
		
		supported actions:
		- move: moving in a direction (north, south, east, west)
		- look: examining the current room
		- take: picking up an item
		- attack: attacking an enemy
		- inventory: checking inventory
		- unknown: unrecognized action
		"""
		prompt = f"""Analyze the player's input and call the appropriate action tool.

Player input: "{user_input}"

Use the available tools to classify the intent:
- action_move: if they want to go somewhere (extract the direction)
- action_look: if they want to examine surroundings
- action_take: if they want to pick up an item (extract the item name)
- action_attack: if they want to fight something (extract the target name)
- action_inventory: if they want to check their items
- action_unknown: if none of the above apply

Call the most appropriate tool based on the player's intent."""

		response = await self.classify_agent.ainvoke(prompt)
		
		# extract tool call from response
		if hasattr(response, 'tool_calls') and response.tool_calls:
			tool_call = response.tool_calls[0]
			tool_name = tool_call['name']
			tool_args = tool_call.get('args', {})
			
			# execute the tool to get the result
			for action_tool in self.action_tools:
				if action_tool.name == tool_name:
					result = action_tool.invoke(tool_args)
					print(f"Classified intent: {result}")
					return result
		
		# fallback if no tool was called
		return {"action": "unknown"}