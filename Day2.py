from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS  # FAISS!
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import dotenv
import os
dotenv.load_dotenv()
os.environ.get("GROQ_API_KEY")

loader = PyPDFLoader("./life-skills-counseling.pdf")
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
prompt = PromptTemplate.from_template("Context: {context}\nQuestion: {question}\nEnglish answer:")
chain = (
    {"context": retriever | (lambda docs: "\n".join(doc.page_content for doc in docs)), 
     "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)
print(chain.invoke("What are the important life skills mentioned in the document?"))