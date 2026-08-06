from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from materials_mvp.data import generate_sample_data

generate_sample_data(ROOT / "data" / "sample_materials.csv")
print("generated data/sample_materials.csv")

