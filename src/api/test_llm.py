import asyncio
from app.services.llm import LLMService

async def test_classify_intent():
    """test the classify_intent method with various inputs"""
    llm_service = LLMService()
    
    test_cases = [
        ("go north", "move"),
        ("move east", "move"),
        ("head south", "move"),
        ("walk west", "move"),
        ("look around", "look"),
        ("examine the room", "look"),
        ("take sword", "take"),
        ("pick up the potion", "take"),
        ("grab key", "take"),
        ("attack goblin", "attack"),
        ("fight the orc", "attack"),
        ("check inventory", "inventory"),
        ("what do I have", "inventory"),
        ("dance a jig", "unknown"),
    ]
    
    print("\n" + "="*60)
    print("Testing Intent Classification")
    print("="*60 + "\n")
    
    for user_input, expected_action in test_cases:
        print(f"Input: '{user_input}'")
        print(f"Expected action: {expected_action}")
        
        try:
            result = await llm_service.classify_intent(user_input)
            actual_action = result.get("action", "unknown")
            
            print(f"Result: {result}")
            
            status = "✓ PASS" if actual_action == expected_action else "✗ FAIL"
            print(f"Status: {status}")
            
            # additional info for debugging
            if actual_action != expected_action:
                print(f"  Expected: {expected_action}")
                print(f"  Got: {actual_action}")
                
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 60 + "\n")

async def test_tool_binding():
    """verify that tools are properly bound to the agent"""
    llm_service = LLMService()
    
    print("\n" + "="*60)
    print("Testing Tool Binding")
    print("="*60 + "\n")
    
    print(f"Number of action tools: {len(llm_service.action_tools)}")
    print("Tool names:")
    for tool in llm_service.action_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # check if classify_agent has tools bound
    print(f"\nClassify agent type: {type(llm_service.classify_agent)}")
    print(f"Classify agent model: {llm_service.classify_agent_llm.model}")
    
    # try to see if tools are bound
    if hasattr(llm_service.classify_agent, 'bound_tools'):
        print(f"Bound tools: {llm_service.classify_agent_llm}")
    else:
        print("Warning: classify_agent doesn't have 'bound_tools' attribute")

async def test_raw_response():
    """test what the raw llm response looks like"""
    llm_service = LLMService()
    
    print("\n" + "="*60)
    print("Testing Raw LLM Response")
    print("="*60 + "\n")
    
    test_input = "go north"
    prompt = f"""Analyze the player's input and call the appropriate action tool.

Player input: "{test_input}"

Use the available tools to classify the intent:
- action_move: if they want to go somewhere (extract the direction)
- action_look: if they want to examine surroundings
- action_take: if they want to pick up an item (extract the item name)
- action_attack: if they want to fight something (extract the target name)
- action_inventory: if they want to check their items
- action_unknown: if none of the above apply

Call the most appropriate tool based on the player's intent."""
    
    print(f"Sending prompt for: '{test_input}'\n")
    
    try:
        response = await llm_service.classify_agent.ainvoke(prompt)
        
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        print(f"\nResponse attributes: {dir(response)}")
        
        if hasattr(response, 'content'):
            print(f"\nContent: {response.content}")
        
        if hasattr(response, 'tool_calls'):
            print(f"\nTool calls: {response.tool_calls}")
            print(f"Tool calls type: {type(response.tool_calls)}")
            print(f"Tool calls length: {len(response.tool_calls) if response.tool_calls else 0}")
        
        if hasattr(response, 'additional_kwargs'):
            print(f"\nAdditional kwargs: {response.additional_kwargs}")
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🧪 LLM Service Test Suite\n")
    
    asyncio.run(test_tool_binding())
    asyncio.run(test_raw_response())
    asyncio.run(test_classify_intent())
