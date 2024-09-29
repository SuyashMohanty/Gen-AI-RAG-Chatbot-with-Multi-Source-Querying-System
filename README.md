# RAG Chatbot with Multi-Source Querying System

## Project Overview

This project implements a **Retrieval Argument Generation (RAG) Chatbot** with a multi-source querying system designed to handle natural language queries across three key domains: **Technical**, **Diet**, and **Patient-related** information. Depending on the query type, the system retrieves information from different sources:

- **PDF Documents** (for Technical queries)
- **Web URLs** (for Diet-related queries)
- **MS SQL Database** (for Patient-related queries)

In addition to routing queries to specific data sources based on relevance, the system includes a **fallback mechanism** for handling unknown or irrelevant queries. If the chatbot cannot categorize a query into any predefined category (Technical, Diet, or Patient), it will:
1. **Search Both PDF and Web Sources**: Attempt to find relevant content in both the loaded PDFs and predefined web URLs.
2. **No Relevant Content**: If no content is found, the chatbot will return a default message indicating that it lacks sufficient information to answer the query.

This fallback mechanism improves the user experience by handling unexpected or vague queries effectively.

## System Components

The system consists of two main components:
1. **FastAPI Uvicorn Server** (Backend)
2. **Streamlit Client** (Frontend)

### 1. FastAPI Uvicorn Server

The FastAPI server acts as the backend responsible for handling various query types. It integrates multiple tools to retrieve data from different sources.

#### Key Features:

- **Predefined Knowledge Routing**:
  - **Technical Queries (PDF)**: For technical queries, the system processes PDFs using LangChain’s PDF Loader. Documents are chunked using the Recursive Character Text Splitter, and embeddings are generated using OpenAI Embeddings for querying.
  - **Diet Queries (Web URL)**: Diet-related queries retrieve information from predefined web URLs using the Web Base Loader.
  - **Patient Queries (MS SQL Database)**: Patient-related queries are handled by connecting to an MS SQL Database using SQLAlchemy to fetch relevant data.
  
- **JWT Authentication**:
  - The server uses OAuth2PasswordBearer for user authentication, generating JWT tokens to manage secure access to the API.

- **Vector Store (FAISS)**:
  - Document embeddings are stored in a FAISS Vector Store, which allows efficient similarity search when querying documents.

- **SQL Database Interaction**:
  - For patient-related queries, the server interacts with the MS SQL Database using an SQL agent to retrieve the relevant records.

- **Fallback for Irrelevant Queries**:
  - If the query type is unrecognized, the system enters fallback mode:
    - It queries both PDFs and Web URLs for relevant information.
    - If no relevant information is found, the chatbot responds with a polite message stating that it couldn't find any related content.

This logic ensures that users are informed even when their query falls outside the predefined categories.

#### API Endpoints:

- **POST /query**: The main endpoint where the server receives a query, determines its type (Technical, Diet, or Patient-related), and routes it to the appropriate data source.

#### Server Application Screenshots

1. **Swagger Documentation**  
   ![Swagger Documentation](https://github.com/user-attachments/assets/35147e54-4b02-4186-b9c6-2819114a5f6d)

2. **Code Logic for Query Routing**  
   ![Code Logic for Query Routing 1](https://github.com/user-attachments/assets/9f3a129c-02b1-4923-b569-ee9b25614f9a)  
   ![Code Logic for Query Routing 2](https://github.com/user-attachments/assets/8664037b-3993-433a-a0ee-f3b4dd2a1033)

3. **MS SQL DB Integration**  
   <img width="696" alt="MS SQL DB Integration" src="https://github.com/user-attachments/assets/00e7e8f1-8c27-4208-ac60-d180b78c266a">

4. **PDF & Web Query Logic**  
   <img width="539" alt="PDF & Web Query Logic 1" src="https://github.com/user-attachments/assets/700fccae-572b-439c-a000-3ea604142c56">  
   <img width="760" alt="PDF & Web Query Logic 2" src="https://github.com/user-attachments/assets/f69fb1d8-7abb-4cff-ae88-e1488c002956">  
   <img width="419" alt="PDF & Web Query Logic 3" src="https://github.com/user-attachments/assets/3919b3a4-4c72-45d8-8b52-2a43fbd7c787">

#### Database Screenshots

1. **JWT Authentication Users Table**  
   <img width="680" alt="Users Table" src="https://github.com/user-attachments/assets/96f6991a-8a09-454d-974d-1e79375054ef">

2. **Patients Table**  
   <img width="680" alt="Patients Table" src="https://github.com/user-attachments/assets/c6b6d08c-01ad-43aa-a4b3-d49352c4b4dd">

### 2. Streamlit Client

The Streamlit client serves as the frontend where users can interact with the system via a user-friendly interface. It provides options for logging in, entering queries, and receiving responses based on the content type.

#### Key Features:

- **Login & JWT Token**:
  - Users must authenticate via a login form. Upon successful authentication, a JWT token is retrieved from the FastAPI server and stored in the session state.

- **Query Submission**:
  - After authentication, users can enter their queries in a text box. The system routes the request to the FastAPI server, which returns results from the relevant data source (PDFs, web content, or MS SQL database).

- **Dynamic Query Handling**:
  - The app dynamically routes queries to the FastAPI backend, which retrieves answers based on the query type.

#### Client Application Screenshots

1. **Login Screen**  
   <img width="491" alt="1 Login Screen" src="https://github.com/user-attachments/assets/525cc791-3259-4512-9e2d-efee6aad2bab">

2. **Authenticated Interface**  
   <img width="491" alt="2 Authenticated Interface" src="https://github.com/user-attachments/assets/1fe89101-976b-4140-bae7-b89953f2c2b6">

### 3. Query Processing

#### 3.1 PDF Query Processing:
<img width="443" alt="3 1 PDF Query Processing" src="https://github.com/user-attachments/assets/d07c7832-956a-4f1d-b0a9-4ffaf8db28ef">

#### 3.2 Web URL Query Processing:
<img width="485" alt="3 2 Web URL Query Processing" src="https://github.com/user-attachments/assets/5e592e04-af61-4b72-91a2-914ba31c9984">

#### 3.3 SQL Patients DB Query Processing:
<img width="481" alt="3 3 SQL Patients DB Query Processing" src="https://github.com/user-attachments/assets/a0faf889-957c-4e54-8e3a-f64e3383ccc3">

#### 3.4 Irrelevant Query Processing:
<img width="493" alt="3 4 Irrelevant Query Processing" src="https://github.com/user-attachments/assets/f66a6a43-979b-45af-a599-cec8237a51b3">

### 4. Streamlit Interface:
<img width="926" alt="4 Streamlit Interface" src="https://github.com/user-attachments/assets/7769925a-b64c-4a0b-aa43-242b28df57ba">

## Conclusion

This project combines natural language processing, retrieval-augmented generation, document retrieval, web scraping, and SQL querying into a seamless multi-source chatbot. It leverages FastAPI for efficient backend management and JWT-based authentication for secure access. The Streamlit frontend offers an intuitive user interface, allowing users to interact with multiple data sources depending on their query type.
