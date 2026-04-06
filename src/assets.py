from pathlib import Path

def resolve_asset_path(relative_path: str) -> str:
    candidates = [
        Path(relative_path),
        Path("assets") / relative_path,
        Path(__file__).resolve().parent.parent / relative_path,
        Path(__file__).resolve().parent.parent / "assets" / relative_path,
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    raise FileNotFoundError(f"Could not find asset: {relative_path}")