from typing import Annotated, Optional, Dict, List, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage

# For newer versions of LangGraph, we may need to import add_messages differently
try:
    from langgraph.graph.message import add_messages
except ImportError:
    from langgraph.graph import add_messages


class CVCreatorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Document uploads
    uploaded_resume: Optional[str]  # Resume content as text
    job_description: Optional[str]  # JD content as text
    
    # Analysis results
    resume_analysis: Optional[Dict[str, Any]]  # Structured resume data
    jd_analysis: Optional[Dict[str, Any]]  # Structured JD requirements
    match_analysis: Optional[Dict[str, Any]]  # Match score and gaps
    
    # CV Generation
    improved_cv: Optional[str]  # Generated improved CV content
    final_cv: Optional[str]  # Final CV after user feedback
    user_feedback: Optional[str]  # User modifications/feedback
    
    # Processing state
    current_step: str  # Track which step we're on
    processing: bool  # UI loading state
    error: Optional[str]  # Error messages
    
    # Results for UI
    match_percentage: Optional[float]
    identified_gaps: Optional[List[str]]
    addressed_gaps: Optional[List[str]]
    remaining_gaps: Optional[List[str]]
    
    # Enhanced features - NEW FIELDS NEEDED
    # ATS Compliance
    ats_compliance_score: Optional[int]  # Original ATS score
    final_ats_score: Optional[int]  # Final ATS score after improvements
    ats_improvement: Optional[int]  # ATS score improvement
    ats_feedback: Optional[List[str]]  # ATS improvement suggestions
    
    # Detailed Analysis
    gap_details: Optional[List[Dict[str, Any]]]  # Detailed gap analysis with severity
    strengths: Optional[List[Dict[str, Any]]]  # Identified strengths
    recommendations: Optional[List[Dict[str, Any]]]  # Improvement recommendations
    
    # Change Tracking
    changes_made: Optional[List[Dict[str, Any]]]  # Detailed changes made to CV
    keywords_added: Optional[List[str]]  # Keywords added during improvement
    ats_improvements: Optional[List[str]]  # ATS-specific improvements made
    sections_restructured: Optional[List[str]]  # Sections that were reorganized
    
    # User Feedback Integration
    user_feedback_applied: Optional[List[Dict[str, Any]]]  # Feedback changes applied
    feedback_not_applied: Optional[List[Dict[str, Any]]]  # Feedback that couldn't be applied
    user_feedback_text: Optional[str]  # Original user feedback text
    
    # Final Analysis
    final_match_percentage: Optional[float]  # Final match score after all improvements
    improvement_summary: Optional[Dict[str, Any]]  # Summary of all improvements made
    final_analysis: Optional[Dict[str, Any]]  # Comprehensive final analysis