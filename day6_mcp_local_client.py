import ollama
import requests
import json

MCP_URL = "http://localhost:8000/mcp"

def get_mcp_tools():
    """Dynamic: Fetch ALL tools from MCP server."""
    resp = requests.get(f"{MCP_URL}/tools")  
    if resp.ok:
        tools = resp.json()
        print("Discovered tools:", [t['name'] for t in tools])
        return tools
    return []

def call_tool(tool_name, args):
    resp = requests.post(f"{MCP_URL}/tools/{tool_name}", json=args)
    return resp.json() if resp.ok else {"error": "Tool failed"}

tools_schemas = get_mcp_tools() 
print(tools_schemas) 

def dynamic_agent(query):
    ollama_tools = []
    for tool in tools_schemas:
        ollama_tools.append({
            'type': 'function',
            'function': {
                'name': tool['name'],
                'description': tool.get('description', ''),
                'parameters': tool['inputSchema']
            }
        })
    
    response = ollama.chat(
        model='qwen2.5:7b-instruct-q4_0',
        messages=[{'role': 'user', 'content': query}],
        tools=ollama_tools  
    )
    msg = response['message']
    if 'tool_calls' in msg:
        for tc in msg['tool_calls']:
            name = tc['function']['name']
            args = tc['function']['arguments']
            result = call_tool(name, args)
            print(f"✅ {name}: {result}")
            
            # LLM summarizes
            final = ollama.chat(model='qwen2.5:7b-instruct-q4_0', messages=[
                {'role': 'user', 'content': query + f"\nTool result: {json.dumps(result)}"}
            ])
            return final['message']['content']
    return msg['content']

print(dynamic_agent("20L loan 8.5% 20yrs interest?"))
