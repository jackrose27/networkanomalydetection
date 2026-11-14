"""Launch with: python app.py"""

from pathlib import Path
import tempfile

import gradio as gr
import pandas as pd

from inference import load_models, predict_dataframe

CHUNK_SIZE = 10_000
PREVIEW_ROWS = 50


def analyze_csv(filepath: str):
    """Run memory-bounded CSV inference and return a preview + full CSV file."""
    if not filepath:
        raise gr.Error("Upload a .csv file first.")

    try:
        models = load_models()
        output_file = tempfile.NamedTemporaryFile(
            prefix="network_predictions_", suffix=".csv", delete=False
        )
        output_path = Path(output_file.name)
        output_file.close()

        preview = []
        total = 0
        attacks = 0
        family_counts = {}
        first_chunk = True

        for chunk in pd.read_csv(filepath, chunksize=CHUNK_SIZE):
            result = predict_dataframe(chunk, models)
            result.to_csv(output_path, mode="w" if first_chunk else "a",
                          index=False, header=first_chunk)
            first_chunk = False
            total += len(result)
            attacks += int((result["Tier1_Prediction"] == "Attack").sum())

            for name, count in result["Predicted_Class"].value_counts().items():
                family_counts[name] = family_counts.get(name, 0) + int(count)

            if sum(len(part) for part in preview) < PREVIEW_ROWS:
                n = PREVIEW_ROWS - sum(len(part) for part in preview)
                preview.append(result.head(n))

        if total == 0:
            raise ValueError("The CSV has column headers but no data rows.")

        summary = (
            f"**Flows processed:** {total:,}  |  "
            f"**Flagged attacks:** {attacks:,}  |  "
            f"**Predicted normal:** {total - attacks:,}  |  "
            f"**Tier 1 cutoff:** {models.metadata['threshold']:.2f}\n\n"
            "**Predicted classes:** "
            + ", ".join(
                f"{name}: {count:,}" for name, count in
                sorted(family_counts.items(), key=lambda item: -item[1])
            )
        )
        return summary, pd.concat(preview, ignore_index=True), str(output_path)

    except (FileNotFoundError, ValueError, KeyError, pd.errors.ParserError) as exc:
        raise gr.Error(str(exc)) from exc


with gr.Blocks(title="Network Anomaly Detection") as demo:
    gr.Markdown(
        "# Network Anomaly Detection\n"
        "Upload a CSV of UNSW-NB15-format network flows. "
        "Tier 1 detects potentially malicious traffic; Tier 2 assigns "
        "one of nine attack families.\n\n"
        "The attack score is a **model score**, not a calibrated probability. "
        "This is a research demo, not a production security monitor."
    )
    uploaded = gr.File(label="Upload network-flow CSV", file_types=[".csv"], type="filepath")
    run = gr.Button("Analyze network flows", variant="primary")
    summary = gr.Markdown()
    preview = gr.Dataframe(label="First 50 predictions", interactive=False)
    download = gr.File(label="Download all predictions (.csv)")
    run.click(analyze_csv, inputs=uploaded, outputs=[summary, preview, download])


if __name__ == "__main__":
    demo.launch()
