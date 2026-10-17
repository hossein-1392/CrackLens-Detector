"""Command line entry point for CrackLens."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from cracklens.app import launch
from cracklens.data.prepare import prepare_dataset
from cracklens.models.train import train_segmentation
from cracklens.pipeline import analyze_image, save_analysis

def run_report() -> str:
    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError as exc:
        raise RuntimeError("report generation needs nbformat and nbclient") from exc
    notebook_path = Path("notebooks/report.ipynb")
    executed_path = Path("notebooks/report.executed.ipynb")
    notebook = nbformat.read(notebook_path, as_version=4)
    NotebookClient(notebook, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(Path.cwd())}}).execute()
    nbformat.write(notebook, executed_path)
    return str(executed_path)

def main() -> None:
    parser = argparse.ArgumentParser(prog="cracklens")
    sub = parser.add_subparsers(dest="command", required=True)
    p_prepare = sub.add_parser("prepare"); p_prepare.add_argument("--root", default="data/processed"); p_prepare.add_argument("--count", type=int, default=24); p_prepare.add_argument("--seed", type=int, default=42); p_prepare.add_argument("--offline", action="store_true")
    p_train = sub.add_parser("train"); p_train.add_argument("--dataset-root", default="data/processed"); p_train.add_argument("--output-dir", default="models"); p_train.add_argument("--epochs", type=int, default=1); p_train.add_argument("--imgsz", type=int, default=320); p_train.add_argument("--device", default="auto")
    p_analyze = sub.add_parser("analyze"); p_analyze.add_argument("--image", required=True); p_analyze.add_argument("--model-path", default="models/cracklens_classical.json"); p_analyze.add_argument("--output", default="artifacts/analysis.json"); p_analyze.add_argument("--reference-mm", type=float, default=100.0); p_analyze.add_argument("--reference-pixels", type=float, default=None); p_analyze.add_argument("--code", default="ACI224R"); p_analyze.add_argument("--exposure", default="humidity")
    sub.add_parser("report")
    p_demo = sub.add_parser("demo"); p_demo.add_argument("--model-path", default="models/cracklens_classical.json")
    args = parser.parse_args()
    if args.command == "prepare":
        print(json.dumps(prepare_dataset(args.root, args.count, args.seed, allow_network=not args.offline).__dict__, indent=2))
    elif args.command == "train":
        print(json.dumps(train_segmentation(args.dataset_root, args.output_dir, args.epochs, args.imgsz, args.device), indent=2))
    elif args.command == "analyze":
        result = analyze_image(args.image, model_path=args.model_path, reference_mm=args.reference_mm, reference_pixels=args.reference_pixels, code=args.code, exposure=args.exposure)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        save_analysis(result, args.output)
        result["overlay"].save(Path(args.output).with_suffix(".png"))
        print(json.dumps(result["summary"], indent=2))
    elif args.command == "report":
        print(run_report())
    elif args.command == "demo":
        launch(args.model_path)

if __name__ == "__main__":
    main()
