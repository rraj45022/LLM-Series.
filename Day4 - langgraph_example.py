from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq  # Or ChatOpenAI
from langgraph.graph.message import add_messages
import os
import dotenv
dotenv.load_dotenv()
os.environ.get("GROQ_API_KEY")

class ErrorFixState(TypedDict):
    error: str  # "yes" or "no"
    error_reason: str  # Detailed error message
    fixed_code: str  # Corrected code
    messages: Annotated[list[BaseMessage], add_messages]
    iterations: int
    visited_nodes: Annotated[list[str], "operator.add"]  # Tracks path [web:67]



llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)  # Your pref

# Explain chain: Converts dict to messages
explain_prompt = ChatPromptTemplate.from_messages([
    ("system", "Analyze error briefly (under 30 words). Be precise."),
    ("human", "{error_reason}"),
    MessagesPlaceholder(variable_name="messages")
])
explain_chain = explain_prompt | llm | StrOutputParser()

def explain_error(state):
    explanation = explain_chain.invoke({
        "error_reason": state["error_reason"],
        "messages": state["messages"]
    })
    return {
        "messages": state["messages"] + [{"role": "assistant", "content": explanation}],
        "iterations": state["iterations"],
        "visited_nodes": state["visited_nodes"] + ["explain_error"]
    }

# Fix chain
fix_prompt = ChatPromptTemplate.from_messages([
    ("system", """Fix code. Output ONLY runnable Python code—no explanation, no ``` marks, no extra text.

Example output:
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)"""),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Previous code:\n{old_code}")
])

fix_chain = fix_prompt | llm | StrOutputParser()

def fix_code(state):
    fixed = fix_chain.invoke({
        "messages": state["messages"],
        "old_code": state.get("fixed_code", "")
    })
    return {
        "fixed_code": fixed,
        "messages": state["messages"] + [{"role": "assistant", "content": f"Fixed code:\n{fixed}"}],
        "iterations": state["iterations"],
        "visited_nodes": state["visited_nodes"] + ["fix_code"]
    }

# Execute unchanged, but add message
def execute_code(state):
    try:
        exec(state["fixed_code"])
        return {"error": "no", "messages": state["messages"] + [{"role": "system", "content": "Success!"}],
                "visited_nodes": state["visited_nodes"] + ["execute_code"]
}
    except Exception as e:
        error_msg = f"Execution failed: {str(e)}"
        return {
            "error": "yes",
            "error_reason": error_msg,
            "messages": state["messages"] + [{"role": "system", "content": error_msg}],
            "visited_nodes": state["visited_nodes"] + ["execute_code"]
        } 


def should_retry(state: ErrorFixState) -> str:
    if state["error"] == "no" or state["iterations"] >= 1:
        return END
    state["iterations"] += 1  # Increment here
    return "explain_error"


from langgraph.graph import StateGraph, START, END

graph = StateGraph(ErrorFixState)
graph.add_node("explain_error", explain_error)
graph.add_node("fix_code", fix_code)
graph.add_node("execute_code", execute_code)
graph.add_node("should_retry", should_retry)
graph.add_edge(START, "explain_error")
graph.add_edge("explain_error", "fix_code")
graph.add_edge("fix_code", "execute_code")
graph.add_edge("execute_code", END)
graph.add_conditional_edges("execute_code", should_retry, {"explain_error": "explain_error", END: END})

app = graph.compile()

result = app.invoke({
    "error": "yes",
    "error_reason": "SyntaxError: invalid syntax",
    "fixed_code": "broken_code_here",
    "messages": [],
    "iterations": 0,
    "visited_nodes": []
})

def print_messages(result):
    print("\n=== EXECUTION LOG ===")
    for i, msg in enumerate(result["messages"], 1):
        role = msg.__class__.__name__.replace("Message", "").lower()
        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        print(f"[{i}] {role.upper()}: {content}")
    print("=== PATH ===")
    print(" → ".join(result["visited_nodes"]))
    print("============\n")

# Usage (replace your print)
print_messages(result)
print("FINAL CODE:\n", result["fixed_code"])
