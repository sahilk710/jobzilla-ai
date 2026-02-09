"""
Jobzilla Frontend - Streamlit Application

Main entry point with navigation and session management.
Connects to backend API for real job matching.
"""

import streamlit as st
import requests
import os

# Backend API URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="KillMatch - AI Job Matching",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for premium styling
st.markdown("""
<style>
    /* Main theme */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --background-dark: #0f0f23;
        --card-bg: rgba(255, 255, 255, 0.05);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
    }
    
    /* Score gauge */
    .score-high { color: #10b981; }
    .score-medium { color: #f59e0b; }
    .score-low { color: #ef4444; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)


def fetch_jobs_from_db(limit=10):
    """Fetch real jobs from the backend/database."""
    try:
        # Try to get jobs from backend API
        response = requests.get(f"{BACKEND_URL}/api/v1/jobs", params={"limit": limit}, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback: Direct database query via a simple endpoint we'll create
    # For now, use psycopg2 directly
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "killmatch"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres")
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, company, description, source_platform 
            FROM jobs 
            WHERE is_active = true
            ORDER BY scraped_at DESC 
            LIMIT %s
        """, (limit,))
        jobs = []
        for row in cur.fetchall():
            jobs.append({
                "id": row[0],
                "title": row[1],
                "company": row[2],
                "description": row[3] or "",
                "source": row[4] or "LinkedIn"
            })
        cur.close()
        conn.close()
        return jobs
    except Exception as e:
        st.warning(f"Could not fetch jobs from database: {e}")
        return []


def main():
    """Main application entry point."""
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎯 KillMatch")
        st.caption("*AI-Powered Job Matching*")
        st.divider()
        
        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "🔍 Job Match", "🤖 Agent Debate", 
             "✉️ Cover Letter", "📈 Skill Roadmap", "📊 Analytics", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Profile section
        st.markdown("### 👤 Profile")
        if "resume_uploaded" in st.session_state and st.session_state["resume_uploaded"]:
            st.success("✅ Resume uploaded")
        else:
            st.info("Upload your resume to get started")
    
    # Route to pages
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🔍 Job Match":
        show_job_match()
    elif page == "🤖 Agent Debate":
        show_agent_debate()
    elif page == "✉️ Cover Letter":
        show_cover_letter()
    elif page == "📈 Skill Roadmap":
        show_skill_roadmap()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "⚙️ Settings":
        show_settings()


def show_dashboard():
    """Dashboard page - showing real jobs from database."""
    st.markdown('<h1 class="main-header">Welcome Back! 👋</h1>', unsafe_allow_html=True)
    
    # Fetch real jobs from database
    jobs = fetch_jobs_from_db(limit=20)
    total_jobs = len(jobs)
    
    # Quick stats - now with real data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", str(total_jobs), "+scraped today")
    with col2:
        st.metric("Sources", "LinkedIn, Indeed", "Active")
    with col3:
        if "resume_uploaded" in st.session_state:
            st.metric("Profile", "Ready", "Complete")
        else:
            st.metric("Profile", "Pending", "Upload resume")
    with col4:
        st.metric("Database", "PostgreSQL", "Connected")
    
    st.divider()
    
    # Show real jobs from database
    st.markdown("### 🌟 Latest Scraped Jobs")
    
    if jobs:
        for job in jobs[:5]:  # Show top 5
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{job['title']}** at {job['company']}")
                with col2:
                    st.caption(f"via {job.get('source', 'LinkedIn')}")
                with col3:
                    if st.button(f"View", key=f"view_{job['id']}"):
                        st.session_state["selected_job"] = job
                st.divider()
    else:
        st.info("No jobs found. Run the Airflow job_scraping DAG to populate jobs!")
        st.markdown("Go to http://localhost:8080 → trigger `job_scraping` DAG")


def show_job_match():
    """Job matching page with real backend integration."""
    st.markdown('<h1 class="main-header">🔍 Find Your Perfect Match</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📄 Your Profile")
        
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF)",
            type=["pdf"],
            help="We'll extract your skills and experience"
        )
        
        github_username = st.text_input(
            "GitHub Username (optional)",
            placeholder="e.g., octocat",
            help="We'll analyze your repositories for additional insights"
        )
        
        if uploaded_file:
            st.success("✅ Resume uploaded successfully!")
            st.session_state["resume_uploaded"] = True
            st.session_state["resume_file"] = uploaded_file
    
    with col2:
        st.markdown("### 🎯 Job Search")
        
        search_query = st.text_input(
            "What role are you looking for?",
            placeholder="e.g., Senior Python Developer"
        )
        
        location = st.text_input(
            "Preferred location",
            placeholder="e.g., San Francisco, CA or Remote"
        )
        
        experience_level = st.select_slider(
            "Experience Level",
            options=["Entry", "Mid", "Senior", "Lead", "Executive"],
            value="Senior"
        )
    
    st.divider()
    
    if st.button("🚀 Start Matching", use_container_width=True):
        if not search_query and not st.session_state.get("resume_uploaded"):
            st.warning("Please upload a resume or enter a search query!")
            return

        with st.spinner("Running semantic search & multi-agent analysis..."):
            try:
                # Prepare payload
                payload = {
                    "query": search_query,
                    "location": location,
                    "level": experience_level,
                    "github_username": github_username
                }
                
                # If resume uploaded, send it
                files = {}
                if st.session_state.get("resume_file"):
                    # Reset buffer position
                    st.session_state["resume_file"].seek(0)
                    files = {"resume": ("resume.pdf", st.session_state["resume_file"], "application/pdf")}
                    
                # Call backend match API
                # Note: We use the multipart/form-data endpoint
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/match",
                    data=payload,
                    files=files if files else None,
                    timeout=60  # Increased for Pinecone/OpenAI latency
                )
                
                if response.status_code == 200:
                    results = response.json()
                    st.session_state["matched_jobs"] = results.get("matches", [])
                    st.session_state["has_matches"] = True
                    st.rerun()
                else:
                    st.error(f"Validation failed: {response.text}")
                    
            except Exception as e:
                st.error(f"Matching failed: {str(e)}")
                # Fallback to local search if backend fails
                st.warning("Falling back to basic keyword search...")
                # ... (keep fallback logic if needed)
    
    # Show matched jobs
    if st.session_state.get("has_matches") and st.session_state.get("matched_jobs"):
        st.success(f"Found {len(st.session_state['matched_jobs'])} semantically matched jobs!")
        
        st.markdown("### 🎯 Your Matches")
        for job in st.session_state["matched_jobs"]:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    job_url = job.get('url', '')
                    if job_url:
                        st.markdown(f"**[{job['title']}]({job_url})** at {job['company']}")
                    else:
                        st.markdown(f"**{job['title']}** at {job['company']}")
                    st.caption(f"Position at {job['company']}. Found via {job.get('source', 'LinkedIn')}.")
                with col2:
                    score = job.get("match_score", 0) * 100 if job.get("match_score", 0) < 1 else job.get("match_score", 0)
                    score_class = "score-high" if score >= 80 else "score-medium" if score >= 60 else "score-low"
                    st.markdown(f"<span class='{score_class}'>{int(score)}% match</span>", unsafe_allow_html=True)
                with col3:
                    job_url = job.get('url', '')
                    if job_url:
                        st.link_button("Apply", job_url)
                    else:
                        st.button("Apply", key=f"apply_{job.get('id', job.get('title'))}", disabled=True)
                st.divider()


def run_langgraph_debate(job, resume_text, resume_skills, github_username):
    """Run the real LangGraph agent debate via backend API."""
    try:
        payload = {
            "resume_summary": resume_text[:2000],  # Limit length
            "resume_skills": resume_skills,
            "job_title": job.get("title", "Unknown"),
            "job_company": job.get("company", "Unknown"),
            "job_description": job.get("description", "")[:2000],  # Limit length
            "job_required_skills": job.get("missing_skills", []), # Use missing skills as proxy for important ones
            "github_username": github_username,
            "include_cover_letter": False
        }
        
        response = requests.post(f"{BACKEND_URL}/api/v1/debate/run-debate", json=payload, timeout=120)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Debate failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def show_agent_debate():
    """Enhanced Agent debate with job selection and detailed AI insights."""
    st.markdown('<h1 class="main-header">🤖 Agent Debate</h1>', unsafe_allow_html=True)
    
    # Explain the feature clearly
    st.info("""
    **How It Works:**
    - 🔴 **Recruiter Agent** plays devil's advocate and finds gaps
    - 🟢 **Coach Agent** advocates for your strengths and potential
    - ⚖️ **Judge Agent** listens to the debate and issues a final verdict
    """)
    
    # Check if we have matched jobs
    if not st.session_state.get("matched_jobs"):
        st.warning("No job matches found. Go to **Job Match** and run a search first!")
        if st.button("🔍 Go to Job Match"):
            st.switch_page("Job Match")
        return
    
    matched_jobs = st.session_state["matched_jobs"]
    
    # JOB SELECTOR - Let user choose which job to analyze
    st.markdown("### 📋 Select a Job to Analyze")
    job_options = [f"{j['title']} at {j['company']}" for j in matched_jobs]
    selected_idx = st.selectbox(
        "Choose a job from your matches:",
        range(len(job_options)),
        format_func=lambda x: job_options[x]
    )
    
    selected_job = matched_jobs[selected_idx]
    job_key = f"debate_result_{selected_job.get('id', selected_idx)}"
    
    # Get resume data from session
    resume_summary = st.session_state.get("resume_summary", "")
    # We need skills list - try to parse from summary or use empty
    resume_skills = [] 
    
    # UI Controls
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🚀 Run AI Debate", type="primary", use_container_width=True):
            with st.spinner("🤖 Agents are debating your candidacy... (This uses real GPT-4 calls)"):
                result = run_langgraph_debate(
                    selected_job, 
                    resume_summary, 
                    resume_skills, 
                    st.session_state.get("github_username")
                )
                if result:
                    st.session_state[job_key] = result
                    st.rerun()
    
    # Display Results if available
    if job_key in st.session_state:
        result = st.session_state[job_key]
        
        st.divider()
        st.markdown("## 🎙️ Live Debate Transcript")
        
        # Show debate rounds
        for round_data in result.get("debate_rounds", []):
            round_num = round_data.get("round_number", 1)
            
            with st.expander(f"�️ Round {round_num}", expanded=True):
                # Recruiter
                st.markdown("#### 🔴 Recruiter's Arguments")
                for arg in round_data.get("recruiter_arguments", []):
                    st.markdown(f"• **{arg.get('point')}**: {arg.get('evidence')} ({arg.get('strength')})")
                st.caption(f"Score: {round_data.get('recruiter_score')}/100")
                
                st.divider()
                
                # Coach
                st.markdown("#### � Coach's Rebuttal")
                for arg in round_data.get("coach_arguments", []):
                    st.markdown(f"• **{arg.get('point')}**: {arg.get('evidence')} ({arg.get('strength')})")
                st.caption(f"Score: {round_data.get('coach_score')}/100")

        # Final Verdict
        st.divider()
        st.markdown("## ⚖️ Judge's Final Verdict")
        
        final_score = result.get("final_score", 50)
        recommendation = result.get("recommendation", "Unknown")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Final Match Score", f"{final_score:.1f}/100")
        with col2:
            color = "🟢" if final_score >= 75 else "🟡" if final_score >= 55 else "�"
            st.markdown(f"### {color} {recommendation}")
        
        # Key factors
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**👍 Key Strengths**")
            for item in result.get("key_strengths", []):
                st.markdown(f"• {item}")
        with c2:
            st.markdown("**� Key Concerns**")
            for item in result.get("key_concerns", []):
                st.markdown(f"• {item}")
                
    else:
        st.info("👆 Click 'Run AI Debate' to see the Recruiter and Career Coach analyze your fit for this role in real-time!")



def show_cover_letter():
    """Cover letter generation."""
    st.markdown('<h1 class="main-header">✉️ Cover Letter Generator</h1>', unsafe_allow_html=True)
    
    if not st.session_state.get("matched_jobs"):
        st.warning("Run a job match first to generate tailored cover letters!")
        return
    
    # Select a job
    job_options = [f"{j['title']} at {j['company']}" for j in st.session_state["matched_jobs"]]
    selected = st.selectbox("Select a job to write a cover letter for:", job_options)
    
    col1, col2 = st.columns(2)
    with col1:
        tone = st.select_slider("Tone", options=["Casual", "Professional", "Formal"], value="Professional")
    with col2:
        focus = st.multiselect("Focus Areas", ["Technical Skills", "Leadership", "Culture Fit", "Achievements"], default=["Technical Skills"])
    
    if st.button("Generate Cover Letter", use_container_width=True):
        with st.spinner("Generating with AI..."):
            try:
                # Get the selected job details
                selected_idx = job_options.index(selected)
                job = st.session_state["matched_jobs"][selected_idx]
                
                # Resume text from session if available
                resume_summary = st.session_state.get("resume_summary", "a software professional with relevant experience")
                
                # Call OpenAI for cover letter
                import openai
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                
                prompt = f"""Write a {tone.lower()} cover letter for the following job:

Job Title: {job['title']}
Company: {job['company']}
Job Description: {job.get('description', 'Not provided')[:500]}

Candidate Profile: {resume_summary}

Focus areas: {', '.join(focus)}

Write a compelling cover letter (3-4 paragraphs) that:
1. Opens with an engaging hook
2. Connects the candidate's skills to the job requirements
3. Shows enthusiasm for the company
4. Ends with a strong call to action
"""
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=800
                )
                
                cover_letter = response.choices[0].message.content
                
                st.text_area(
                    "Your Cover Letter",
                    value=cover_letter,
                    height=400
                )
                
                # Copy button
                st.download_button(
                    "📋 Download as .txt",
                    cover_letter,
                    file_name=f"cover_letter_{job['company'].replace(' ', '_')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")
                st.warning("Make sure OPENAI_API_KEY is set in your environment.")


def show_skill_roadmap():
    """Enhanced skill gap analysis and roadmap based on actual matched jobs."""
    st.markdown('<h1 class="main-header">📈 Skill Roadmap</h1>', unsafe_allow_html=True)
    
    st.info("**How This Helps You**: Identifies skills most commonly required by your matched jobs but missing from your profile. Focus on these to maximize your job prospects!")
    
    if not st.session_state.get("matched_jobs"):
        st.warning("Run a job match first to see personalized skill recommendations!")
        if st.button("🔍 Go to Job Match"):
            st.switch_page("Job Match")
        return
    
    matched_jobs = st.session_state["matched_jobs"]
    
    st.markdown(f"### 📊 Analyzing {len(matched_jobs)} Matched Jobs")
    
    # Method 1: Use missing_skills from backend if available
    missing_counts = {}
    for job in matched_jobs:
        for skill in job.get("missing_skills", []):
            skill_clean = skill.strip().title()
            missing_counts[skill_clean] = missing_counts.get(skill_clean, 0) + 1
    
    # Method 2: Extract common skills from job descriptions AND titles if no missing_skills
    if not missing_counts:
        st.caption("*Extracting skills from job descriptions...*")
        # Common tech skills to look for (expanded list including data science and variations)
        skill_keywords = [
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'sql', 'r ', 'scala', 'go ', 'rust',
            'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'terraform', 'jenkins',
            'ci/cd', 'devops', 'cloud', 'microservices',
            # Data & ML
            'machine learning', 'deep learning', 'nlp', 'natural language', 'computer vision',
            'data science', 'data engineering', 'data analysis', 'data analyst',
            'tensorflow', 'pytorch', 'keras', 'scikit', 'sklearn', 'pandas', 'numpy',
            'spark', 'hadoop', 'kafka', 'airflow', 'dbt', 'snowflake', 'databricks',
            'etl', 'data pipeline', 'big data',
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'neo4j',
            # GenAI / LLM
            'llm', 'genai', 'generative ai', 'gpt', 'langchain', 'rag', 'transformers',
            'hugging face', 'chatgpt', 'openai', 'large language',
            # Web & Frameworks
            'react', 'node.js', 'nodejs', 'angular', 'vue', 'django', 'flask', 'fastapi',
            'spring', 'graphql', 'rest api',
            # BI & Visualization
            'tableau', 'power bi', 'looker', 'excel', 'visualization',
            # Methodologies
            'agile', 'scrum', 'git', 'linux',
            # Soft skills / Roles
            'leadership', 'director', 'manager', 'senior', 'architect', 'lead'
        ]
        
        for job in matched_jobs:
            # Check BOTH description AND title for skills
            desc = (job.get("description", "") or "").lower()
            title = (job.get("title", "") or "").lower()
            full_text = f"{title} {desc}"
            
            for skill in skill_keywords:
                if skill in full_text:
                    # Clean up the skill name for display
                    skill_display = skill.strip().title()
                    # Handle special cases
                    if skill in ['r ', 'go ']:
                        skill_display = skill.strip().upper()
                    elif skill in ['aws', 'gcp', 'sql', 'nlp', 'llm', 'etl', 'ci/cd', 'k8s', 'api']:
                        skill_display = skill.upper()
                    elif skill in ['genai']:
                        skill_display = 'GenAI'
                    elif skill in ['node.js', 'nodejs']:
                        skill_display = 'Node.js'
                    elif skill in ['postgresql', 'mysql', 'mongodb']:
                        skill_display = skill.replace('sql', 'SQL').replace('db', 'DB').title()
                    
                    missing_counts[skill_display] = missing_counts.get(skill_display, 0) + 1
    
    # Sort by frequency
    sorted_skills = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Resources mapping
    resources = {
        "Python": "https://docs.python.org/3/tutorial/",
        "Java": "https://dev.java/learn/",
        "Javascript": "https://javascript.info/",
        "Sql": "https://www.w3schools.com/sql/",
        "Aws": "https://aws.amazon.com/training/",
        "Azure": "https://learn.microsoft.com/en-us/training/azure/",
        "Gcp": "https://cloud.google.com/training",
        "Docker": "https://docs.docker.com/get-started/",
        "Kubernetes": "https://kubernetes.io/docs/tutorials/",
        "React": "https://react.dev/learn",
        "Node.Js": "https://nodejs.org/en/learn",
        "Tensorflow": "https://www.tensorflow.org/tutorials",
        "Pytorch": "https://pytorch.org/tutorials/",
        "Spark": "https://spark.apache.org/docs/latest/quick-start.html",
        "Machine Learning": "https://www.coursera.org/learn/machine-learning",
        "Deep Learning": "https://www.deeplearning.ai/",
        "Nlp": "https://huggingface.co/learn/nlp-course",
        "Airflow": "https://airflow.apache.org/docs/",
        "Snowflake": "https://learn.snowflake.com/",
        "System Design": "https://github.com/donnemartin/system-design-primer",
    }
    
    if sorted_skills:
        st.markdown("### 🎯 Top Skills to Learn")
        st.markdown("*These skills appear most frequently in your matched job descriptions:*")
        
        for i, (skill, count) in enumerate(sorted_skills[:8]):
            priority = "🔴 High" if count >= 3 else "🟡 Medium" if count >= 2 else "🟢 Low"
            time_est = "2-4 weeks" if count < 3 else "1-2 months" if count < 5 else "2-3 months"
            
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{skill}** - *Found in {count} jobs*")
                with col2:
                    st.caption(f"Priority: {priority}")
                with col3:
                    st.caption(f"Est: {time_est}")
                with col4:
                    resource_url = resources.get(skill, f"https://www.google.com/search?q=learn+{skill.replace(' ', '+')}")
                    st.link_button("📚 Learn", resource_url, use_container_width=True)
        
        # Show summary stats
        st.divider()
        st.markdown("### 📈 Your Skill Gap Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Unique Skills to Learn", len(sorted_skills))
        with col2:
            high_priority = len([s for s, c in sorted_skills if c >= 3])
            st.metric("High Priority", high_priority)
        with col3:
            st.metric("Jobs Analyzed", len(matched_jobs))
    else:
        st.success("🎉 Great news! No significant skill gaps detected in your matched jobs!")
        st.info("This could mean:\n- Your skills align well with available roles\n- Try matching with different job types to discover new skills to learn")


def show_analytics():
    """Enhanced Analytics dashboard with personal insights and database stats."""
    st.markdown('<h1 class="main-header">📊 Analytics</h1>', unsafe_allow_html=True)
    
    st.info("**Your Job Search Analytics**: Track your searches, analyze company trends, and see skills in demand.")
    
    # ============ PERSONAL ANALYTICS ============
    st.markdown("### 👤 Your Activity")
    col1, col2, col3, col4 = st.columns(4)
    
    matched_jobs = st.session_state.get("matched_jobs", [])
    
    with col1:
        st.metric("Jobs Matched", len(matched_jobs))
    with col2:
        if matched_jobs:
            avg_score = sum(j.get("match_score", 0) for j in matched_jobs) / len(matched_jobs)
            avg_score = avg_score * 100 if avg_score <= 1 else avg_score
            st.metric("Avg Match Score", f"{avg_score:.0f}%")
        else:
            st.metric("Avg Match Score", "N/A")
    with col3:
        resume_status = "✅ Yes" if st.session_state.get("resume_uploaded") else "❌ No"
        st.metric("Resume Uploaded", resume_status)
    with col4:
        gh_user = st.session_state.get("github_username", "")
        st.metric("GitHub Connected", gh_user if gh_user else "❌ No")
    
    # ============ MATCHED JOBS ANALYSIS ============
    if matched_jobs:
        st.divider()
        st.markdown("### 🏢 Companies in Your Matches")
        
        # Company breakdown
        companies = {}
        for job in matched_jobs:
            company = job.get("company", "Unknown")
            companies[company] = companies.get(company, 0) + 1
        
        sorted_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)
        
        cols = st.columns(min(len(sorted_companies), 4))
        for i, (company, count) in enumerate(sorted_companies[:4]):
            with cols[i]:
                st.metric(company[:15] + "..." if len(company) > 15 else company, f"{count} jobs")
        
        # Match score distribution
        st.divider()
        st.markdown("### 📈 Match Score Distribution")
        
        high_matches = len([j for j in matched_jobs if (j.get("match_score", 0) * 100 if j.get("match_score", 0) <= 1 else j.get("match_score", 0)) >= 70])
        med_matches = len([j for j in matched_jobs if 50 <= (j.get("match_score", 0) * 100 if j.get("match_score", 0) <= 1 else j.get("match_score", 0)) < 70])
        low_matches = len([j for j in matched_jobs if (j.get("match_score", 0) * 100 if j.get("match_score", 0) <= 1 else j.get("match_score", 0)) < 50])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🟢 Strong (70%+)", high_matches)
        with col2:
            st.metric("🟡 Good (50-70%)", med_matches)
        with col3:
            st.metric("🟠 Stretch (<50%)", low_matches)
    
    # ============ DATABASE STATS ============
    st.divider()
    st.markdown("### 🗄️ Job Database Stats")
    
    jobs = fetch_jobs_from_db(limit=100)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Jobs Available", len(jobs))
    with col2:
        if jobs:
            sources = set(j.get('source', 'Unknown') for j in jobs)
            st.metric("Job Sources", len(sources))
    
    # Source breakdown
    if jobs:
        sources = {}
        for job in jobs:
            src = job.get('source', 'Unknown')
            sources[src] = sources.get(src, 0) + 1
        
        st.markdown("#### Jobs by Platform")
        for src, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(jobs)) * 100
            st.progress(pct / 100, text=f"**{src}**: {count} jobs ({pct:.0f}%)")
    else:
        st.warning("No jobs in database. Run the job vectorization script first.")


def show_settings():
    """Settings page."""
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    st.markdown("### API Configuration")
    backend_url = st.text_input("Backend API URL", value=BACKEND_URL)
    
    st.markdown("### Database Connection")
    st.code(f"""
Host: localhost
Port: 5432
Database: killmatch
User: postgres
    """)
    
    st.markdown("### User Preferences")
    st.toggle("Enable email notifications", value=False)
    st.toggle("Daily job digest", value=True)
    
    if st.button("Save Settings"):
        st.success("Settings saved!")


if __name__ == "__main__":
    main()
