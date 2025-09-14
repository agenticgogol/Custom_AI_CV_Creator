import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from cv_agent.clients import get_client_analyzer, get_client_generator, is_clients_initialized
from cv_agent.state import CVCreatorState
from cv_agent.document_parser import DocumentParser


def analyze_resume_node(state: CVCreatorState) -> Dict[str, Any]:
    """Extract structured information from resume with enhanced analysis"""
    
    if not state.get("uploaded_resume"):
        return {"error": "No resume uploaded"}
    
    if not is_clients_initialized():
        return {"error": "LLM clients not initialized. Please configure API key first."}
    
    # Calculate ATS compliance score
    ats_analysis = DocumentParser.calculate_ats_compliance_score(state["uploaded_resume"])
    
    prompt = f"""
    Analyze the following resume comprehensively and extract structured information in JSON format:
    
    Resume Content:
    {state["uploaded_resume"]}
    
    ATS Compliance Analysis:
    {json.dumps(ats_analysis, indent=2)}
    
    Extract ALL available information in this exact JSON structure. Be comprehensive and don't miss details:
    {{
        "personal_info": {{
            "name": "Full name",
            "email": "email address",
            "phone": "phone number", 
            "location": "city, state/country",
            "linkedin": "LinkedIn profile URL if available",
            "github": "GitHub profile URL if available",
            "website": "Personal website if available"
        }},
        "professional_summary": "Complete professional summary or objective - capture the full text",
        "experience": [
            {{
                "company": "Company name",
                "position": "Complete job title",
                "duration": "Full time period (start - end)",
                "location": "City, State if mentioned",
                "responsibilities": [
                    "Complete bullet point 1 - capture exact text",
                    "Complete bullet point 2 - capture exact text"
                ],
                "achievements": [
                    "Quantified achievement 1 with numbers",
                    "Quantified achievement 2 with numbers"
                ],
                "technologies": ["List of technologies/tools mentioned for this role"]
            }}
        ],
        "education": [
            {{
                "institution": "Full school/university name", 
                "degree": "Complete degree type and field of study",
                "graduation_year": "Year or expected year",
                "location": "City, State if mentioned",
                "gpa": "GPA if mentioned",
                "honors": ["Any honors, magna cum laude, etc."],
                "relevant_coursework": ["Relevant courses if mentioned"]
            }}
        ],
        "skills": {{
            "technical": ["All technical skills - be comprehensive"],
            "programming_languages": ["All programming languages"],
            "frameworks": ["All frameworks and libraries"],
            "tools": ["All tools and software"],
            "databases": ["All databases"],
            "cloud_platforms": ["AWS, Azure, GCP, etc."],
            "soft_skills": ["All soft skills mentioned"],
            "languages": ["Spoken languages if mentioned"]
        }},
        "certifications": [
            {{
                "name": "Full certification name",
                "issuer": "Issuing organization",
                "date": "Date obtained",
                "expiry": "Expiry date if mentioned"
            }}
        ],
        "projects": [
            {{
                "name": "Project name",
                "description": "Complete project description",
                "technologies": ["Technologies used"],
                "duration": "Project duration if mentioned",
                "url": "Project URL if available",
                "achievements": ["Project achievements with metrics"]
            }}
        ],
        "awards": ["All awards and recognitions"],
        "publications": ["Any publications mentioned"],
        "volunteer_experience": [
            {{
                "organization": "Organization name",
                "role": "Volunteer role",
                "duration": "Time period",
                "description": "What they did"
            }}
        ],
        "total_experience_years": "Calculate total years of professional experience",
        "key_industries": ["Industries they have worked in"],
        "key_keywords": ["ALL important keywords from the resume - be comprehensive"],
        "resume_format_analysis": {{
            "has_summary": true/false,
            "has_quantified_achievements": true/false,
            "uses_action_verbs": true/false,
            "contact_info_complete": true/false,
            "length_appropriate": true/false
        }}
    }}
    
    IMPORTANT: 
    - Be extremely thorough and capture ALL information present
    - Don't summarize or paraphrase - extract complete text
    - Include all skills, technologies, and keywords mentioned
    - Capture exact bullet points and achievements
    - Don't miss any sections or details
    
    Only return valid JSON, no additional text.
    """
    
    try:
        client = get_client_analyzer()
        response = client.invoke([
            SystemMessage(content="You are an expert resume parser. Extract ALL information comprehensively. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        # Clean the response and parse JSON
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        resume_analysis = json.loads(content)
        
        return {
            "resume_analysis": resume_analysis,
            "ats_compliance_score": ats_analysis["score"],
            "ats_feedback": ats_analysis["feedback"],
            "current_step": "resume_analyzed"
        }
        
    except Exception as e:
        return {"error": f"Error analyzing resume: {str(e)}"}


def analyze_job_description_node(state: CVCreatorState) -> Dict[str, Any]:
    """Extract comprehensive requirements from job description"""
    
    if not state.get("job_description"):
        return {"error": "No job description provided"}
    
    if not is_clients_initialized():
        return {"error": "LLM clients not initialized. Please configure API key first."}
    
    prompt = f"""
    Analyze the following job description comprehensively and extract ALL requirements in JSON format:
    
    Job Description:
    {state["job_description"]}
    
    Extract the following information in this exact JSON structure. Be extremely thorough:
    {{
        "job_title": "Complete position title",
        "company": "Company name (if mentioned)",
        "location": "Job location",
        "employment_type": "Full-time/Part-time/Contract/etc.",
        "salary_range": "Salary information if mentioned",
        "required_skills": {{
            "technical": ["ALL required technical skills"],
            "programming_languages": ["Required programming languages"],
            "frameworks": ["Required frameworks and libraries"],
            "tools": ["Required tools and software"],
            "databases": ["Required databases"],
            "cloud_platforms": ["Required cloud platforms"],
            "soft_skills": ["Required soft skills"],
            "languages": ["Required spoken languages"]
        }},
        "preferred_skills": {{
            "technical": ["ALL preferred technical skills"],
            "programming_languages": ["Preferred programming languages"],
            "frameworks": ["Preferred frameworks and libraries"],
            "tools": ["Preferred tools and software"],
            "databases": ["Preferred databases"],
            "cloud_platforms": ["Preferred cloud platforms"],
            "soft_skills": ["Preferred soft skills"],
            "languages": ["Preferred spoken languages"]
        }},
        "experience_required": {{
            "minimum_years": "Minimum years required",
            "preferred_years": "Preferred years",
            "specific_experience": [
                "Specific type of experience 1",
                "Specific type of experience 2"
            ],
            "industry_experience": ["Preferred industries"],
            "leadership_experience": "Leadership requirements if any"
        }},
        "education_requirements": {{
            "minimum_degree": "Minimum degree required",
            "preferred_degree": "Preferred degree level",
            "fields": ["Relevant fields of study"],
            "alternative_experience": "Can experience substitute for degree?"
        }},
        "certifications": [
            {{
                "name": "Certification name",
                "required": true/false,
                "preferred": true/false
            }}
        ],
        "key_responsibilities": [
            "Complete responsibility 1",
            "Complete responsibility 2"
        ],
        "success_metrics": ["How success will be measured"],
        "team_structure": "Team information if mentioned",
        "reporting_structure": "Who they'll report to",
        "important_keywords": [
            "ALL critical keywords that should appear in resume"
        ],
        "deal_breakers": [
            "Absolute requirements that cannot be compromised"
        ],
        "nice_to_have": [
            "Skills/experience that would be a bonus"
        ],
        "company_culture": "Company culture and values",
        "benefits": ["Benefits mentioned if any"],
        "growth_opportunities": "Career growth information if mentioned"
    }}
    
    IMPORTANT: Be extremely comprehensive and extract ALL requirements, both explicit and implicit.
    
    Only return valid JSON, no additional text.
    """
    
    try:
        client = get_client_analyzer()
        response = client.invoke([
            SystemMessage(content="You are an expert job description analyzer. Extract ALL requirements comprehensively. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        # Clean the response and parse JSON
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        jd_analysis = json.loads(content)
        
        return {
            "jd_analysis": jd_analysis,
            "current_step": "jd_analyzed"
        }
        
    except Exception as e:
        return {"error": f"Error analyzing job description: {str(e)}"}


def match_analysis_node(state: CVCreatorState) -> Dict[str, Any]:
    """Comprehensive match analysis between resume and job description"""
    
    if not state.get("resume_analysis") or not state.get("jd_analysis"):
        return {"error": "Both resume and job description must be analyzed first"}
    
    if not is_clients_initialized():
        return {"error": "LLM clients not initialized. Please configure API key first."}
    
    prompt = f"""
    Perform a comprehensive match analysis between the resume and job requirements:
    
    RESUME ANALYSIS:
    {json.dumps(state["resume_analysis"], indent=2)}
    
    JOB REQUIREMENTS:
    {json.dumps(state["jd_analysis"], indent=2)}
    
    Provide detailed analysis in this exact JSON structure:
    {{
        "overall_match_percentage": 85.5,
        "detailed_skill_match": {{
            "technical_skills": {{
                "matched": ["Skills present in both resume and JD"],
                "missing": ["Technical skills required but not in resume"],
                "additional": ["Skills in resume but not required"],
                "match_percentage": 75.0
            }},
            "programming_languages": {{
                "matched": ["Languages present in both"],
                "missing": ["Required languages not in resume"],
                "additional": ["Languages in resume but not required"],
                "match_percentage": 80.0
            }},
            "frameworks_tools": {{
                "matched": ["Frameworks/tools present in both"],
                "missing": ["Required frameworks/tools not in resume"],
                "additional": ["Frameworks/tools in resume but not required"],
                "match_percentage": 70.0
            }},
            "soft_skills": {{
                "matched": ["Soft skills present in both"],
                "missing": ["Required soft skills not clearly demonstrated"],
                "match_percentage": 85.0
            }}
        }},
        "experience_analysis": {{
            "years_match": true/false,
            "total_years_candidate": "X years",
            "total_years_required": "Y years",
            "years_gap": "Gap in years if any",
            "industry_match": {{
                "relevant_industries": ["Industries in common"],
                "missing_industries": ["Required industries not in resume"],
                "match_percentage": 90.0
            }},
            "role_level_match": {{
                "current_level": "Junior/Mid/Senior/Lead",
                "required_level": "Junior/Mid/Senior/Lead", 
                "match": true/false
            }},
            "specific_experience_match": {{
                "matched": ["Specific experiences that align"],
                "missing": ["Required experiences not demonstrated"],
                "match_percentage": 75.0
            }}
        }},
        "education_analysis": {{
            "degree_match": {{
                "candidate_degree": "Highest degree",
                "required_degree": "Required degree",
                "meets_minimum": true/false,
                "exceeds_requirement": true/false
            }},
            "field_match": {{
                "candidate_field": "Field of study",
                "required_fields": ["Required fields"],
                "relevant": true/false
            }},
            "alternative_qualifications": "Can experience substitute for education?"
        }},
        "keyword_analysis": {{
            "total_keywords": 50,
            "matched_keywords": ["List of matched important keywords"],
            "missing_critical_keywords": ["Critical keywords not in resume"],
            "missing_preferred_keywords": ["Preferred keywords not in resume"],
            "keyword_density_score": 75.0,
            "ats_keyword_optimization": "Assessment of keyword usage for ATS"
        }},
        "certification_analysis": {{
            "required_certifications": {{
                "matched": ["Required certs candidate has"],
                "missing": ["Required certs candidate lacks"]
            }},
            "preferred_certifications": {{
                "matched": ["Preferred certs candidate has"],
                "missing": ["Preferred certs candidate lacks"]
            }},
            "additional_certifications": ["Extra certs that add value"]
        }},
        "gaps_identified": [
            {{
                "category": "Technical Skills",
                "gap": "Missing Python programming skills",
                "severity": "Critical/High/Medium/Low",
                "addressable": true/false,
                "suggestions": ["How to address this gap"]
            }},
            {{
                "category": "Experience", 
                "gap": "Needs 2 more years of ML experience",
                "severity": "High",
                "addressable": false,
                "suggestions": ["How to mitigate this gap"]
            }}
        ],
        "strengths_identified": [
            {{
                "category": "Technical Skills",
                "strength": "Strong Java programming background", 
                "value": "Directly matches core requirement",
                "leverage_suggestion": "Highlight Java projects prominently"
            }}
        ],
        "recommendations": [
            {{
                "type": "Content Addition",
                "priority": "High",
                "description": "Add specific Python projects to demonstrate proficiency",
                "section": "Projects or Experience"
            }},
            {{
                "type": "Keyword Optimization",
                "priority": "Medium", 
                "description": "Include more cloud computing terminology",
                "section": "Skills or Summary"
            }},
            {{
                "type": "Formatting",
                "priority": "Low",
                "description": "Use more action verbs in experience bullets",
                "section": "Experience"
            }}
        ],
        "match_score_breakdown": {{
            "skills_weight": 40,
            "experience_weight": 30,
            "education_weight": 15,
            "keywords_weight": 15,
            "skills_score": 75.0,
            "experience_score": 80.0,
            "education_score": 100.0,
            "keywords_score": 70.0
        }},
        "ats_compatibility": {{
            "current_score": 75,
            "improvements_needed": ["Specific ATS improvements"],
            "keyword_optimization": "Assessment of keyword strategy"
        }},
        "competitive_analysis": {{
            "candidate_positioning": "How candidate compares to typical applicants",
            "standout_factors": ["What makes candidate unique"],
            "areas_for_improvement": ["Where candidate falls behind"]
        }}
    }}
    
    IMPORTANT: 
    - Be extremely thorough in identifying gaps and strengths
    - Provide specific, actionable recommendations
    - Calculate match percentages based on actual overlap
    - Consider both explicit and implicit requirements
    
    Only return valid JSON, no additional text.
    """
    
    try:
        client = get_client_analyzer()
        response = client.invoke([
            SystemMessage(content="You are an expert at matching resumes to job requirements. Provide comprehensive analysis. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        # Clean the response and parse JSON
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        match_analysis = json.loads(content)
        
        return {
            "match_analysis": match_analysis,
            "match_percentage": match_analysis.get("overall_match_percentage", 0),
            "identified_gaps": [gap["gap"] for gap in match_analysis.get("gaps_identified", [])],
            "gap_details": match_analysis.get("gaps_identified", []),
            "strengths": match_analysis.get("strengths_identified", []),
            "recommendations": match_analysis.get("recommendations", []),
            "current_step": "match_analyzed"
        }
        
    except Exception as e:
        return {"error": f"Error in match analysis: {str(e)}"}


def generate_improved_cv_node(state: CVCreatorState) -> Dict[str, Any]:
    """Generate an improved CV with detailed change tracking"""
    
    if not all([state.get("resume_analysis"), state.get("jd_analysis"), state.get("match_analysis")]):
        return {"error": "Complete analysis required before CV generation"}
    
    if not is_clients_initialized():
        return {"error": "LLM clients not initialized. Please configure API key first."}
    
    prompt = f"""
    Create an improved, ATS-compliant resume based on the analysis and identified gaps. Track all changes made.
    
    ORIGINAL RESUME:
    {state["uploaded_resume"]}
    
    RESUME ANALYSIS:
    {json.dumps(state["resume_analysis"], indent=2)}
    
    JOB REQUIREMENTS:
    {json.dumps(state["jd_analysis"], indent=2)}
    
    MATCH ANALYSIS & GAPS:
    {json.dumps(state["match_analysis"], indent=2)}
    
    Create an improved resume that addresses the gaps while maintaining truthfulness. Return your response as a JSON object with this structure:
    
    {{
        "improved_resume_text": "The complete improved resume in plain text format",
        "changes_made": [
            {{
                "section": "Summary",
                "change_type": "Added/Modified/Restructured/Enhanced",
                "original": "Original text or 'N/A' if new",
                "improved": "New/improved text",
                "reason": "Why this change was made",
                "addresses_gap": "Which gap this addresses"
            }},
            {{
                "section": "Skills",
                "change_type": "Added",
                "original": "N/A",
                "improved": "Added Python, Machine Learning",
                "reason": "Job requires Python and ML skills",
                "addresses_gap": "Missing technical skills"
            }}
        ],
        "keywords_added": ["List of new keywords incorporated"],
        "ats_improvements": [
            "Specific ATS compliance improvements made"
        ],
        "sections_restructured": [
            "Which sections were reorganized and why"
        ]
    }}
    
    Guidelines for improvement:
    1. MAINTAIN TRUTHFULNESS - Only enhance/reorganize existing information
    2. Add missing keywords naturally into existing content
    3. Quantify achievements where possible
    4. Use strong action verbs
    5. Follow ATS-compliant formatting:
       - Standard section headers
       - Bullet points for experience
       - Simple formatting, no tables
       - Consistent date formatting
    6. Address identified gaps creatively but truthfully
    7. Optimize for both ATS and human readers
    
    Return ONLY the JSON object, no additional text.
    """
    
    try:
        client = get_client_generator()
        response = client.invoke([
            SystemMessage(content="You are an expert resume writer. Create improved resumes that track changes and maintain truthfulness. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        # Clean the response and parse JSON
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        cv_result = json.loads(content)
        
        return {
            "improved_cv": cv_result.get("improved_resume_text", ""),
            "changes_made": cv_result.get("changes_made", []),
            "keywords_added": cv_result.get("keywords_added", []),
            "ats_improvements": cv_result.get("ats_improvements", []),
            "sections_restructured": cv_result.get("sections_restructured", []),
            "current_step": "cv_generated"
        }
        
    except Exception as e:
        return {"error": f"Error generating improved CV: {str(e)}"}


def apply_user_feedback_node(state: CVCreatorState) -> Dict[str, Any]:
    """Apply user feedback to the generated CV with change tracking"""
    
    if not state.get("improved_cv"):
        return {"error": "No improved CV to modify"}
    
    if not is_clients_initialized():
        return {"error": "LLM clients not initialized. Please configure API key first."}
    
    # Store user feedback in state
    user_feedback = state.get("user_feedback", "")
    
    if not user_feedback:
        # No feedback provided, use improved CV as final
        return {
            "final_cv": state["improved_cv"],
            "user_feedback_applied": [],
            "current_step": "cv_finalized"
        }
    
    prompt = f"""
    Apply the user's feedback to improve the CV further. Track what changes are made based on feedback.
    
    CURRENT CV:
    {state["improved_cv"]}
    
    USER FEEDBACK:
    {user_feedback}
    
    JOB REQUIREMENTS (for context):
    {json.dumps(state.get("jd_analysis", {}), indent=2)}
    
    ORIGINAL CHANGES MADE:
    {json.dumps(state.get("changes_made", []), indent=2)}
    
    Apply the user's feedback and return a JSON response:
    
    {{
        "final_resume_text": "The updated resume incorporating user feedback",
        "feedback_changes": [
            {{
                "feedback_item": "The specific feedback being addressed",
                "section": "Which section was modified",
                "change_type": "Added/Modified/Removed/Restructured",
                "original": "What was there before",
                "updated": "What it became",
                "reasoning": "Why this change addresses the feedback"
            }}
        ],
        "feedback_not_applied": [
            {{
                "feedback_item": "Feedback that couldn't be applied",
                "reason": "Why it wasn't applied (e.g., would hurt ATS score, not truthful, etc.)"
            }}
        ]
    }}
    
    Guidelines:
    1. Address user feedback while maintaining ATS compliance
    2. Keep all information truthful
    3. Explain why some feedback might not be applied
    4. Maintain professional formatting
    5. Ensure changes align with job requirements
    
    Return ONLY the JSON object.
    """
    
    try:
        client = get_client_generator()
        response = client.invoke([
            SystemMessage(content="You are an expert resume editor. Apply user feedback thoughtfully while maintaining quality. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        # Clean the response and parse JSON
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        feedback_result = json.loads(content)
        
        return {
            "final_cv": feedback_result.get("final_resume_text", state["improved_cv"]),
            "user_feedback_applied": feedback_result.get("feedback_changes", []),
            "feedback_not_applied": feedback_result.get("feedback_not_applied", []),
            "user_feedback_text": user_feedback,  # Store the original feedback
            "current_step": "cv_finalized"
        }
        
    except Exception as e:
        return {"error": f"Error applying user feedback: {str(e)}"}


def final_analysis_node(state: CVCreatorState) -> Dict[str, Any]:
    """Perform comprehensive final analysis of the improved CV"""
    
    if not state.get("final_cv") or not state.get("jd_analysis"):
        return {"error": "Final CV and job analysis required"}
    
    if not is_clients_initialized():
        return {"error": "LLM clients not initialized. Please configure API key first."}
    
    # Calculate new ATS compliance score
    final_ats_analysis = DocumentParser.calculate_ats_compliance_score(state["final_cv"])
    
    prompt = f"""
    Analyze the final CV against job requirements and provide comprehensive improvement analysis:
    
    FINAL CV:
    {state["final_cv"]}
    
    ORIGINAL CV:
    {state["uploaded_resume"]}
    
    JOB REQUIREMENTS:
    {json.dumps(state["jd_analysis"], indent=2)}
    
    ORIGINAL MATCH ANALYSIS:
    {json.dumps(state.get("match_analysis", {}), indent=2)}
    
    CHANGES MADE:
    {json.dumps(state.get("changes_made", []), indent=2)}
    
    USER FEEDBACK APPLIED:
    {json.dumps(state.get("user_feedback_applied", []), indent=2)}
    
    NEW ATS ANALYSIS:
    {json.dumps(final_ats_analysis, indent=2)}
    
    Provide comprehensive final analysis in this JSON structure:
    {{
        "final_match_analysis": {{
            "overall_match_percentage": 92.5,
            "improvement_from_original": 15.5,
            "skill_match_percentage": 85.0,
            "experience_match_percentage": 90.0,
            "keyword_match_percentage": 95.0,
            "education_match_percentage": 100.0
        }},
        "ats_compliance": {{
            "final_score": 88,
            "improvement_from_original": 13,
            "strong_areas": ["Areas where ATS compliance is strong"],
            "areas_for_improvement": ["Remaining ATS issues if any"],
            "keyword_optimization_score": 85
        }},
        "gaps_analysis": {{
            "original_gaps": ["List of original gaps"],
            "gaps_addressed": [
                {{
                    "gap": "Gap that was addressed",
                    "how_addressed": "How it was addressed in the CV",
                    "effectiveness": "High/Medium/Low"
                }}
            ],
            "remaining_gaps": [
                {{
                    "gap": "Gap that still exists", 
                    "reason": "Why it couldn't be addressed",
                    "mitigation": "How it's mitigated in the CV"
                }}
            ]
        }},
        "improvement_summary": {{
            "key_enhancements": [
                "Major improvement 1",
                "Major improvement 2" 
            ],
            "sections_improved": ["Which sections were enhanced"],
            "new_strengths": ["New strengths highlighted"],
            "competitive_advantage": "How this CV now stands out"
        }},
        "recommendations": {{
            "for_application": [
                "How to use this CV effectively",
                "Cover letter focus areas"
            ],
            "for_interview": [
                "Key points to prepare for interview",
                "Stories to develop"
            ],
            "for_further_improvement": [
                "Long-term career development suggestions"
            ]
        }}
    }}
    
    Only return valid JSON, no additional text.
    """
    
    try:
        client = get_client_analyzer()
        response = client.invoke([
            SystemMessage(content="You are an expert at analyzing CV improvements. Provide comprehensive final analysis. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        # Clean the response and parse JSON
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        final_analysis = json.loads(content)
        
        return {
            "final_match_percentage": final_analysis.get("final_match_analysis", {}).get("overall_match_percentage", 0),
            "final_ats_score": final_ats_analysis["score"],
            "ats_improvement": final_ats_analysis["score"] - state.get("ats_compliance_score", 0),
            "addressed_gaps": [gap["gap"] for gap in final_analysis.get("gaps_analysis", {}).get("gaps_addressed", [])],
            "remaining_gaps": [gap["gap"] for gap in final_analysis.get("gaps_analysis", {}).get("remaining_gaps", [])],
            "improvement_summary": final_analysis.get("improvement_summary", {}),
            "final_analysis": final_analysis,
            "current_step": "analysis_complete"
        }
        
    except Exception as e:
        return {"error": f"Error in final analysis: {str(e)}"}