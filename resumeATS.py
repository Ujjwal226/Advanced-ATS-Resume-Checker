import streamlit as st
import os
import sqlite3 
import re 
from dotenv import load_dotenv
import google.generativeai as genai
from PyPDF2 import PdfReader


load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


DB_FILE = "feedback.db"


if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = ""
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = ""


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    return conn


def create_feedback_table(conn):
    try:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feedback_text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error creating table: {e}")


def insert_feedback(feedback_text):
    conn = create_connection(DB_FILE)
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("INSERT INTO feedback(feedback_text) VALUES(?)", (feedback_text,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            st.error(f"Error inserting feedback: {e}")
            conn.close()
            return False
    return False


conn = create_connection(DB_FILE)
if conn:
    create_feedback_table(conn)
    conn.close()


def get_gemini_output(pdf_text, prompt):
    response = model.generate_content([pdf_text, prompt])
    return response.text


def read_pdf(uploaded_file):
    if uploaded_file is not None:
        pdf_reader = PdfReader(uploaded_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()
        return pdf_text
    else:
        st.error("No file uploaded") 
        return ""


st.set_page_config(page_title="ResumeChecker", layout="wide")


st.markdown("""
    <style>
    /* Main content area styling */
    .main {
        background-color: #f5f5f7; /* Light gray background */
        color: #1d1d1f; /* Dark text color */
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; /* System font stack */
        padding: 2rem;
    }

    /* Sidebar styling */
    .stsidebar > div:first-child {
        background-color: #ffffff; /* White background */
        padding: 1.5rem;
        border-right: 1px solid #e0e0e0; /* Subtle border */
        box-shadow: 2px 0 5px rgba(0,0,0,0.05); /* Soft shadow */
    }

    /* Title and subheader styling */
    h1 {
        color: #1d1d1f;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    h2 {
        color: #3a3a3c;
        font-size: 1.8rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    h3 {
        color: #5a5a5c;
        font-size: 1.4rem;
        margin-top: 1rem;
        margin-bottom: 0.8rem;
    }

    /* Button styling */
    .stButton>button {
        background-color: #0071e3; /* Apple Blue */
        color: white;
        border-radius: 8px; /* Slightly less rounded */
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        transition: background-color 0.2s ease-in-out;
        border: none;
    }
    .stButton>button:hover {
        background-color: #005cb2; /* Darker blue on hover */
        color: white; /* Ensure text remains white on hover */
    }

    /* Text input and text area styling */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-radius: 8px; /* Consistent with buttons */
        border: 1px solid #d0d0d0;
        padding: 0.75rem;
        width: 100%;
        box-sizing: border-box; /* Include padding and border in element's total width */
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; /* Consistent font */
    }
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #0071e3; /* Highlight with blue on focus */
        outline: none; /* Remove default outline */
        box-shadow: 0 0 0 0.1rem rgba(0, 113, 227, 0.25); /* Add a subtle glow */
    }

    /* File uploader styling */
    .stFileUploader>div>div>button {
         background-color: #e9e9eb; /* Light gray button */
         color: #1d1d1f;
         border-radius: 8px;
         padding: 0.75rem 1.5rem;
         font-size: 1rem;
         transition: background-color 0.2s ease-in-out;
         border: none;
    }
    .stFileUploader>div>div>button:hover {
         background-color: #d0d0d2; /* Darker gray on hover */
         color: #1d1d1f;
    }

    /* Radio button styling */
    .stRadio > label {
        margin-right: 15px; /* Add space between options */
        font-weight: normal;
    }
    .stRadio > label > div > div {
        border-radius: 50%; /* Make radio circles round */
        border: 1px solid #d0d0d0;
        width: 16px;
        height: 16px;
        margin-right: 5px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
     .stRadio > label > div > div > div {
        background-color: #0071e3; /* Blue selected state */
        border-radius: 50%;
        width: 8px;
        height: 8px;
     }

    /* Success/Warning messages */
    .stSuccess {
        background-color: #e9f5e9;
        color: #1e7b1e;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
        border: 1px solid #c8e6c9;
    }
    .stWarning {
        background-color: #fff8e1;
        color: #ff8f00;
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
         border: 1px solid #ffecb3;
    }

    /* Adjust markdown link colors in sidebar */
    .stsidebar a {
        color: #0071e3; /* Apple blue for links */
        text-decoration: none;
    }
    .stsidebar a:hover {
        text-decoration: underline;
    }

    </style>
""", unsafe_allow_html=True)


st.title("ResumeChecker")
st.subheader("Optimize Your Resume for ATS and Get Hired")


st.markdown("\n")


st.write("Upload your resume below:") 
upload_file = st.file_uploader("", type=["pdf"], label_visibility="collapsed") 


st.markdown("\n")


st.write("Enter the job description (optional):") 
job_description = st.text_area("", height=150, label_visibility="collapsed") 


st.markdown("\n")


st.write("Choose analysis type:") #
analysis_option = st.radio("", 
                           ["Quick Scan", "Detailed Analysis", "ATS Optimization"], horizontal=True, label_visibility="collapsed")


st.markdown("\n")


if st.button("Analyze Resume", use_container_width=True): 
    if upload_file is not None:
        pdf_text = read_pdf(upload_file)
        st.session_state.pdf_text = pdf_text 
        
        if pdf_text: 
            if analysis_option == "Quick Scan":
                prompt = f"""
                You are ResumeChecker, an expert in resume analysis. Provide a quick scan of the following resume. Structure your response using Markdown headings.
                
                ## Suitable Profession
                Identify the most suitable profession for this resume.
                
                ## Strengths
                List 3 key strengths of the resume.
                
                ## Quick Improvements
                Suggest 2 quick improvements.
                
                ## Overall ATS Score
                Give an overall ATS score out of 100.
                
                Resume text: {pdf_text}
                Job description (if provided): {job_description}
                """
            elif analysis_option == "Detailed Analysis":
                prompt = f"""
                You are ResumeChecker, an expert in resume analysis. Provide a detailed analysis of the following resume. Structure your response using Markdown headings for each section.
                
                ## Suitable Profession
                Identify the most suitable profession for this resume.
                
                ## Strengths
                List 5 strengths of the resume.
                
                ## Areas for Improvement
                Suggest 3-5 areas for improvement with specific recommendations.
                
                ## Section Review
                Provide a brief review of each major section (e.g., Summary, Experience, Education).
                
                ## Ratings
                Rate the following aspects out of 10: Impact, Brevity, Style, Structure, Skills. Present this as a list.
                
                ## Overall ATS Score
                Give an overall ATS score out of 100 with a breakdown of the scoring.
                
                Resume text: {pdf_text}
                Job description (if provided): {job_description}
                """
            else:  
                prompt = f"""
                You are ResumeChecker, an expert in ATS optimization. Analyze the following resume and provide optimization suggestions for the given job description. Structure your response using Markdown headings for each section. Specifically, provide lists of keywords as requested.
                
                ## Identified Keywords from Job Description
                List the key technical and soft skill keywords identified from the job description.

                ## Keywords Found in Resume
                List the keywords from the job description that are found in the resume text.

                ## Missing Keywords
                List the keywords from the job description that are *not* found in the resume text.

                ## Reformatting Suggestions
                Suggest reformatting or restructuring to improve ATS readability.
                
                ## Keyword Density
                Recommend changes to improve keyword density without keyword stuffing.
                
                ## Tailoring Suggestions
                Provide 3-5 bullet points on how to tailor this resume for the specific job description.
                
                ## ATS Compatibility Score
                Give an ATS compatibility score out of 100 and explain how to improve it.
                
                Resume text: {pdf_text}
                Job description: {job_description}
                """
            
            response = get_gemini_output(pdf_text, prompt)
            st.session_state.analysis_results = response 
            
            st.subheader("Analysis Results")
            
            st.markdown(st.session_state.analysis_results)
            
          
            if analysis_option == "ATS Optimization":
                
                response_sections = response.split("## ")
                keywords_found_section = ""
                missing_keywords_section = ""

                for section in response_sections:
                    if section.strip().startswith("Keywords Found in Resume"):
                        keywords_found_section = section.replace("Keywords Found in Resume", "", 1).strip()
                    elif section.strip().startswith("Missing Keywords"):
                        missing_keywords_section = section.replace("Missing Keywords", "", 1).strip()

                
                found_keywords = []
               
                if keywords_found_section:
                    
                    lines = keywords_found_section.split('\n')
                    for line in lines:
                        
                        cleaned_line = re.sub(r'^[-*\s]*', '', line).strip()
                        if cleaned_line:
                           
                            for keyword in re.split(r',\s*', cleaned_line):
                                if keyword:
                                    found_keywords.append(keyword.strip())

           
                if st.session_state.pdf_text and found_keywords:
                    with st.expander("View Resume Text with Found Keywords Highlighted"):
                        highlighted_text = highlight_keywords(st.session_state.pdf_text, found_keywords)
                        st.markdown(highlighted_text, unsafe_allow_html=True)

                
                if missing_keywords_section:
                    st.subheader("Missing Keywords from Job Description")
                  
                    st.markdown(missing_keywords_section)
      
            
            
            st.subheader("Have questions about your resume?")
            user_question = st.text_input("Ask me anything about your resume or the analysis:")
            if user_question:
                chat_prompt = f"""
                Based on the resume and analysis above, answer the following question:
                {user_question}
                
                Resume text: {pdf_text}
                Previous analysis: {response}
                """
                chat_response = get_gemini_output(pdf_text, chat_prompt)
                st.write(chat_response)
        else:
            st.error("No text extracted from the file.")
    else:
        st.error("Please upload a resume to analyze.")


st.subheader("Edit Resume Text")
st.write("Edit the extracted resume text below:")
edited_text = st.text_area(
    "", 
    value=st.session_state.pdf_text, 
    height=400, 
    key="resume_editor", 
    label_visibility="collapsed"
)


st.session_state.pdf_text = edited_text


if st.button("Download Edited Text"): 
    if edited_text:
        st.download_button(
            label="Click to Download",
            data=edited_text,
            file_name="edited_resume.txt",
            mime="text/plain"
        )
    else:
        st.warning("No text to download.")


st.sidebar.title("Resources")
st.sidebar.markdown("""
- [Resume Writing Tips](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/)
- [ATS Optimization Guide](https://career.io/career-advice/create-an-optimized-ats-resume)
- [Interview Preparation](https://hbr.org/2021/11/10-common-job-interview-questions-and-how-to-answer-them)
""")


st.sidebar.title("Feedback")
st.sidebar.markdown("Help us improve! Leave your feedback:") 

feedback_text = st.sidebar.text_area("", key="feedback_input", label_visibility="collapsed") 

if st.sidebar.button("Submit Feedback", use_container_width=True):
    if feedback_text:
        if insert_feedback(feedback_text):
            st.sidebar.success("Thank you for your feedback! It has been stored in the database.")
            
        else:
            st.sidebar.warning("Please enter some feedback before submitting.")
    else:
        st.sidebar.warning("Please enter some feedback before submitting.")


def highlight_keywords(text, keywords):
    if not keywords:
        return text

    
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    highlighted_text = text

    for keyword in sorted_keywords:
       
        try:
            pattern = r'\b(' + re.escape(keyword) + r')\b'
            highlighted_text = re.sub(
                pattern,
                lambda match: f"<mark>{match.group(0)}</mark>",
                highlighted_text,
                flags=re.IGNORECASE
            )
        except re.error as e:
            st.warning(f"Error highlighting keyword '{keyword}': {e}")
            
            continue

    return highlighted_text
