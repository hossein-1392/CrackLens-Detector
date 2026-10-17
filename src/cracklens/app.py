"""Gradio demo for CrackLens."""
from __future__ import annotations
import json
from pathlib import Path
from cracklens.pipeline import analyze_image

CSS = """
:root { --ink: #182326; --paper: #f4f1e8; --accent: #0d6e70; --warm: #d46b3b; }
.gradio-container { max-width: 1180px !important; background: var(--paper); color: var(--ink); }
#hero { border-left: 6px solid var(--accent); padding: 18px 24px; margin-bottom: 18px; }
#hero h1 { letter-spacing: -0.03em; color: var(--accent); }
button.primary { background: var(--accent) !important; border: none !important; }
"""

def build_demo(model_path: str | Path = "models/cracklens_classical.json"):
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError("Gradio is not installed. Run `python -m pip install -r requirements.txt`.") from exc
    def run(image, reference_mm, reference_pixels, code, exposure):
        if image is None:
            return None, [], "Upload an image to begin."
        result = analyze_image(image, model_path=model_path, reference_mm=float(reference_mm), reference_pixels=float(reference_pixels) if reference_pixels else None, code=code, exposure=exposure)
        rows = []
        for record in result["records"]:
            rows.append([record["crack_id"], record["classification"], round(record["angle_deg_from_vertical"], 1), round(record["length_mm"], 2), round(record["max_width_mm"], 3), round(record["mean_width_mm"], 3), record["verdict"]])
        return result["overlay"], rows, json.dumps(result["summary"], indent=2)
    with gr.Blocks(css=CSS, title="CrackLens") as demo:
        gr.Markdown("# CrackLens\n### RC beam crack inspection", elem_id="hero")
        with gr.Row():
            with gr.Column(scale=1):
                input_image = gr.Image(type="numpy", label="Beam image")
                reference_mm = gr.Number(value=100.0, label="Reference length (mm)")
                reference_pixels = gr.Number(value=None, label="Reference length (pixels, optional)")
                code = gr.Dropdown(["ACI224R", "Mabhas9"], value="ACI224R", label="Screening code")
                exposure = gr.Dropdown(["dry_air", "humidity", "deicing", "seawater_wetting_drying", "water_retaining"], value="humidity", label="Exposure")
                analyze = gr.Button("Analyze cracks", variant="primary")
            with gr.Column(scale=1):
                output_image = gr.Image(label="Segmented overlay")
                table = gr.Dataframe(headers=["ID", "Type", "Angle?", "Length mm", "Max width mm", "Mean width mm", "Verdict"], label="Per-crack measurements", interactive=False)
                summary = gr.Code(label="Summary", language="json")
        analyze.click(run, [input_image, reference_mm, reference_pixels, code, exposure], [output_image, table, summary])
    return demo

def launch(model_path: str | Path = "models/cracklens_classical.json") -> None:
    build_demo(model_path).launch()

if __name__ == "__main__":
    launch()
