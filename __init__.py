# cv_agent/__init__.py
"""
AI CV Creator Agent - Enhanced Version

A LangGraph-based application that analyzes resumes against job descriptions
and generates improved, ATS-compliant CVs with comprehensive features.

Enhanced Features:
- Multi-LLM support (OpenAI GPT-4, Google Gemini)
- ATS compliance scoring and analysis
- Comprehensive gap analysis with severity levels
- Change tracking and highlighting
- User feedback integration
- Multiple export formats (PDF, DOCX, TXT)
- Robust document parsing with multiple PDF engines
"""

__version__ = "2.0.0"
__author__ = "AI CV Creator Agent Team"
__description__ = "Transform your resume to match job descriptions with AI-powered analysis and multi-LLM support"

# tests/__init__.py
"""Test package for Enhanced CV Creator Agent"""

# tests/test_nodes.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from cv_agent.nodes import (
    analyze_resume_node,
    analyze_job_description_node,
    match_analysis_node,
    generate_improved_cv_node,
    apply_user_feedback_node,
    final_analysis_node
)
from cv_agent.state import CVCreatorState


class TestEnhancedNodes:
    
    def test_analyze_resume_node_no_resume(self):
        """Test resume analysis node with no resume"""
        state = CVCreatorState(messages=[])
        result = analyze_resume_node(state)
        assert "error" in result
        assert "No resume uploaded" in result["error"]
    
    def test_analyze_resume_node_no_llm_client(self):
        """Test resume analysis node with no LLM client configured"""
        state = CVCreatorState(
            messages=[],
            uploaded_resume="John Doe\nSoftware Engineer with 5 years experience..."
        )
        
        with patch('cv_agent.nodes.is_clients_initialized', return_value=False):
            result = analyze_resume_node(state)
            assert "error" in result
            assert "LLM clients not initialized" in result["error"]
    
    @patch('cv_agent.nodes.is_clients_initialized')
    @patch('cv_agent.nodes.get_client_analyzer')
    @patch('cv_agent.document_parser.DocumentParser.calculate_ats_compliance_score')
    def test_analyze_resume_node_success(self, mock_ats_score, mock_client_func, mock_initialized):
        """Test successful resume analysis with enhanced features"""
        # Setup mocks
        mock_initialized.return_value = True
        mock_client = Mock()
        mock_client_func.return_value = mock_client
        
        # Mock ATS compliance score
        mock_ats_score.return_value = {
            "score": 75,
            "feedback": ["Add more action verbs", "Include contact information"]
        }
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '''{
            "personal_info": {"name": "John Doe", "email": "john@example.com"},
            "professional_summary": "Experienced Software Engineer",
            "experience": [{"company": "TechCorp", "position": "Software Engineer"}],
            "education": [{"institution": "Tech University", "degree": "BS Computer Science"}],
            "skills": {
                "technical": ["Python", "JavaScript"], 
                "programming_languages": ["Python", "Java"],
                "frameworks": ["Django", "React"],
                "tools": ["Git", "Docker"],
                "soft": ["Leadership", "Communication"]
            },
            "certifications": [],
            "projects": [],
            "total_experience_years": "5",
            "key_keywords": ["Python", "Software", "Engineering"],
            "resume_format_analysis": {
                "has_summary": true,
                "has_quantified_achievements": false,
                "uses_action_verbs": true,
                "contact_info_complete": true,
                "length_appropriate": true
            }
        }'''
        mock_client.invoke.return_value = mock_response
        
        state = CVCreatorState(
            messages=[],
            uploaded_resume="John Doe\nSoftware Engineer with 5 years experience..."
        )
        
        result = analyze_resume_node(state)
        
        # Assertions for enhanced features
        assert "resume_analysis" in result
        assert "ats_compliance_score" in result
        assert "ats_feedback" in result
        assert result["current_step"] == "resume_analyzed"
        assert result["ats_compliance_score"] == 75
        assert result["resume_analysis"]["personal_info"]["name"] == "John Doe"
        assert "programming_languages" in result["resume_analysis"]["skills"]
    
    @patch('cv_agent.nodes.is_clients_initialized')
    @patch('cv_agent.nodes.get_client_analyzer')
    def test_analyze_job_description_node_success(self, mock_client_func, mock_initialized):
        """Test successful job description analysis with enhanced structure"""
        # Setup mocks
        mock_initialized.return_value = True
        mock_client = Mock()
        mock_client_func.return_value = mock_client
        
        # Mock LLM response with enhanced structure
        mock_response = Mock()
        mock_response.content = '''{
            "job_title": "Senior Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "employment_type": "Full-time",
            "required_skills": {
                "technical": ["Python", "Django", "REST APIs"], 
                "programming_languages": ["Python", "JavaScript"],
                "frameworks": ["Django", "React"],
                "tools": ["Git", "Docker", "AWS"],
                "databases": ["PostgreSQL", "Redis"],
                "cloud_platforms": ["AWS"],
                "soft_skills": ["Leadership", "Communication"]
            },
            "preferred_skills": {
                "technical": ["Machine Learning", "Kubernetes"],
                "programming_languages": ["Go"],
                "frameworks": ["FastAPI"],
                "tools": ["Terraform"],
                "soft_skills": ["Mentoring"]
            },
            "experience_required": {
                "minimum_years": "5",
                "preferred_years": "7",
                "specific_experience": ["API development", "Team leadership"],
                "industry_experience": ["Fintech", "SaaS"],
                "leadership_experience": "2+ years"
            },
            "education_requirements": {
                "minimum_degree": "Bachelor",
                "preferred_degree": "Master",
                "fields": ["Computer Science", "Engineering"],
                "alternative_experience": "8+ years experience can substitute"
            },
            "certifications": [
                {"name": "AWS Solutions Architect", "required": false, "preferred": true}
            ],
            "important_keywords": ["Python", "Django", "REST", "API", "Leadership"],
            "deal_breakers": ["Less than 5 years experience", "No Python experience"],
            "company_culture": "Fast-paced startup environment"
        }'''
        mock_client.invoke.return_value = mock_response
        
        state = CVCreatorState(
            messages=[],
            job_description="Senior Software Engineer position requiring Python and Django..."
        )
        
        result = analyze_job_description_node(state)
        
        assert "jd_analysis" in result
        assert result["current_step"] == "jd_analyzed"
        assert result["jd_analysis"]["job_title"] == "Senior Software Engineer"
        assert "programming_languages" in result["jd_analysis"]["required_skills"]
        assert "deal_breakers" in result["jd_analysis"]
    
    @patch('cv_agent.nodes.is_clients_initialized')
    @patch('cv_agent.nodes.get_client_analyzer')
    def test_match_analysis_node_success(self, mock_client_func, mock_initialized):
        """Test successful match analysis with enhanced gap analysis"""
        # Setup mocks
        mock_initialized.return_value = True
        mock_client = Mock()
        mock_client_func.return_value = mock_client
        
        # Mock enhanced match analysis response
        mock_response = Mock()
        mock_response.content = '''{
            "overall_match_percentage": 82.5,
            "detailed_skill_match": {
                "technical_skills": {
                    "matched": ["Python", "Git"],
                    "missing": ["Django", "REST APIs"],
                    "match_percentage": 60.0
                },
                "programming_languages": {
                    "matched": ["Python"],
                    "missing": ["JavaScript"],
                    "match_percentage": 50.0
                }
            },
            "gaps_identified": [
                {
                    "category": "Technical Skills",
                    "gap": "Missing Django framework experience",
                    "severity": "High",
                    "addressable": true,
                    "suggestions": ["Highlight any web development projects", "Mention similar frameworks"]
                },
                {
                    "category": "Experience",
                    "gap": "Leadership experience not clearly demonstrated",
                    "severity": "Medium", 
                    "addressable": true,
                    "suggestions": ["Highlight team projects", "Mention mentoring activities"]
                }
            ],
            "strengths_identified": [
                {
                    "category": "Technical Skills",
                    "strength": "Strong Python programming background",
                    "value": "Directly matches core requirement",
                    "leverage_suggestion": "Emphasize Python projects prominently"
                }
            ],
            "recommendations": [
                {
                    "type": "Content Addition",
                    "priority": "High",
                    "description": "Add Django-related projects or experience",
                    "section": "Experience or Projects"
                }
            ]
        }'''
        mock_client.invoke.return_value = mock_response
        
        state = CVCreatorState(
            messages=[],
            resume_analysis={"personal_info": {"name": "John Doe"}},
            jd_analysis={"job_title": "Senior Software Engineer"}
        )
        
        result = match_analysis_node(state)
        
        # Test enhanced match analysis results
        assert "match_analysis" in result
        assert "gap_details" in result
        assert "strengths" in result
        assert "recommendations" in result
        assert result["current_step"] == "match_analyzed"
        assert result["match_percentage"] == 82.5
        assert len(result["gap_details"]) == 2
        assert result["gap_details"][0]["severity"] == "High"
        assert len(result["strengths"]) == 1
        assert len(result["recommendations"]) == 1
    
    @patch('cv_agent.nodes.is_clients_initialized')
    @patch('cv_agent.nodes.get_client_generator')
    def test_generate_improved_cv_node_success(self, mock_client_func, mock_initialized):
        """Test CV generation with change tracking"""
        # Setup mocks
        mock_initialized.return_value = True
        mock_client = Mock()
        mock_client_func.return_value = mock_client
        
        # Mock CV generation response with change tracking
        mock_response = Mock()
        mock_response.content = '''{
            "improved_resume_text": "JOHN DOE\\nSoftware Engineer\\n\\nEXPERIENCE\\n• Developed web applications using Python and Django...",
            "changes_made": [
                {
                    "section": "Summary",
                    "change_type": "Enhanced",
                    "original": "Software Engineer",
                    "improved": "Full-Stack Software Engineer with Django expertise",
                    "reason": "Added Django keyword and clarified full-stack capabilities",
                    "addresses_gap": "Missing Django framework experience"
                },
                {
                    "section": "Experience",
                    "change_type": "Added",
                    "original": "N/A",
                    "improved": "Led team of 3 developers on API development project",
                    "reason": "Added leadership experience to address gap",
                    "addresses_gap": "Leadership experience not clearly demonstrated"
                }
            ],
            "keywords_added": ["Django", "REST API", "Team Leadership"],
            "ats_improvements": [
                "Added missing technical keywords",
                "Enhanced job titles with relevant technologies",
                "Improved bullet point formatting"
            ]
        }'''
        mock_client.invoke.return_value = mock_response
        
        state = CVCreatorState(
            messages=[],
            resume_analysis={"personal_info": {"name": "John Doe"}},
            jd_analysis={"job_title": "Senior Software Engineer"},
            match_analysis={"gaps_identified": ["Missing Django", "No leadership"]}
        )
        
        result = generate_improved_cv_node(state)
        
        # Test change tracking features
        assert "improved_cv" in result
        assert "changes_made" in result
        assert "keywords_added" in result
        assert "ats_improvements" in result
        assert result["current_step"] == "cv_generated"
        assert len(result["changes_made"]) == 2
        assert result["changes_made"][0]["addresses_gap"] == "Missing Django framework experience"
        assert "Django" in result["keywords_added"]


if __name__ == "__main__":
    pytest.main([__file__])