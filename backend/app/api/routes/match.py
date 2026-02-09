"""
Match Route

Trigger the agent pipeline for job-resume matching.
"""

from typing import List, Optional
import json
import os
import uuid
import httpx

from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from pydantic import BaseModel

from app.services.resume_parser import parse_resume, extract_skills
from app.services.s3_storage import upload_resume, upload_parsed_resume
from app.models import JobMatch
from pinecone import Pinecone
from openai import OpenAI

# GitHub MCP Server URL
GITHUB_MCP_URL = os.getenv("MCP_GITHUB_SERVER_URL", "http://mcp-github:8001")

router = APIRouter()

# Initialize clients
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME", "killmatch-jobs")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_embedding(text: str) -> List[float]:
    """Get embedding for text using OpenAI."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]  # Truncate to avoid token limits
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0.0] * 1536


def extract_skills_with_llm(text: str, max_skills: int = 10) -> List[str]:
    """
    Extract required skills from job description using LLM.
    This is dynamic - no hardcoded skill list needed.
    """
    if not text or len(text.strip()) < 50:
        return []
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical recruiter. Extract the key technical skills, tools, and technologies required for a job. Return ONLY a comma-separated list of skills, nothing else. Focus on: programming languages, frameworks, tools, cloud platforms, databases, and methodologies."
                },
                {
                    "role": "user", 
                    "content": f"Extract the top {max_skills} required skills from this job description:\n\n{text[:2000]}"
                }
            ],
            temperature=0,
            max_tokens=200
        )
        
        skills_text = response.choices[0].message.content.strip()
        # Parse comma-separated list
        skills = [s.strip() for s in skills_text.split(",") if s.strip()]
        return skills[:max_skills]
        
    except Exception as e:
        print(f"LLM skill extraction failed: {e}")
        return []


@router.post("/match")
async def match_jobs(
    query: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    level: Optional[str] = Form(None),
    github_username: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
):
    """
    Match jobs using semantic search + fields.
    
    1. Parse resume (if provided)
    2. Create embedding from resume + query
    3. Query Pinecone for semantic matches
    4. Return ranked jobs with skill gaps
    """
    try:
        # 1. Parse Resume
        resume_text = ""
        skills = []
        
        if resume:
            if not resume.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Only PDF resumes are supported")
            
            content = await resume.read()
            
            # Upload to S3 for persistent storage
            user_id = str(uuid.uuid4())[:8]  # Generate temporary user ID
            s3_result = await upload_resume(
                user_id=user_id,
                file_content=content,
                filename=resume.filename,
                content_type="application/pdf"
            )
            if s3_result.get("success"):
                print(f"✅ Resume uploaded to S3: {s3_result.get('s3_key')}")
            else:
                print(f"⚠️ S3 upload failed (continuing without): {s3_result.get('error', 'Unknown error')}")
            
            # Use our existing service to parse (returns ResumeData model)
            resume_data = await parse_resume(content)
            
            # Upload parsed data to S3 as well
            if s3_result.get("success"):
                parsed_s3 = await upload_parsed_resume(
                    user_id=user_id,
                    parsed_data=resume_data.model_dump() if hasattr(resume_data, 'model_dump') else {}
                )
                if parsed_s3.get("success"):
                    print(f"✅ Parsed resume saved to S3: {parsed_s3.get('s3_key')}")
            
            # Extract text for embedding - skills are Skill objects, extract names
            skill_names = [s.name if hasattr(s, 'name') else str(s) for s in (resume_data.skills or [])]
            resume_text = f"{resume_data.summary or ''} {' '.join(skill_names)} "
            for exp in resume_data.experience or []:
                resume_text += f"{exp.title} {exp.company} {exp.description or ''} "
            
            skills = skill_names  # Use string skill names, not Skill objects
        
        # 2. Fetch GitHub profile for additional context
        github_context = ""
        if github_username:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{GITHUB_MCP_URL}/tools/get_user_repos",
                        json={"username": github_username}
                    )
                    if response.status_code == 200:
                        github_data = response.json()
                        repos = github_data.get("repos", [])[:5]  # Top 5 repos
                        languages = set()
                        topics = set()
                        for repo in repos:
                            if repo.get("language"):
                                languages.add(repo["language"])
                            topics.update(repo.get("topics", []))
                        
                        github_context = f" GitHub skills: {', '.join(languages)}. "
                        github_context += f"Projects: {', '.join(topics)}. "
                        print(f"✅ GitHub profile fetched for {github_username}: {len(repos)} repos")
            except Exception as e:
                print(f"⚠️ GitHub fetch failed (continuing without): {e}")
        
        # 3. Create Embedding Context
        # Combine user query with resume text and GitHub context
        search_context = f"{query or ''} {level or ''} {location or ''}"
        if resume_text:
            search_context += f" Skills: {', '.join(skills[:20])}. Experience: {resume_text[:1000]}"
        if github_context:
            search_context += github_context
            
        print(f"Generating embedding for context depth: {len(search_context)}")
        
        # Get embedding vector
        query_vector = get_embedding(search_context)
        
        # 3. Query Pinecone
        search_results = index.query(
            vector=query_vector,
            top_k=10,
            include_metadata=True
        )
        
        matches = []
        for match in search_results.matches:
            # Extract job data from metadata
            metadata = match.metadata or {}
            
            # Basic validation to ensure we have required fields
            if not metadata.get("title"):
                continue
            
            job_description = metadata.get("description", "") or ""
            job_title = metadata.get("title", "")
            
            # Use LLM to extract required skills from job (dynamic, not hardcoded)
            # Combine title and description for better extraction
            full_job_text = f"{job_title}\n\n{job_description}"
            job_skills = set(extract_skills_with_llm(full_job_text, max_skills=10))
            
            # Get user's skills (already strings)
            resume_skills_lower = set(s.lower() for s in skills if s)
            job_skills_lower = set(s.lower() for s in job_skills if s)
            
            # Calculate gaps (case-insensitive comparison)
            missing_skills_lower = job_skills_lower - resume_skills_lower
            
            # Get original casing for display
            missing_skills = [s for s in job_skills if s.lower() in missing_skills_lower][:5]
                
            job_match = {
                "id": str(metadata.get("job_id", match.id)),
                "title": metadata.get("title", "Unknown Role"),
                "company": metadata.get("company", "Unknown Company"),
                "description": job_description,
                "url": metadata.get("url", ""),
                "source": metadata.get("source", "LinkedIn"),
                "match_score": match.score,  # Cosine similarity (0-1)
                "recruiter_concerns": [], 
                "coach_highlights": [],
                "missing_skills": missing_skills, 
            }
            matches.append(job_match)
            
        return {"matches": matches, "count": len(matches)}
        
    except Exception as e:
        print(f"Error in match_jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
