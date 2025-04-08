# pages/home.py
import gradio as gr

def home_page():
    with gr.Column():
        gr.Markdown("# Review Platform for LLM-Generated Ophthalmology Dialogues and Reports")
        gr.Markdown("### Project: Streamline Ophthalmology Clinic Patient QA and Pre-Surgical Inquiry By Agentive LLMs")
        gr.Markdown("- Cataract is a common condition, yet limited consultation time often leaves patients without sufficient education about surgery and IOL options. This platform assists in improving patient understanding and decision-making with the help of AI-powered LLMs, reducing physician workload.")
        gr.Image("./assets/SchematicFlowDiagram.png", label="Cataract Overview", elem_classes="esponsive-image img")
        gr.Markdown("### Platform Purpose\n - Provide a report scoring system to refine the quality of AI-generated patient consultation reports.")
        gr.Markdown("### Powered by\n - Director : SJ, Chen | Vice Dean : TF, Chen | Resident : KJ, Chang | PGY : WC, Fang | Fellow : SC, Chi | MSc : KR, Liu | MSc : YJ, Meng | MSc : MK, Chen")
    return None