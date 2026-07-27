import streamlit as st
import pandas as pd
import numpy as np
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, PageBreak, HRFlowable)
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os
from dotenv import load_dotenv
import io
import pdfplumber
from auth import (init_db, register_user, login_user,
                  reset_password, save_audit_history, get_audit_history)

load_dotenv()

# Support both local .env and Streamlit Cloud secrets

try:

    api_key = st.secrets['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']

except:

    api_key = os.getenv('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')

client = Groq(api_key=api_key)

st.set_page_config(
    page_title="AuditIQ",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"   # add this
)


st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
            color: #2C2C2C;
        }
        .auditiq-header {
            background-color: #1B3A6B;
            padding: 24px 32px;
            border-radius: 4px;
            margin-bottom: 24px;
        }
        .auditiq-header h1 {
            color: white;
            font-size: 28px;
            font-weight: 700;
            margin: 0;
            letter-spacing: 1px;
        }
        .auditiq-header p {
            color: #B0C4DE;
            font-size: 13px;
            margin: 4px 0 0 0;
        }
        .audit-card {
            background-color: #F8FAFF;
            border: 1px solid #D0DCF0;
            border-left: 4px solid #1B3A6B;
            border-radius: 4px;
            padding: 20px 24px;
            margin-bottom: 16px;
        }
        .audit-card h4 {
            color: #1B3A6B;
            font-size: 14px;
            font-weight: 600;
            margin: 0 0 8px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .section-header {
            color: #1B3A6B;
            font-size: 16px;
            font-weight: 600;
            border-bottom: 2px solid #1B3A6B;
            padding-bottom: 8px;
            margin: 24px 0 16px 0;
        }
        .stButton > button {
            background-color: #1B3A6B;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 10px 24px;
            font-weight: 600;
            font-size: 14px;
            letter-spacing: 0.3px;
        }
        .stButton > button:hover {
            background-color: #15305A;
        }
        [data-testid="stSidebar"] {
            background-color: #F0F4FB;
            border-right: 1px solid #D0DCF0;
        }
        [data-testid="stMetric"] {
            background-color: #E8F0FE;
            border: 1px solid #D0DCF0;
            border-radius: 4px;
            padding: 12px;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: visible;}
        .finding-critical {
            background-color: #FFF0F0;
            border-left: 4px solid #C0392B;
            padding: 12px 16px;
            border-radius: 4px;
            margin: 8px 0;
            font-size: 13px;
        }
        .finding-warning {
            background-color: #FFFBF0;
            border-left: 4px solid #E67E22;
            padding: 12px 16px;
            border-radius: 4px;
            margin: 8px 0;
            font-size: 13px;
        }
        .finding-ok {
            background-color: #F0FFF4;
            border-left: 4px solid #27AE60;
            padding: 12px 16px;
            border-radius: 4px;
            margin: 8px 0;
            font-size: 13px;
        }
        .user-card {
            background-color: #1B3A6B;
            padding: 16px;
            border-radius: 4px;
            margin-bottom: 16px;
            color: white;
        }
        .user-card p {
            margin: 0;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'auth_page' not in st.session_state:
    st.session_state.auth_page = 'login'

# Auth pages
if not st.session_state.logged_in:
    st.markdown("""
        <div class="auditiq-header">
            <h1>AuditIQ</h1>
            <p>Intelligent Financial Audit Platform</p>
        </div>
    """, unsafe_allow_html=True)

    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])

    with auth_col2:
        tab1, tab2, tab3 = st.tabs([
            "Sign In", "Create Account", "Reset Password"
        ])

        # Sign in
        with tab1:
            st.markdown("### Welcome back")
            login_email = st.text_input(
                "Email address", key="login_email")
            login_password = st.text_input(
                "Password", type="password", key="login_password")

            if st.button("Sign In", key="login_btn"):
                if login_email and login_password:
                    success, result = login_user(
                        login_email, login_password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user = result
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.warning(
                        "Please enter your email and password.")

        # Create account
        with tab2:
            st.markdown("### Create your account")
            reg_name = st.text_input(
                "Full name", key="reg_name")
            reg_email = st.text_input(
                "Email address", key="reg_email")
            reg_password = st.text_input(
                "Password", type="password", key="reg_password")
            reg_confirm = st.text_input(
                "Confirm password", type="password",
                key="reg_confirm")

            if st.button("Create Account", key="reg_btn"):
                if not all([reg_name, reg_email,
                            reg_password, reg_confirm]):
                    st.warning("Please complete all fields.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 6:
                    st.error(
                        "Password must be at least 6 characters.")
                else:
                    success, message = register_user(
                        reg_name, reg_email, reg_password)
                    if success:
                        st.success(message)
                        st.info("Please sign in to continue.")
                    else:
                        st.error(message)

        # Reset password
        with tab3:
            st.markdown("### Reset your password")
            st.info(
                "Enter your registered email address and "
                "choose a new password."
            )
            reset_email = st.text_input(
                "Email address", key="reset_email")
            reset_new = st.text_input(
                "New password", type="password", key="reset_new")
            reset_confirm = st.text_input(
                "Confirm new password", type="password",
                key="reset_confirm")

            if st.button("Reset Password", key="reset_btn"):
                if not all([reset_email, reset_new, reset_confirm]):
                    st.warning("Please complete all fields.")
                elif reset_new != reset_confirm:
                    st.error("Passwords do not match.")
                elif len(reset_new) < 6:
                    st.error(
                        "Password must be at least 6 characters.")
                else:
                    success, message = reset_password(
                        reset_email, reset_new)
                    if success:
                        st.success(message)
                        st.info(
                            "You may now sign in with "
                            "your new password.")
                    else:
                        st.error(message)

    st.stop()

# User is logged in
# Sidebar
st.sidebar.markdown("### AuditIQ")
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**{st.session_state.user['name']}**")
st.sidebar.markdown(
    f"{st.session_state.user['email']}")
st.sidebar.markdown(
    f"Member since: {st.session_state.user['created_at'][:10]}")

if st.sidebar.button("Sign Out", key="signout_btn"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

st.sidebar.markdown("---")

with st.sidebar.expander("My Audit History"):
    history = get_audit_history(st.session_state.user['email'])
    if history:
        for h in history[:5]:
            st.sidebar.markdown(
                f"**{h[2] or 'Unknown'}** — {h[5]}"
                f"\n{h[6]} | {h[8]} critical findings"
            )
    else:
        st.sidebar.markdown("No audits completed yet.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Audit Configuration")

company_name = st.sidebar.text_input("Company Name", "")
industry = st.sidebar.selectbox("Industry", [
    "Banking and Finance", "Fintech", "Healthcare", "Retail",
    "Manufacturing", "Government", "Non-Profit", "Technology",
    "Real Estate", "Other"
])
accounting_standard = st.sidebar.selectbox("Accounting Standard", [
    "IFRS", "IFRS for SMEs", "US GAAP", "UK GAAP",
    "Japanese GAAP", "Chinese GAAP",
    "Indian Ind AS", "Swiss GAAP FER", "Australian AASB",
    "Brazilian BR GAAP", "IPSASB", "South Africa GRAP"
])
materiality_threshold = st.sidebar.number_input(
    "Materiality Threshold ($)",
    min_value=100, max_value=10000000, value=10000
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Standard Audit Checks")
st.sidebar.markdown("""
- Duplicate transactions
- Round number bias
- Weekend and holiday postings
- Quarter-end anomalies
- Material transactions
- Benfords Law analysis
- Management override indicators
- Accounting standards compliance
- AI audit opinion
""")

# Helper functions
def extract_file_content(uploaded_file):
    content = ""
    file_type = uploaded_file.name.split(".")[-1].lower()
    if file_type == "csv":
        df = pd.read_csv(uploaded_file)
        content = df.to_string()
        return content, df, file_type
    elif file_type in ["xlsx", "xls"]:
        df = pd.read_excel(uploaded_file)
        content = df.to_string()
        return content, df, file_type
    elif file_type == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        return content, None, file_type
    return "", None, file_type

def run_audit_checks(df, materiality_threshold):
    findings = []
    details = {}
    if df is None:
        return ["Automated audit checks require CSV or Excel data."], {}
    numeric_cols = df.select_dtypes(
        include=[np.number]).columns.tolist()
    if not numeric_cols:
        return ["No numeric columns found for audit analysis."], {}
    amount_col = numeric_cols[0]
    date_cols = [c for c in df.columns
                 if 'date' in c.lower() or 'time' in c.lower()]
    date_col = date_cols[0] if date_cols else None
    ref_cols = [c for c in df.columns
                if 'ref' in c.lower() or 'id' in c.lower()]
    ref_col = ref_cols[0] if ref_cols else None

    # Duplicates
    dups = df[df.duplicated(keep=False)]
    if len(dups) > 0:
        findings.append(
            f"CRITICAL: {len(dups)} duplicate records detected, "
            f"indicating possible double posting or data integrity "
            f"issues.")
        details['duplicates'] = dups
    else:
        findings.append("No duplicate records were identified.")

    # Round number bias
    round_nums = df[df[amount_col] % 1000 == 0]
    ratio = len(round_nums) / len(df)
    if ratio > 0.3:
        findings.append(
            f"WARNING: {round(ratio*100,1)}% of transactions contain "
            f"round figures, which may indicate estimation or "
            f"manipulation.")
        details['round_numbers'] = round_nums
    else:
        findings.append(
            f"Round number concentration is within acceptable range "
            f"at {round(ratio*100,1)}%.")

    # Timing anomalies
    if date_col:
        try:
            df[date_col] = pd.to_datetime(
                df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            weekends = df[df[date_col].dt.dayofweek >= 5]
            quarter_end = df[
                df[date_col].dt.month.isin([3, 6, 9, 12]) &
                (df[date_col].dt.day >= 25)
            ]
            if len(weekends) > 0:
                findings.append(
                    f"WARNING: {len(weekends)} transactions were "
                    f"posted on weekends, which requires further "
                    f"explanation.")
                details['weekends'] = weekends
            else:
                findings.append(
                    "No weekend transactions were identified.")
            if len(quarter_end) > 0:
                findings.append(
                    f"WARNING: {len(quarter_end)} transactions were "
                    f"recorded near quarter-end dates, suggesting "
                    f"potential earnings management.")
                details['quarter_end'] = quarter_end
            else:
                findings.append(
                    "No anomalous quarter-end transaction "
                    "patterns were detected.")
        except:
            findings.append(
                "Date analysis could not be completed due to "
                "inconsistent date formatting.")

    # Material transactions
    large = df[df[amount_col].abs() > materiality_threshold]
    if len(large) > 0:
        findings.append(
            f"NOTE: {len(large)} transactions exceed the materiality "
            f"threshold of ${materiality_threshold:,} and require "
            f"individual review.")
        details['material'] = large
    else:
        findings.append(
            f"No transactions exceed the materiality threshold "
            f"of ${materiality_threshold:,}.")

    # Benfords Law
    try:
        expected = {1: 30.1, 2: 17.6, 3: 12.5, 4: 9.7, 5: 7.9,
                    6: 6.7, 7: 5.8, 8: 5.1, 9: 4.6}
        amounts = df[amount_col].abs()
        first_digits = amounts.astype(str).str[0].astype(int)
        actual = first_digits.value_counts(normalize=True) * 100
        violations = []
        for digit in range(1, 10):
            deviation = abs(actual.get(digit, 0) - expected[digit])
            if deviation > 5:
                violations.append(str(digit))
        if violations:
            findings.append(
                f"CRITICAL: Benfords Law violations detected for "
                f"leading digits {', '.join(violations)}, which is a "
                f"recognised indicator of potential fraud or data "
                f"manipulation.")
        else:
            findings.append(
                "The data distribution is consistent with Benfords "
                "Law. No fraud indicators were detected.")
    except:
        findings.append(
            "Benfords Law analysis could not be completed.")

    # Management override
    if ref_col:
        no_ref = df[
            df[ref_col].isna() |
            (df[ref_col].astype(str).str.strip() == '')
        ]
        if len(no_ref) > 0:
            findings.append(
                f"WARNING: {len(no_ref)} transactions have no "
                f"reference number, which may indicate management "
                f"override of standard controls.")
            details['no_reference'] = no_ref
        else:
            findings.append(
                "All transactions contain valid reference numbers.")

    return findings, details

def get_ai_response(content, question, standard, company, industry):
    company_info = (f"for {company}, a {industry} company"
                    if company else f"for a {industry} company")
    prompt = f"""You are a senior partner at a Big 4 audit firm with 
25 years of experience in financial audit and forensic accounting. 
You are reviewing financial data {company_info} that reports 
under {standard}.

The following data has been provided:

{content[:4000]}

Respond to the following request:

{question}

Your response must adhere to the following standards:
- Written at C1 English proficiency level
- Elegant, professional and authoritative in tone
- Favour well-constructed paragraphs over bullet points
- Reference specific {standard} standards or sections where relevant,
  citing only those you are certain exist. Do not invent or 
  approximate standard numbers.
- Direct, precise and free of unnecessary filler language
- Written as a senior human auditor would write, not as a machine. Do not refer to yourself in the report, for example "As a senior auditor".
- Free of em-dashes and unnecessary punctuation"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500
    )
    return response.choices[0].message.content

def generate_pdf_report(company, standard, industry, content_summary,
                         ai_response, report_type, materiality):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1*inch, rightMargin=1*inch,
        topMargin=1*inch, bottomMargin=1*inch
    )
    story = []

    cover_title = ParagraphStyle(
        'CoverTitle', fontSize=20,
        textColor=colors.HexColor('#1B3A6B'),
        spaceAfter=8, fontName='Helvetica-Bold',
        alignment=TA_LEFT)
    cover_sub = ParagraphStyle(
        'CoverSub', fontSize=12,
        textColor=colors.HexColor('#4A6FA5'),
        spaceAfter=6, fontName='Helvetica',
        alignment=TA_LEFT)
    section_head = ParagraphStyle(
        'SectionHead', fontSize=13,
        textColor=colors.HexColor('#1B3A6B'),
        spaceAfter=10, spaceBefore=16,
        fontName='Helvetica-Bold')
    body = ParagraphStyle(
        'Body', fontSize=10,
        textColor=colors.HexColor('#2C2C2C'),
        spaceAfter=8, fontName='Helvetica',
        leading=16, alignment=TA_JUSTIFY)
    critical = ParagraphStyle(
        'Critical', fontSize=10,
        textColor=colors.HexColor('#C0392B'),
        spaceAfter=6, fontName='Helvetica', leading=14)
    warning = ParagraphStyle(
        'Warning', fontSize=10,
        textColor=colors.HexColor('#E67E22'),
        spaceAfter=6, fontName='Helvetica', leading=14)
    ok_style = ParagraphStyle(
        'OK', fontSize=10,
        textColor=colors.HexColor('#27AE60'),
        spaceAfter=6, fontName='Helvetica', leading=14)
    disclaimer_style = ParagraphStyle(
        'Disclaimer', fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceAfter=6, fontName='Helvetica-Oblique',
        leading=13, alignment=TA_JUSTIFY)

    date = datetime.now().strftime("%d %B %Y")

    def hr():
        story.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#D0DCF0')))

    def thick_hr():
        story.append(HRFlowable(
            width="100%", thickness=3,
            color=colors.HexColor('#1B3A6B')))

    # Cover
    story.append(Spacer(1, 0.8*inch))
    thick_hr()
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("AuditIQ", cover_title))
    story.append(Paragraph(
        "Intelligent Financial Audit Platform", cover_sub))
    story.append(Spacer(1, 0.4*inch))
    hr()
    story.append(Spacer(1, 0.4*inch))

    cover_data = [
        ['Report Type', report_type],
        ['Company', company if company else 'Confidential'],
        ['Industry', industry],
        ['Accounting Standard', standard],
        ['Materiality Threshold', f"${materiality:,}"],
        ['Report Date', date],
        ['Prepared by', 'AuditIQ Intelligent Audit Platform'],
        ['Classification', 'CONFIDENTIAL']
    ]
    cover_table = Table(cover_data, colWidths=[2.2*inch, 4*inch])
    cover_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#1B3A6B')),
        ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#2C2C2C')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D0DCF0')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#E8F0FE')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1),
         [colors.HexColor('#F8FAFF'), colors.white]),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.5*inch))
    thick_hr()
    story.append(PageBreak())

    # Findings
    story.append(Paragraph("Audit Findings", section_head))
    hr()
    story.append(Spacer(1, 0.15*inch))
    for i, finding in enumerate(content_summary, 1):
        if 'CRITICAL' in finding:
            clean = finding.replace('CRITICAL: ', '')
            story.append(Paragraph(f"{i}.  {clean}", critical))
        elif 'WARNING' in finding:
            clean = finding.replace('WARNING: ', '')
            story.append(Paragraph(f"{i}.  {clean}", warning))
        elif 'NOTE' in finding:
            clean = finding.replace('NOTE: ', '')
            story.append(Paragraph(f"{i}.  {clean}", body))
        else:
            story.append(Paragraph(f"{i}.  {finding}", ok_style))
    story.append(PageBreak())

    # AI Analysis
    story.append(Paragraph(
        "Auditor Analysis and Opinion", section_head))
    hr()
    story.append(Spacer(1, 0.15*inch))
    for line in ai_response.split('\n'):
        if line.strip():
            if any(line.strip().startswith(f"{n}.")
                   for n in range(1, 10)):
                story.append(Paragraph(
                    f"<b>{line.strip()}</b>", body))
            else:
                story.append(Paragraph(line.strip(), body))
    story.append(PageBreak())

    # Disclaimer
    story.append(Paragraph("Important Notice", section_head))
    hr()
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(
        "This report has been generated by AuditIQ, an AI-powered "
        "financial audit platform, and is intended solely for internal "
        "review and preliminary assessment purposes. It does not "
        "constitute a formal audit opinion, assurance engagement or "
        "professional advice under any recognised auditing, accounting "
        "or regulatory standards. The findings and observations "
        "contained herein should be reviewed and validated by a "
        "qualified, licensed auditor or chartered accountant prior to "
        "any formal reporting, regulatory submission or board-level "
        "decision-making. AuditIQ and its developers accept no "
        "liability for decisions made on the basis of this report "
        "without independent professional verification.",
        disclaimer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer

# Main header
st.markdown("""
    <div class="auditiq-header">
        <h1>AuditIQ</h1>
        <p>Intelligent Financial Audit Platform &nbsp;|&nbsp;
        AI-Powered Anomaly Detection and Compliance Analysis</p>
    </div>
""", unsafe_allow_html=True)

# Upload section
st.markdown(
    '<p class="section-header">Upload Financial Data</p>',
    unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Select a file to begin your audit",
    type=['csv', 'xlsx', 'xls', 'pdf'],
    help="Accepted formats: PDF, CSV and Excel"
)

if uploaded_file:
    with st.spinner("Reading file..."):
        content, df, file_type = extract_file_content(uploaded_file)

    st.markdown(f"""
        <div class="finding-ok">
            File loaded successfully.
            {f"{len(df):,} records detected."
             if df is not None
             else "Document content extracted."}
        </div>
    """, unsafe_allow_html=True)

    if df is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Records", f"{len(df):,}")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            total = pd.to_numeric(
                df[numeric_cols[0]], errors='coerce').sum()
            col2.metric("Total Value", f"${total:,.2f}")
        col3.metric("Columns Detected", len(df.columns))

        with st.expander("Preview uploaded data"):
            st.dataframe(df.head(10), use_container_width=True)

    st.markdown(
        '<p class="section-header">Select Audit Mode</p>',
        unsafe_allow_html=True)

    mode_col1, mode_col2 = st.columns(2)

    with mode_col1:
        st.markdown("""
            <div class="audit-card">
                <h4>Ask a Specific Question</h4>
                <p style="font-size:13px; color:#555;">
                    Direct the audit towards a specific area of concern,
                    accounting treatment or compliance question.
                </p>
            </div>
        """, unsafe_allow_html=True)
        question = st.text_area(
            "Enter your question or instruction",
            placeholder="Example: Are there any revenue recognition "
                        "issues under IFRS 15? Or: Summarise the key "
                        "financial risks in this data.",
            height=120
        )
        ask_button = st.button("Submit Question", key="ask_btn")

    with mode_col2:
        st.markdown("""
            <div class="audit-card">
                <h4>Run Standard Audit Checks</h4>
                <p style="font-size:13px; color:#555;">
                    Run the full suite of automated audit procedures
                    including Benfords Law, duplicate detection, timing
                    anomalies and standards compliance review.
                </p>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.write("")
        audit_button = st.button(
            "Run Full Audit Checks", key="audit_btn")

    # Question mode
    if ask_button and question:
        st.markdown(
            '<p class="section-header">Analysis</p>',
            unsafe_allow_html=True)
        with st.spinner("Analysing your data..."):
            response = get_ai_response(
                content, question,
                accounting_standard,
                company_name, industry
            )
        st.markdown(response)

        save_audit_history(
            st.session_state.user['email'],
            company_name,
            accounting_standard,
            industry,
            "Query Audit",
            1,
            0
        )

        with st.spinner("Generating report..."):
            pdf = generate_pdf_report(
                company_name, accounting_standard, industry,
                [f"User query: {question}"],
                response, "Specific Audit Query",
                materiality_threshold
            )
        st.download_button(
            "Download Report (PDF)",
            pdf,
            f"AuditIQ_Query_Report_"
            f"{datetime.now().strftime('%Y%m%d')}.pdf",
            "application/pdf",
            key="download_query"
        )

    # Full audit mode
    if audit_button:
        st.markdown(
            '<p class="section-header">Audit Results</p>',
            unsafe_allow_html=True)

        if df is None:
            st.warning(
                "Standard audit checks require CSV or Excel data. "
                "Please upload a structured data file.")
        else:
            findings, details = run_audit_checks(
                df, materiality_threshold)
            progress = st.progress(0)

            for i, finding in enumerate(findings):
                if 'CRITICAL' in finding:
                    st.markdown(
                        f'<div class="finding-critical">'
                        f'{finding.replace("CRITICAL: ", "")}'
                        f'</div>',
                        unsafe_allow_html=True)
                elif 'WARNING' in finding:
                    st.markdown(
                        f'<div class="finding-warning">'
                        f'{finding.replace("WARNING: ", "")}'
                        f'</div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div class="finding-ok">'
                        f'{finding}</div>',
                        unsafe_allow_html=True)
                progress.progress(int((i+1)/len(findings)*80))

            st.markdown(
                '<p class="section-header">AI Auditor Opinion</p>',
                unsafe_allow_html=True)

            findings_text = "\n".join(findings)
            audit_question = (
                f"Based on the automated audit findings provided, "
                f"deliver a comprehensive audit opinion covering "
                f"overall risk assessment, the most significant "
                f"findings, compliance with {accounting_standard}, "
                f"and your recommended audit opinion type. Conclude "
                f"with specific recommendations for management."
            )

            with st.spinner("Preparing audit opinion..."):
                ai_response = get_ai_response(
                    findings_text, audit_question,
                    accounting_standard, company_name, industry
                )
            st.markdown(ai_response)
            progress.progress(95)

            save_audit_history(
                st.session_state.user['email'],
                company_name,
                accounting_standard,
                industry,
                "Full Audit",
                len(findings),
                len([f for f in findings if 'CRITICAL' in f])
            )

            with st.spinner("Generating report..."):
                pdf = generate_pdf_report(
                    company_name, accounting_standard, industry,
                    findings, ai_response,
                    "Full Audit Report", materiality_threshold
                )
            st.download_button(
                "Download Full Audit Report (PDF)",
                pdf,
                f"AuditIQ Full Report"
                f"{datetime.now().strftime('%Y%m%d')}.pdf",
                "application/pdf",
                key="download_full"
            )
            progress.progress(100)
            st.success(
                "Audit complete. Your report is ready for download.")