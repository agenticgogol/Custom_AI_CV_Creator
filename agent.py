from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from cv_agent.state import CVCreatorState
from cv_agent.nodes import (
    analyze_resume_node,
    analyze_job_description_node,
    match_analysis_node,
    generate_improved_cv_node,
    apply_user_feedback_node,
    final_analysis_node
)
from cv_agent.edges import (
    should_continue,
    after_resume_analysis,
    after_jd_analysis,
    after_match_analysis,
    after_cv_generation,
    after_feedback_application,
    after_final_analysis
)


def build_cv_agent(local_memory=True):
    """Build the CV Creator Agent using LangGraph"""
    
    # Create the state graph
    workflow = StateGraph(CVCreatorState)
    
    # Add nodes
    workflow.add_node("analyze_resume", analyze_resume_node)
    workflow.add_node("analyze_jd", analyze_job_description_node)
    workflow.add_node("match_analysis", match_analysis_node)
    workflow.add_node("generate_cv", generate_improved_cv_node)
    workflow.add_node("apply_feedback", apply_user_feedback_node)
    workflow.add_node("final_analysis", final_analysis_node)
    
    # Set entry point
    workflow.add_edge(START, "analyze_resume")
    
    # Add deterministic edges between nodes
    workflow.add_conditional_edges(
        "analyze_resume",
        after_resume_analysis,
        {
            "analyze_jd": "analyze_jd",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "analyze_jd",
        after_jd_analysis,
        {
            "match_analysis": "match_analysis",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "match_analysis",
        after_match_analysis,
        {
            "generate_cv": "generate_cv",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "generate_cv",
        after_cv_generation,
        {
            "apply_feedback": "apply_feedback",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "apply_feedback",
        after_feedback_application,
        {
            "final_analysis": "final_analysis",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "final_analysis",
        after_final_analysis,
        {
            "END": END
        }
    )
    
    # Compile the agent with increased recursion limit
    agent = workflow.compile(
        checkpointer=MemorySaver() if local_memory else None
    )
    
    return agent