import streamlit as st
from openai import OpenAI
import base64
from PIL import Image
import datetime
import json
from io import BytesIO

# Set up page configuration
st.set_page_config(
    page_title="HungerBox Vision Analysis",
    page_icon="🍲",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
<style>
    .header {
        color: #2E86C1;
        border-bottom: 2px solid #2E86C1;
        padding-bottom: 10px;
    }
    .metric-box {
        background-color: #F8F9F9;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .severity-critical { color: #E74C3C !important; }
    .severity-major { color: #F39C12 !important; }
    .severity-minor { color: #F1C40F !important; }
</style>
""", unsafe_allow_html=True)

# Main app function
def main():
    st.title("🍲 HungerBox Food Safety Analyzer")
    st.markdown("### AI-powered Compliance Assessment for Cafeteria Operations")

    # Input Section
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            api_key = st.text_input("OpenAI API Key", type="password")
            cafeteria_name = st.text_input("Cafeteria Name")
            question = st.text_area("Assessment Question", 
                                  placeholder="Enter your food safety question...")
            
        with col2:
            uploaded_image = st.file_uploader("Upload Cafeteria Image", 
                                           type=["jpg", "jpeg", "png"],
                                           help="Upload a clear image of the area to assess")
            if uploaded_image:
                image = Image.open(uploaded_image)
                st.image(image, caption="Preview of Uploaded Image", use_container_width=True)

        submitted = st.form_submit_button("Analyze Compliance")

    # Analysis Logic
    if submitted:
        if not all([api_key, cafeteria_name, question, uploaded_image]):
            st.error("⚠️ Please fill all required fields and upload an image")
            return

        try:
            with st.spinner("🔍 Analyzing image and preparing report..."):
                # Convert image to base64
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                # Create OpenAI client
                client = OpenAI(api_key=api_key)

                # Construct analysis prompt
                prompt = f"""
                You are a food safety manager analyzing a cafeteria image.
                Question to evaluate: {question}

                IMPORTANT INSTRUCTIONS:
                1. First assess image quality (darkness/blurriness)
                2. For blank/empty area requests, dark images may be compliant
                3. Only mark dark/blurry images as compliant if they satisfy specific criteria

                Provide JSON analysis with:
                - criteria_met: Yes/No/Unable
                - explanation: 2-3 sentence assessment
                - improvements: actionable suggestions
                - severity: Critical/Major/Minor/None
                - image_quality_issues: list of issues
                - quality_assessment: image quality impact
                - tags: 3-5 descriptive tags
                """

                # API Call
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", 
                             "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                            }
                        ]
                    }],
                    response_format={"type": "json_object"}
                )

                # Process response
                result = json.loads(response.choices[0].message.content)
                analysis_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Display Results
                st.success("✅ Analysis Complete!")
                display_results(result, cafeteria_name, question, analysis_date)

        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")

# Results display function
def display_results(result, cafeteria_name, question, analysis_date):
    # Severity color mapping
    severity_color = {
        "Critical": "severity-critical",
        "Major": "severity-major",
        "Minor": "severity-minor",
        "None": ""
    }

    # Main metrics
    with st.container():
        st.markdown("## 📋 Compliance Report")
        
        col1, col2, col3 = st.columns([1,1,2])
        
        with col1:
            st.markdown(f"**Cafeteria:** {cafeteria_name}")
            st.markdown(f"**Analysis Date:** {analysis_date}")
            
        with col2:
            status = result.get('criteria_met', 'Unknown')
            status_icon = "✅" if status == "Yes" else "❌" if status == "No" else "❓"
            st.markdown(f"**Compliance Status:** {status_icon} {status}")
            
            severity = result.get('severity', 'Unknown')
            color_class = severity_color.get(severity, "")
            st.markdown(f"**Severity Level:** <span class='{color_class}'>{severity}</span>", 
                       unsafe_allow_html=True)
        
        with col3:
            tags = result.get('tags', [])
            if isinstance(tags, list):
                tags = ", ".join(tags)
            st.markdown(f"**Tags:** 🏷️ {tags}")

    # Quality Assessment
    with st.expander("📸 Image Quality Analysis", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            issues = result.get('image_quality_issues', ['none'])
            if issues == ['none']:
                st.success("✅ No quality issues detected")
            else:
                st.error(f"⚠️ Detected issues: {', '.join(issues)}")
        
        with col2:
            st.info(f"Quality Impact Assessment: {result.get('quality_assessment', '')}")

    # Detailed Analysis
    with st.expander("🔍 Detailed Compliance Analysis"):
        st.markdown(f"**Assessment Question:** {question}")
        st.markdown("### Explanation")
        st.write(result.get('explanation', 'No explanation provided'))
        
        improvements = result.get('improvements', '')
        if improvements:
            st.markdown("### 🛠️ Improvement Suggestions")
            st.write(improvements)
        else:
            st.success("🌟 No improvements needed - all standards met")

if __name__ == "__main__":
    main()
