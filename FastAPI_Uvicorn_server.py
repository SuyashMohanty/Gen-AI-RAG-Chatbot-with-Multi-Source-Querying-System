from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.agents import create_sql_agent
from sqlalchemy import create_engine, Table, MetaData
from langchain.agents.agent_types import AgentType
import urllib.parse
import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize LLM and embeddings
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, max_tokens=1000)
embeddings = OpenAIEmbeddings()

# Vector stores for PDFs and URLs
pdf_vectorstore = None
url_vectorstore = None

# SQL Database Connection for PatientConsultationDB
SERVER = os.getenv("DB_SERVER")
PATIENT_DB = os.getenv("DB_NAME")  
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")

if not all([SERVER, PATIENT_DB, USER, PASSWORD]):
    raise ValueError("Missing one or more environment variables for PatientConsultationDB.")

# Encode password for URL
encoded_password = urllib.parse.quote_plus(PASSWORD)

# Connection string for SQL Server (PatientConsultationDB)
patient_cs = f"mssql+pyodbc://{USER}:{encoded_password}@{SERVER}/{PATIENT_DB}?driver=ODBC+Driver+17+for+SQL+Server"

patient_engine = create_engine(patient_cs)
patient_db = SQLDatabase(patient_engine)

# Create SQL toolkit and agent
toolkit = SQLDatabaseToolkit(db=patient_db, llm=llm)
sql_agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# SQL Database Connection for ChatbotDB (Authentication)
AUTH_DB = os.getenv("DB_Auth_NAME")  

if not AUTH_DB:
    raise ValueError("Missing DB_Auth_NAME environment variable for ChatbotDB.")

# Connection string for SQL Server (ChatbotDB)
auth_cs = f"mssql+pyodbc://{USER}:{encoded_password}@{SERVER}/{AUTH_DB}?driver=ODBC+Driver+17+for+SQL+Server"

auth_engine = create_engine(auth_cs)

# User model
class User(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class QueryRequest(BaseModel):
    query: str

# Function to get user from database
def get_user(username: str):
    metadata = MetaData()
    users = Table('users', metadata, autoload_with=auth_engine)
    with auth_engine.connect() as connection:
        result = connection.execute(users.select().where(users.c.Name == username)).first()
    if result:
        return {"username": result.Name, "password": result.Password}

# Function to authenticate user
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not user["password"] == password:  
        return False
    return user

# Function to create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Token endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    print(access_token)
    return {"access_token": access_token, "token_type": "bearer"}

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = User(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Global flag to check if knowledge base is initialized
knowledge_base_initialized = False

# Load and process the PDF and URL content
def initialize_knowledge_base():
    global pdf_vectorstore, url_vectorstore, knowledge_base_initialized

    try:
        logger.info("Starting knowledge base initialization...")

        # Load PDF content
        logger.info("Loading PDF content...")
        pdf_loader = PyPDFLoader('Technical_DIABETES.pdf')
        pdf_docs = pdf_loader.load()
        logger.info("PDF content loaded successfully.")

        logger.info("Splitting PDF documents...")
        pdf_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        pdf_documents = pdf_splitter.split_documents(pdf_docs)
        logger.info("PDF documents split successfully.")

        # Load URL content
        logger.info("Loading URL content...")
        url_loader = WebBaseLoader("https://www.mayoclinic.org/diseases-conditions/diabetes/in-depth/diabetes-diet/art-20044295")
        url_docs = url_loader.load()
        logger.info("URL content loaded successfully.")

        logger.info("Splitting URL documents...")
        url_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        url_documents = url_splitter.split_documents(url_docs)
        logger.info("URL documents split successfully.")

        # Create FAISS vector stores
        logger.info("Creating PDF vector store...")
        pdf_vectorstore = FAISS.from_documents(pdf_documents, embeddings)
        logger.info("PDF vector store created successfully.")

        logger.info("Creating URL vector store...")
        url_vectorstore = FAISS.from_documents(url_documents, embeddings)
        logger.info("URL vector store created successfully.")

        knowledge_base_initialized = True
        logger.info("Knowledge base initialized successfully.")

    except Exception as e:
        logger.error(f"Error initializing knowledge base: {e}", exc_info=True)
        knowledge_base_initialized = False

# Call to initialize the knowledge base when the application starts
logger.info("Calling initialize_knowledge_base()...")
initialize_knowledge_base()
logger.info("initialize_knowledge_base() call completed.")

# Modified query function
def query_vectorstore(query: str, vectorstore, k=3):
    if vectorstore is None:
        raise ValueError("Vector store is not initialized")
    
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": k}),
        return_source_documents=True,
        chain_type="stuff"
    )
    result = qa_chain({"query": query})
    return result["result"]


# Modified query function
def query_vectorstore(query: str, vectorstore, k=3):
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": k}),
        return_source_documents=True,
        chain_type="stuff"
    )
    result = qa_chain({"query": query})
    return result["result"]

# Protected query endpoint
@app.post("/query")
async def query_system(request: QueryRequest, current_user: User = Depends(get_current_user)):
    try:
        if not knowledge_base_initialized:
            return {"error": "Knowledge base is not initialized. Please try again later."}

        query = request.query.lower()
        
        if "patient" in query:
            # Query SQL database using the agent
            response = sql_agent.run(query)
            return {"answer": response}

        elif "diet" in query and url_vectorstore:
            # Query the URL vectorstore for diet-related info
            answer = query_vectorstore(query, url_vectorstore)
            return {"answer": answer}

        elif "technical" in query and pdf_vectorstore:
            # Query the PDF vectorstore for technical info
            answer = query_vectorstore(query, pdf_vectorstore)
            return {"answer": answer}

        else:
            # If no specific source is identified, try both PDF and URL sources
            pdf_answer = query_vectorstore(query, pdf_vectorstore)
            url_answer = query_vectorstore(query, url_vectorstore)
            
            # Combine answers
            combined_answer = f"From PDF: {pdf_answer}\n\nFrom Web: {url_answer}"
            
            return {"answer": combined_answer}
    
    except ValueError as ve:
        return {"error": str(ve)}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

# Start FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)