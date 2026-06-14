"""Training script for custom emergency vehicle YOLOv8 model."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import torch
from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train custom emergency-vehicle detector.")
    parser.add_argument(
        "--data",
        type=str,
        default="training/dataset.yaml",
        help="Path to dataset.yaml",
    )
    parser.add_argument("--weights", type=str, default="yolov8n.pt", help="Base pretrained weights.")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs.")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size for training.")
    parser.add_argument("--batch", type=int, default=16, help="Batch size.")
    parser.add_argument("--device", type=str, default="auto", help="Device: auto, mps, cpu, or CUDA index.")
    parser.add_argument("--project", type=str, default="runs/train", help="Ultralytics project dir.")
    parser.add_argument("--name", type=str, default="emergency_yolov8n", help="Ultralytics run name.")
    return parser.parse_args()


def save_best_model(run_dir: Path, output_path: Path) -> None:
    best_weight = run_dir / "weights" / "best.pt"
    if not best_weight.exists():
        raise FileNotFoundError(f"best.pt not found in expected run directory: {best_weight}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_weight, output_path)
    print(f"[INFO] Saved trained model to: {output_path}")


def resolve_device(device_arg: str) -> str:
    if device_arg != "auto":
        return device_arg
    if torch.cuda.is_available():
        return "0"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main() -> None:
    args = parse_args()
    dataset_file = Path(args.data)
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset YAML not found: {dataset_file}")

    selected_device = resolve_device(args.device)
    print(f"[INFO] Training device: {selected_device}")

    model = YOLO(args.weights)
    model.train(
        data=str(dataset_file),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=selected_device,
        project=args.project,
        name=args.name,
        pretrained=True,
        workers=4,
    )

    run_dir = Path(model.trainer.save_dir)
    save_best_model(run_dir=run_dir, output_path=Path("model/best.pt"))


if __name__ == "__main__":
    main()
