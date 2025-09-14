from cv_agent.state import CVCreatorState
from cv_agent.clients import is_clients_initialized


def should_continue(state: CVCreatorState) -> str:
    """Main routing logic - enhanced for better error handling and LLM client checks"""
    
    # Check for errors first
    if state.get("error"):
        return "END"
    
    # Check if LLM clients are initialized for analysis steps
    current_step = state.get("current_step", "")
    analysis_steps = ["upload", "resume_analyzed", "jd_analyzed", "match_analyzed", "cv_generated", "cv_finalized"]
    
    if current_step in analysis_steps and not is_clients_initialized():
        return "END"  # Cannot proceed without LLM clients
    
    # Direct routing based on what's been completed
    if current_step == "upload":
        if state.get("uploaded_resume") and state.get("job_description"):
            return "analyze_resume"
        else:
            return "END"  # Missing required inputs
    
    elif current_step == "resume_analyzed":
        if state.get("resume_analysis"):
            return "analyze_jd"
        else:
            return "END"  # Resume analysis failed
    
    elif current_step == "jd_analyzed":
        if state.get("jd_analysis"):
            return "match_analysis"
        else:
            return "END"  # JD analysis failed
    
    elif current_step == "match_analyzed":
        if state.get("match_analysis"):
            return "generate_cv"
        else:
            return "END"  # Match analysis failed
    
    elif current_step == "cv_generated":
        if state.get("improved_cv"):
            return "apply_feedback"
        else:
            return "END"  # CV generation failed
    
    elif current_step == "cv_finalized":
        if state.get("final_cv"):
            return "final_analysis"
        else:
            return "END"  # CV finalization failed
    
    elif current_step == "analysis_complete":
        return "END"
    
    else:
        # Default case - end the graph
        return "END"


def after_resume_analysis(state: CVCreatorState) -> str:
    """Route after resume analysis with enhanced validation"""
    # Check for errors
    if state.get("error"):
        return "END"
    
    # Check if LLM clients are still available
    if not is_clients_initialized():
        return "END"
    
    # Verify resume analysis was successful
    if not state.get("resume_analysis"):
        return "END"
    
    return "analyze_jd"


def after_jd_analysis(state: CVCreatorState) -> str:
    """Route after job description analysis with enhanced validation"""
    # Check for errors
    if state.get("error"):
        return "END"
    
    # Check if LLM clients are still available
    if not is_clients_initialized():
        return "END"
    
    # Verify JD analysis was successful
    if not state.get("jd_analysis"):
        return "END"
    
    return "match_analysis"


def after_match_analysis(state: CVCreatorState) -> str:
    """Route after match analysis with enhanced validation"""
    # Check for errors
    if state.get("error"):
        return "END"
    
    # Check if LLM clients are still available
    if not is_clients_initialized():
        return "END"
    
    # Verify match analysis was successful and has required data
    match_analysis = state.get("match_analysis")
    if not match_analysis or not state.get("match_percentage"):
        return "END"
    
    return "generate_cv"


def after_cv_generation(state: CVCreatorState) -> str:
    """Route after CV generation with enhanced validation"""
    # Check for errors
    if state.get("error"):
        return "END"
    
    # Check if LLM clients are still available
    if not is_clients_initialized():
        return "END"
    
    # Verify CV generation was successful
    if not state.get("improved_cv"):
        return "END"
    
    return "apply_feedback"


def after_feedback_application(state: CVCreatorState) -> str:
    """Route after applying feedback with enhanced validation"""
    # Check for errors
    if state.get("error"):
        return "END"
    
    # Check if LLM clients are still available for final analysis
    if not is_clients_initialized():
        return "END"
    
    # Verify feedback application was successful
    if not state.get("final_cv"):
        return "END"
    
    return "final_analysis"


def after_final_analysis(state: CVCreatorState) -> str:
    """Route after final analysis - always end"""
    # Always end after final analysis, even if there were issues
    # The final analysis should have set appropriate error states if needed
    return "END"


def validate_state_for_step(state: CVCreatorState, step: str) -> bool:
    """Validate that the state has the required data for a given step"""
    
    validations = {
        "analyze_resume": lambda s: bool(s.get("uploaded_resume")),
        "analyze_jd": lambda s: bool(s.get("job_description") and s.get("resume_analysis")),
        "match_analysis": lambda s: bool(s.get("resume_analysis") and s.get("jd_analysis")),
        "generate_cv": lambda s: bool(s.get("match_analysis") and s.get("resume_analysis") and s.get("jd_analysis")),
        "apply_feedback": lambda s: bool(s.get("improved_cv")),
        "final_analysis": lambda s: bool(s.get("final_cv") and s.get("jd_analysis"))
    }
    
    validator = validations.get(step)
    if validator:
        return validator(state)
    
    return True  # Default to valid for unknown steps


def get_next_step(current_step: str) -> str:
    """Get the expected next step in the workflow"""
    
    step_sequence = [
        "upload",
        "analyze_resume", 
        "analyze_jd",
        "match_analysis",
        "generate_cv",
        "apply_feedback",
        "final_analysis",
        "analysis_complete"
    ]
    
    try:
        current_index = step_sequence.index(current_step)
        if current_index < len(step_sequence) - 1:
            return step_sequence[current_index + 1]
    except ValueError:
        pass  # Current step not in sequence
    
    return "END"


def can_skip_step(state: CVCreatorState, step: str) -> bool:
    """Determine if a step can be skipped based on state"""
    
    # User feedback can be skipped if no feedback provided
    if step == "apply_feedback":
        return not bool(state.get("user_feedback"))
    
    # Other steps generally cannot be skipped
    return False