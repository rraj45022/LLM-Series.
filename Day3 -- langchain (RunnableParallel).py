import os
import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel
dotenv.load_dotenv()
os.environ.get("GROQ_API_KEY")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

llm1 = ChatPromptTemplate.from_template("Error cause in 1 line: {trace}") | llm | StrOutputParser()
llm2 = ChatPromptTemplate.from_template("5 numbered fix steps: {trace}") | llm | StrOutputParser()

parallel_llms = RunnableParallel(cause=llm1, fixes=llm2)
trace = "ModuleNotFoundError: No module named 'langchain.chains'"
result = parallel_llms.invoke({"trace": trace})
print("🔍 Cause:", result["cause"])
print("🛠️  Fixes:\n" + result["fixes"])
