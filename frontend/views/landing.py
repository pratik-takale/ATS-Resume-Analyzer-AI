import streamlit as st


def render():
    
    # Landing page CSS
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            padding: 3rem 2rem;
            background: linear-gradient(135deg,#0F172A 0%,#1E3A8A 60%,#2563EB 100%);
            color: white;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(79, 70, 229, 0.3);
        }
        .main-header h1 {
            font-size: 2.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="main-header">
        <h1> AI Resume Analyzer</h1>
        <h3>Land More Interviews with AI-Powered ATS Optimization</h3>
        <p>Analyze your resume, compare it with job descriptions, receive AI feedback, and improve your ATS score in seconds.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Call-to-Action Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Analyze My Resume", use_container_width=True, type="primary"):
            st.session_state.current_view = 'scorer'
            st.rerun()
    
    st.markdown("---")
    
    # Features Overview
    st.markdown("##  Key Features")
    
    col1,col2,col3,col4 = st.columns(4)

    col1.metric("ATS Accuracy","98%")
    col2.metric("AI Analysis","Instant")
    col3.metric("Supported","PDF/DOCX")
    col4.metric("Privacy","100% Secure")
    
    with col1:
        st.markdown("""
        ###  Comprehensive Scoring
        Get detailed scores across 5 key dimensions:
        - Formatting (20%)
        - Keywords & Skills (25%)
        - Content Quality (25%)
        - Skill Validation (15%)
        - ATS Compatibility (15%)
        """)
    
    with col2:
        st.markdown("""
        ###  Skill Validation
        Verify that your claimed skills are demonstrated in your projects and experience using AI-powered semantic analysis.
        
        **No more empty claims!**
        """)
    
    with col3:
        st.markdown("""
        ###  Privacy First
        All analysis runs locally with no external API calls. Your resume data never leaves your system.
        
        **100% Private & Secure**
        """)
    
    st.markdown("---")
    
    # How It Works
    st.markdown("## How It Works")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### Upload Your Resume
        Support for PDF, DOC, and DOCX formats
        """)
    
    with col2:
        st.markdown("""
        ####  AI Analysis
        Our local AI models analyze your resume across multiple dimensions
        """)
    
    with col3:
        st.markdown("""
        ####  Get Actionable Feedback
        Receive detailed recommendations to improve your resume
        """)
