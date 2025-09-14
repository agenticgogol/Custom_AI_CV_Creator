import os
import asyncio
from typing import Optional, Dict, Any, Literal
from fastapi import FastAPI, Request, UploadFile, File
from langchain_core.messages import HumanMessage
from nicegui import run, ui, app
import json
import logging

from cv_agent.state import CVCreatorState
from cv_agent.document_parser import DocumentParser
from cv_agent.cv_generator import CVGenerator
from cv_agent.clients import initialize_llm_clients, is_clients_initialized, get_current_provider

# Set up logging
logger = logging.getLogger(__name__)

# Global reference to store agent when initialized
_GLOBAL_AGENT = None

def set_global_agent(agent):
    """Set the global agent reference"""
    global _GLOBAL_AGENT
    logger.info(f"Setting global agent ID: {id(agent)}")
    _GLOBAL_AGENT = agent
    logger.info(f"Global agent set successfully. Stored: {type(_GLOBAL_AGENT)}")

def get_global_agent():
    """Get the global agent reference"""
    return _GLOBAL_AGENT


class CVCreatorPageData:
    def __init__(self):
        # LLM Configuration
        self.llm_provider: Optional[Literal["openai", "gemini"]] = None
        self.api_key: Optional[str] = None
        self.llm_configured: bool = False
        
        # Document data
        self.uploaded_resume: Optional[str] = None
        self.job_description: Optional[str] = None
        self.current_step: str = "config"
        self.processing: bool = False
        self.error: Optional[str] = None
        
        # Analysis results
        self.match_percentage: Optional[float] = None
        self.identified_gaps: list = []
        self.addressed_gaps: list = []
        self.remaining_gaps: list = []
        self.gap_details: list = []
        self.strengths: list = []
        self.recommendations: list = []
        
        # ATS scores
        self.original_ats_score: Optional[int] = None
        self.final_ats_score: Optional[int] = None
        self.ats_improvement: Optional[int] = None
        self.ats_feedback: list = []
        
        # CV content and changes
        self.improved_cv: Optional[str] = None
        self.final_cv: Optional[str] = None
        self.user_feedback: Optional[str] = None
        self.changes_made: list = []
        self.keywords_added: list = []
        self.user_feedback_applied: list = []
        
        # UI state
        self.resume_filename: Optional[str] = None
        self.show_analysis_results: bool = False
        self.show_cv_editor: bool = False
        self.show_final_results: bool = False
        
        # Step tracking
        self.steps_completed = {
            "config": False,
            "upload": False,
            "analyze": False,
            "generate": False,
            "review": False,
            "finalize": False
        }


class Refreshables:
    @ui.refreshable
    def llm_config_section(self, page_data: CVCreatorPageData) -> None:
        """LLM API configuration section"""
        if page_data.llm_configured:
            return
            
        with ui.card().classes('w-full max-w-4xl mx-auto mb-4'):
            ui.label('Step 1: Configure AI Provider').classes('text-xl font-bold mb-4')
            ui.markdown("""
            **Choose your preferred AI provider and enter your API key:**
            
            - **OpenAI**: Excellent performance, requires OpenAI API key
            - **Gemini**: Google's latest model, requires Google AI API key
            
            Your API key is only used for this session and is not stored.
            """)
            
            with ui.row().classes('w-full gap-4 items-end'):
                # Provider selection
                with ui.column().classes('flex-1'):
                    ui.label('Select AI Provider').classes('font-semibold')
                    
                    def on_provider_change(e):
                        page_data.llm_provider = e.value
                        self.llm_config_section.refresh(page_data)
                    
                    ui.select(
                        options={'openai': 'OpenAI (GPT-4)', 'gemini': 'Google Gemini'},
                        value=page_data.llm_provider,
                        on_change=on_provider_change
                    ).props('outlined').classes('w-full')
                
                # API key input
                with ui.column().classes('flex-2'):
                    ui.label('API Key').classes('font-semibold')
                    
                    placeholder = {
                        'openai': 'sk-...',
                        'gemini': 'AI...'
                    }.get(page_data.llm_provider, 'Enter your API key')
                    
                    ui.input(
                        placeholder=placeholder,
                        value=page_data.api_key or '',
                        password=True
                    ).bind_value(page_data, 'api_key').props('outlined').classes('w-full')
                
                # Configure button
                async def configure_llm():
                    if not page_data.llm_provider or not page_data.api_key:
                        ui.notify('Please select a provider and enter API key', type='warning')
                        return
                    
                    try:
                        page_data.processing = True
                        self.llm_config_section.refresh(page_data)
                        
                        success = await run.io_bound(
                            initialize_llm_clients, 
                            page_data.llm_provider, 
                            page_data.api_key
                        )
                        
                        if success:
                            page_data.llm_configured = True
                            page_data.current_step = "upload"
                            page_data.steps_completed["config"] = True
                            ui.notify(f'✅ {page_data.llm_provider.title()} configured successfully!', type='positive')
                        else:
                            ui.notify('❌ Failed to configure LLM. Check your API key.', type='negative')
                    
                    except Exception as e:
                        ui.notify(f'Configuration error: {str(e)}', type='negative')
                    finally:
                        page_data.processing = False
                        self.llm_config_section.refresh(page_data)
                        self.upload_section.refresh(page_data)
                
                ui.button(
                    'Configure' if not page_data.processing else 'Configuring...',
                    on_click=configure_llm
                ).props('color=primary').bind_enabled_from(page_data, 'processing', backward=lambda x: not x)
            
            if page_data.llm_provider == 'openai':
                ui.markdown("**Get your OpenAI API key:** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)")
            elif page_data.llm_provider == 'gemini':
                ui.markdown("**Get your Google AI API key:** [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)")
    
    @ui.refreshable
    def upload_section(self, page_data: CVCreatorPageData) -> None:
        """File upload section"""
        if not page_data.llm_configured:
            return
            
        with ui.card().classes('w-full max-w-4xl mx-auto mb-4'):
            ui.label('Step 2: Upload Your Documents').classes('text-xl font-bold mb-4')
            
            with ui.row().classes('w-full gap-4'):
                # Resume upload
                with ui.column().classes('flex-1'):
                    ui.label('Upload Resume (PDF/DOCX/TXT)').classes('font-semibold')
                    
                    async def handle_resume_upload(e):
                        if e.content:
                            try:
                                page_data.processing = True
                                self.upload_section.refresh(page_data)
                                
                                # Parse document
                                text = await run.io_bound(DocumentParser.parse_document, e.content, e.name)
                                
                                if DocumentParser.validate_resume(text):
                                    page_data.uploaded_resume = text
                                    page_data.resume_filename = e.name
                                    page_data.error = None
                                    
                                    # Calculate initial ATS score
                                    ats_analysis = DocumentParser.calculate_ats_compliance_score(text)
                                    page_data.original_ats_score = ats_analysis["score"]
                                    page_data.ats_feedback = ats_analysis["feedback"]
                                    
                                    ui.notify(f'✅ Resume uploaded: {e.name}', type='positive')
                                    ui.notify(f'📊 ATS Compliance Score: {page_data.original_ats_score}/100', type='info')
                                else:
                                    page_data.error = "File doesn't appear to be a valid resume"
                                    ui.notify('❌ Invalid resume format', type='negative')
                            except Exception as ex:
                                page_data.error = str(ex)
                                ui.notify(f'Upload error: {str(ex)}', type='negative')
                            finally:
                                page_data.processing = False
                                self.upload_section.refresh(page_data)
                                self.ats_score_section.refresh(page_data)
                    
                    ui.upload(
                        on_upload=handle_resume_upload,
                        multiple=False,
                        max_file_size=10_000_000
                    ).props('accept=".pdf,.docx,.doc,.txt" outlined').classes('w-full')
                    
                    if page_data.resume_filename:
                        ui.label(f'✅ {page_data.resume_filename}').classes('text-green-600 mt-2')
                
                # Job description input
                with ui.column().classes('flex-1'):
                    ui.label('Job Description').classes('font-semibold')
                    
                    def handle_jd_change():
                        if page_data.job_description and DocumentParser.validate_job_description(page_data.job_description):
                            ui.notify('✅ Job description validated', type='positive')
                        elif page_data.job_description:
                            ui.notify('⚠️ Please enter a complete job description', type='warning')
                    
                    ui.textarea(
                        placeholder='Paste the complete job description here...',
                        value=page_data.job_description or ''
                    ).bind_value(page_data, 'job_description').props(
                        'outlined rows=8'
                    ).classes('w-full').on('blur', handle_jd_change)
            
            # Analysis button
            with ui.row().classes('w-full justify-center mt-4'):
                def can_analyze():
                    return (bool(page_data.uploaded_resume) and 
                           bool(page_data.job_description and len(page_data.job_description.strip()) > 10) and 
                           not page_data.processing)
                
                analyze_button = ui.button(
                    'Analyze Resume Match' if not page_data.processing else 'Processing...',
                    on_click=lambda: self.start_analysis(page_data)
                ).props('color=primary size=lg')
                
                # Update button state periodically
                ui.timer(0.5, lambda: setattr(analyze_button, 'enabled', can_analyze()))
    
    @ui.refreshable
    def ats_score_section(self, page_data: CVCreatorPageData) -> None:
        """ATS compliance score display"""
        if not page_data.original_ats_score:
            return
            
        with ui.card().classes('w-full max-w-4xl mx-auto mb-4'):
            with ui.row().classes('w-full items-center'):
                ui.label('ATS Compliance Score:').classes('font-semibold text-lg')
                
                # Color coding for score
                if page_data.original_ats_score >= 80:
                    color = 'green'
                    status = 'Excellent'
                elif page_data.original_ats_score >= 60:
                    color = 'orange'
                    status = 'Good'
                else:
                    color = 'red'
                    status = 'Needs Improvement'
                
                ui.label(f'{page_data.original_ats_score}/100').classes(f'text-2xl font-bold text-{color}-600')
                ui.label(f'({status})').classes(f'text-{color}-600 ml-2')
                
                ui.linear_progress(
                    value=page_data.original_ats_score / 100,
                    color=color
                ).classes('flex-1 ml-4')
            
            # Show feedback if available
            if page_data.ats_feedback:
                with ui.expansion('ATS Feedback Details', icon='info').classes('w-full mt-4'):
                    for feedback in page_data.ats_feedback:
                        with ui.row().classes('items-center'):
                            ui.icon('warning', color='orange').classes('mr-2')
                            ui.label(feedback)
    
    @ui.refreshable  
    def analysis_results(self, page_data: CVCreatorPageData) -> None:
        """Show comprehensive analysis results"""
        if not page_data.show_analysis_results:
            return
            
        with ui.card().classes('w-full max-w-4xl mx-auto mb-4'):
            ui.label('Step 3: Analysis Results').classes('text-xl font-bold mb-4')
            
            # Match percentage
            if page_data.match_percentage is not None:
                with ui.row().classes('w-full items-center mb-4'):
                    ui.label('Match Score:').classes('font-semibold text-lg')
                    
                    color = 'green' if page_data.match_percentage >= 70 else 'orange' if page_data.match_percentage >= 50 else 'red'
                    ui.label(f'{page_data.match_percentage:.1f}%').classes(f'text-2xl font-bold text-{color}-600 ml-2')
                    
                    ui.linear_progress(
                        value=page_data.match_percentage / 100,
                        color=color
                    ).classes('flex-1 ml-4')
            
            # Detailed analysis in tabs
            with ui.tabs().classes('w-full') as tabs:
                gaps_tab = ui.tab('Gaps Identified')
                strengths_tab = ui.tab('Strengths')
                recommendations_tab = ui.tab('Recommendations')
            
            with ui.tab_panels(tabs, value=gaps_tab).classes('w-full'):
                # Gaps panel
                with ui.tab_panel(gaps_tab):
                    if page_data.gap_details:
                        for gap in page_data.gap_details:
                            with ui.card().classes('w-full mb-2'):
                                with ui.row().classes('w-full items-center'):
                                    severity_color = {
                                        'Critical': 'red',
                                        'High': 'orange', 
                                        'Medium': 'yellow',
                                        'Low': 'green'
                                    }.get(gap.get('severity', 'Medium'), 'gray')
                                    
                                    ui.icon('warning', color=severity_color)
                                    ui.label(f"[{gap.get('category', 'General')}] {gap.get('gap', 'Unknown gap')}").classes('font-semibold')
                                    ui.chip(gap.get('severity', 'Medium'), color=severity_color).classes('ml-auto')
                                
                                if gap.get('suggestions'):
                                    ui.label('Suggestions:').classes('font-semibold text-sm mt-2')
                                    for suggestion in gap.get('suggestions', []):
                                        ui.label(f'• {suggestion}').classes('text-sm ml-4')
                
                # Strengths panel
                with ui.tab_panel(strengths_tab):
                    if page_data.strengths:
                        for strength in page_data.strengths:
                            with ui.card().classes('w-full mb-2'):
                                with ui.row().classes('w-full items-center'):
                                    ui.icon('check_circle', color='green')
                                    ui.label(f"[{strength.get('category', 'General')}] {strength.get('strength', 'Unknown strength')}").classes('font-semibold')
                                
                                if strength.get('leverage_suggestion'):
                                    ui.label(f"💡 {strength.get('leverage_suggestion')}").classes('text-sm text-blue-600 mt-2')
                
                # Recommendations panel
                with ui.tab_panel(recommendations_tab):
                    if page_data.recommendations:
                        for rec in page_data.recommendations:
                            with ui.card().classes('w-full mb-2'):
                                with ui.row().classes('w-full items-center'):
                                    priority_color = {
                                        'High': 'red',
                                        'Medium': 'orange',
                                        'Low': 'green'
                                    }.get(rec.get('priority', 'Medium'), 'gray')
                                    
                                    ui.icon('lightbulb', color=priority_color)
                                    ui.label(rec.get('description', 'No description')).classes('font-semibold')
                                    ui.chip(rec.get('priority', 'Medium'), color=priority_color).classes('ml-auto')
                                
                                ui.label(f"Section: {rec.get('section', 'General')}").classes('text-sm text-gray-600')
            
            # Generate CV button
            with ui.row().classes('w-full justify-center mt-4'):
                ui.button(
                    'Generate Improved CV',
                    on_click=lambda: self.generate_cv(page_data)
                ).props('color=primary size=lg').bind_enabled_from(
                    page_data, 'processing', backward=lambda x: not x
                )
    
    @ui.refreshable
    def cv_editor(self, page_data: CVCreatorPageData) -> None:
        """CV editor and feedback section with change tracking"""
        if not page_data.show_cv_editor or not page_data.improved_cv:
            return
            
        with ui.card().classes('w-full max-w-4xl mx-auto mb-4'):
            ui.label('Step 4: Review & Edit CV').classes('text-xl font-bold mb-4')
            
            # Changes summary
            if page_data.changes_made:
                with ui.expansion('📋 Changes Made to Your Resume', icon='edit').classes('w-full mb-4'):
                    with ui.column().classes('w-full'):
                        for change in page_data.changes_made[:10]:  # Show first 10 changes
                            with ui.card().classes('w-full mb-2'):
                                ui.label(f"[{change.get('section', 'General')}] {change.get('change_type', 'Modified')}").classes('font-semibold text-blue-600')
                                ui.label(change.get('reason', 'Improvement made')).classes('text-sm')
                                if change.get('addresses_gap'):
                                    ui.label(f"🎯 Addresses: {change.get('addresses_gap')}").classes('text-xs text-green-600')
                        
                        if len(page_data.changes_made) > 10:
                            ui.label(f"...and {len(page_data.changes_made) - 10} more improvements").classes('text-sm text-gray-600')
            
            # CV preview/editor
            with ui.column().classes('w-full'):
                ui.label('Generated CV:').classes('font-semibold mb-2')
                
                cv_editor = ui.textarea(
                    value=page_data.improved_cv,
                    placeholder='Your improved CV will appear here...'
                ).props('outlined rows=20 font-family=monospace').classes('w-full mb-4')
                
                # Feedback section
                ui.label('Your Feedback (Optional):').classes('font-semibold mb-2')
                ui.textarea(
                    placeholder='Any specific changes you want to make? (e.g., "Add more emphasis on Python skills", "Remove outdated experience")',
                    value=page_data.user_feedback or ''
                ).bind_value(page_data, 'user_feedback').props('outlined rows=3').classes('w-full mb-4')
                
                # Action buttons
                with ui.row().classes('w-full justify-center gap-4'):
                    ui.button(
                        'Apply Feedback & Finalize',
                        on_click=lambda: self.finalize_cv(page_data, cv_editor.value)
                    ).props('color=primary')
                    
                    ui.button(
                        'Use As-Is',
                        on_click=lambda: self.finalize_cv(page_data, cv_editor.value, skip_feedback=True)
                    ).props('color=secondary')
    
    @ui.refreshable
    def final_results(self, page_data: CVCreatorPageData) -> None:
        """Final results with comprehensive metrics and download options"""
        if not page_data.show_final_results or not page_data.final_cv:
            return
            
        with ui.card().classes('w-full max-w-4xl mx-auto mb-4'):
            ui.label('Step 5: Final Results').classes('text-xl font-bold mb-4')
            
            # Improvement metrics
            with ui.row().classes('w-full gap-4 mb-4'):
                # Match score improvement
                with ui.card().classes('flex-1 text-center'):
                    ui.label('Match Score').classes('font-semibold')
                    if page_data.match_percentage:
                        ui.label(f'{page_data.match_percentage:.1f}%').classes('text-2xl font-bold text-green-600')
                        ui.label('Final Score').classes('text-sm text-gray-600')
                
                # ATS score improvement  
                with ui.card().classes('flex-1 text-center'):
                    ui.label('ATS Compliance').classes('font-semibold')
                    if page_data.final_ats_score:
                        ui.label(f'{page_data.final_ats_score}/100').classes('text-2xl font-bold text-blue-600')
                        if page_data.ats_improvement and page_data.ats_improvement > 0:
                            ui.label(f'(+{page_data.ats_improvement} points)').classes('text-sm text-green-600')
                
                # Gaps addressed
                with ui.card().classes('flex-1 text-center'):
                    ui.label('Gaps Addressed').classes('font-semibold')
                    ui.label(f'{len(page_data.addressed_gaps)}').classes('text-2xl font-bold text-purple-600')
                    ui.label('Improvements').classes('text-sm text-gray-600')
            
            # Detailed results in tabs
            with ui.tabs().classes('w-full') as result_tabs:
                addressed_tab = ui.tab('✅ Improvements Made')
                remaining_tab = ui.tab('⚠️ Remaining Gaps') 
                feedback_tab = ui.tab('💬 Feedback Applied')
            
            with ui.tab_panels(result_tabs, value=addressed_tab).classes('w-full'):
                # Addressed gaps
                with ui.tab_panel(addressed_tab):
                    if page_data.addressed_gaps:
                        for gap in page_data.addressed_gaps:
                            with ui.row().classes('items-center mb-2'):
                                ui.icon('check_circle', color='green')
                                ui.label(gap).classes('ml-2')
                    else:
                        ui.label('No specific gaps were addressed in this iteration.')
                
                # Remaining gaps
                with ui.tab_panel(remaining_tab):
                    if page_data.remaining_gaps:
                        for gap in page_data.remaining_gaps:
                            with ui.row().classes('items-center mb-2'):
                                ui.icon('info', color='orange')
                                ui.label(gap).classes('ml-2')
                    else:
                        ui.label('Great! All major gaps have been addressed.')
                
                # Feedback applied
                with ui.tab_panel(feedback_tab):
                    if page_data.user_feedback_applied:
                        for feedback_change in page_data.user_feedback_applied:
                            with ui.card().classes('w-full mb-2'):
                                ui.label(f"[{feedback_change.get('section', 'General')}] {feedback_change.get('change_type', 'Modified')}").classes('font-semibold text-blue-600')
                                ui.label(f"Feedback: {feedback_change.get('feedback_item', 'N/A')}").classes('text-sm')
                                ui.label(f"Change: {feedback_change.get('reasoning', 'Applied as requested')}").classes('text-sm text-green-600')
                    else:
                        ui.label('No specific feedback was provided or applied.')
            
            # Download section
            with ui.row().classes('w-full justify-center gap-4 mt-6'):
                ui.button(
                    'Download PDF',
                    on_click=lambda: self.download_cv(page_data, 'pdf')
                ).props('color=primary icon=download')
                
                ui.button(
                    'Download DOCX',
                    on_click=lambda: self.download_cv(page_data, 'docx')
                ).props('color=secondary icon=download')
                
                ui.button(
                    'Download TXT',
                    on_click=lambda: self.download_cv(page_data, 'txt')
                ).props('color=accent icon=download')
                
                ui.button(
                    'Download Comparison Report',
                    on_click=lambda: self.download_cv(page_data, 'comparison')
                ).props('color=info icon=download')
            
            # Start over section
            with ui.row().classes('w-full justify-center mt-6'):
                ui.button(
                    'Create Another CV',
                    on_click=lambda: self.reset_app(page_data)
                ).props('color=accent outlined')
    
    async def start_analysis(self, page_data: CVCreatorPageData):
        """Start comprehensive CV analysis"""
        logger.info("Starting comprehensive analysis...")
        try:
            page_data.processing = True
            page_data.error = None
            self.upload_section.refresh(page_data)
            
            if not is_clients_initialized():
                raise Exception("LLM clients not initialized")
            
            agent = get_global_agent()
            if not agent:
                raise Exception("Agent not initialized")
            
            config = {"configurable": {"thread_id": f"cv_session_{id(page_data)}", "recursion_limit": 50}}
            
            # Create initial state with all uploaded data
            initial_state = CVCreatorState(
                messages=[HumanMessage(content="Starting comprehensive CV analysis")],
                uploaded_resume=page_data.uploaded_resume,
                job_description=page_data.job_description,
                current_step="upload",
                processing=True
            )
            
            # Run comprehensive analysis
            result = await run.io_bound(agent.invoke, initial_state, config)
            
            # Extract all results
            page_data.match_percentage = result.get("match_percentage")
            page_data.identified_gaps = result.get("identified_gaps", [])
            page_data.gap_details = result.get("gap_details", [])
            page_data.strengths = result.get("strengths", [])
            page_data.recommendations = result.get("recommendations", [])
            page_data.current_step = result.get("current_step", "analysis_complete")
            page_data.show_analysis_results = True
            page_data.steps_completed["analyze"] = True
            
            ui.notify('Analysis complete!', type='positive')
            
        except Exception as e:
            page_data.error = str(e)
            logger.error(f"Analysis failed: {e}")
            ui.notify(f'Analysis failed: {str(e)}', type='negative')
        finally:
            page_data.processing = False
            self.upload_section.refresh(page_data)
            self.analysis_results.refresh(page_data)
    
    async def generate_cv(self, page_data: CVCreatorPageData):
        """Generate improved CV with change tracking"""
        try:
            page_data.processing = True
            self.analysis_results.refresh(page_data)
            
            agent = get_global_agent()
            config = {"configurable": {"thread_id": f"cv_session_{id(page_data)}"}}
            
            # Get current state and trigger CV generation
            current_state = agent.get_state(config).values
            current_state["current_step"] = "match_analyzed"
            
            result = await run.io_bound(agent.invoke, current_state, config)
            
            # Extract generation results
            page_data.improved_cv = result.get("improved_cv")
            page_data.changes_made = result.get("changes_made", [])
            page_data.keywords_added = result.get("keywords_added", [])
            page_data.show_cv_editor = True
            page_data.steps_completed["generate"] = True
            
            ui.notify(f'CV generated successfully! {len(page_data.changes_made)} improvements made.', type='positive')
            
        except Exception as e:
            ui.notify(f'CV generation failed: {str(e)}', type='negative')
        finally:
            page_data.processing = False
            self.analysis_results.refresh(page_data)
            self.cv_editor.refresh(page_data)
    
    async def finalize_cv(self, page_data: CVCreatorPageData, cv_content: str, skip_feedback: bool = False):
        """Finalize CV with user feedback and final analysis"""
        try:
            page_data.processing = True
            self.cv_editor.refresh(page_data)
            
            agent = get_global_agent()
            config = {"configurable": {"thread_id": f"cv_session_{id(page_data)}"}}
            
            # Update state with edited content and feedback
            current_state = agent.get_state(config).values
            current_state["improved_cv"] = cv_content
            current_state["user_feedback"] = page_data.user_feedback if not skip_feedback else None
            current_state["current_step"] = "cv_generated"
            
            # Run through feedback application and final analysis
            result = await run.io_bound(agent.invoke, current_state, config)
            
            # Extract final results
            page_data.final_cv = result.get("final_cv")
            page_data.final_match_percentage = result.get("final_match_percentage", page_data.match_percentage)
            page_data.match_percentage = page_data.final_match_percentage  # Update display
            page_data.final_ats_score = result.get("final_ats_score")
            page_data.ats_improvement = result.get("ats_improvement", 0)
            page_data.addressed_gaps = result.get("addressed_gaps", [])
            page_data.remaining_gaps = result.get("remaining_gaps", [])
            page_data.user_feedback_applied = result.get("user_feedback_applied", [])
            page_data.show_final_results = True
            page_data.steps_completed["finalize"] = True
            
            ui.notify('CV finalized successfully!', type='positive')
            
        except Exception as e:
            ui.notify(f'Finalization failed: {str(e)}', type='negative')
        finally:
            page_data.processing = False
            self.cv_editor.refresh(page_data)
            self.final_results.refresh(page_data)
    
    def download_cv(self, page_data: CVCreatorPageData, format_type: str):
        """Generate and download CV files"""
        if not page_data.final_cv:
            ui.notify('No CV available to download', type='negative')
            return
        
        try:
            if format_type == 'pdf':
                file_content = CVGenerator.create_pdf_from_text(
                    page_data.final_cv, 
                    page_data.changes_made
                )
                filename = "improved_cv.pdf"
                media_type = "application/pdf"
                
            elif format_type == 'docx':
                file_content = CVGenerator.create_docx_from_text(
                    page_data.final_cv,
                    page_data.changes_made
                )
                filename = "improved_cv.docx"
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                
            elif format_type == 'txt':
                file_content = CVGenerator.create_text_file(
                    page_data.final_cv,
                    page_data.changes_made
                )
                filename = "improved_cv.txt"
                media_type = "text/plain"
                
            elif format_type == 'comparison':
                file_content = CVGenerator.create_comparison_document(
                    page_data.uploaded_resume,
                    page_data.final_cv,
                    page_data.changes_made
                )
                filename = "cv_improvement_report.docx"
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            else:
                ui.notify('Unsupported format', type='negative')
                return
            
            ui.download(file_content, filename, media_type=media_type)
            ui.notify(f'Downloaded {filename}', type='positive')
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            ui.notify(f'Download failed: {str(e)}', type='negative')
    
    def reset_app(self, page_data: CVCreatorPageData):
        """Reset application for new CV creation"""
        # Clear all data except LLM configuration
        llm_provider = page_data.llm_provider
        api_key = page_data.api_key
        llm_configured = page_data.llm_configured
        
        page_data.__init__()
        
        # Restore LLM configuration
        page_data.llm_provider = llm_provider
        page_data.api_key = api_key
        page_data.llm_configured = llm_configured
        if llm_configured:
            page_data.current_step = "upload"
            page_data.steps_completed["config"] = True
        
        # Refresh all sections
        self.llm_config_section.refresh(page_data)
        self.upload_section.refresh(page_data)
        self.ats_score_section.refresh(page_data)
        self.analysis_results.refresh(page_data)
        self.cv_editor.refresh(page_data)
        self.final_results.refresh(page_data)
        
        ui.notify('Ready for new CV creation', type='info')


async def cv_creator_page(request: Request):
    """Main CV creator page with enhanced functionality"""
    # Initialize page data
    page_data = CVCreatorPageData()
    refreshables = Refreshables()
    
    # Page styling
    ui.add_css("""
        .max-w-4xl { max-width: 56rem; }
        .font-mono { font-family: monospace; }
        .step-indicator { 
            background: linear-gradient(45deg, #f0f0f0, #e0e0e0);
            border-radius: 8px;
            padding: 8px 16px;
        }
        .step-completed { 
            background: linear-gradient(45deg, #4CAF50, #45a049) !important;
            color: white;
        }
        .step-active { 
            background: linear-gradient(45deg, #2196F3, #1976D2) !important;
            color: white;
        }
    """)
    
    # Header with provider info
    with ui.header().classes('bg-primary text-white'):
        with ui.row().classes('w-full max-w-6xl mx-auto items-center'):
            ui.label('AI CV Creator Agent').classes('text-2xl font-bold')
            ui.space()
            
            # Show current provider
            if is_clients_initialized():
                provider = get_current_provider()
                if provider:
                    ui.label(f'Powered by {provider.title()}').classes('text-sm')
            else:
                ui.label('Configure AI Provider').classes('text-sm')
    
    # Progress indicator
    with ui.row().classes('w-full max-w-4xl mx-auto p-4 gap-2'):
        steps = [
            ("Config", "⚙️"),
            ("Upload", "📄"), 
            ("Analyze", "🔍"),
            ("Generate", "✨"),
            ("Review", "📝"),
            ("Download", "💾")
        ]
        
        for i, (step_name, icon) in enumerate(steps):
            step_key = step_name.lower()
            classes = 'step-indicator text-sm px-3 py-1 rounded'
            
            if page_data.steps_completed.get(step_key, False):
                classes += ' step-completed'
            elif step_name.lower() == page_data.current_step:
                classes += ' step-active'
            
            with ui.element('div').classes(classes):
                ui.label(f'{icon} {step_name}')
    
    # Main content
    with ui.column().classes('w-full max-w-6xl mx-auto p-4 gap-6'):
        # App description
        with ui.card().classes('w-full max-w-4xl mx-auto'):
            ui.markdown("""
            ## Welcome to AI CV Creator Agent
            
            Transform your resume to match any job description with AI-powered analysis and optimization.
            
            **Enhanced Features:**
            - **🤖 Multi-LLM Support** - Choose between OpenAI GPT-4 or Google Gemini
            - **📊 ATS Compliance Scoring** - Get detailed feedback on ATS compatibility
            - **🔍 Comprehensive Gap Analysis** - Identify exactly what's missing from your resume
            - **📝 Change Tracking** - See exactly what improvements were made
            - **💬 Feedback Integration** - Your comments are incorporated into the final CV
            - **📄 Multiple Download Formats** - PDF, DOCX, TXT, and comparison reports
            """)
        
        # Error display
        if page_data.error:
            with ui.card().classes('w-full max-w-4xl mx-auto bg-red-50 border-red-200'):
                ui.label(f'Error: {page_data.error}').classes('text-red-700')
        
        # Render sections
        refreshables.llm_config_section(page_data)
        refreshables.upload_section(page_data)
        refreshables.ats_score_section(page_data)
        refreshables.analysis_results(page_data)
        refreshables.cv_editor(page_data)
        refreshables.final_results(page_data)
    
    # Footer
    with ui.footer().classes('bg-gray-100'):
        with ui.row().classes('w-full max-w-6xl mx-auto justify-center p-4'):
            ui.markdown('Built with [NiceGUI](https://nicegui.io), [LangGraph](https://langchain-ai.github.io/langgraph/), and Multi-LLM Support')


def init_cv_app(fastapi_app: FastAPI) -> None:
    """Initialize the enhanced CV creator app"""
    ui.page('/', title='AI CV Creator Agent - Enhanced', response_timeout=120)(cv_creator_page)
    ui.run_with(fastapi_app, mount_path='/')