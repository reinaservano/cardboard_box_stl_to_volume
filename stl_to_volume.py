"""Convert a closed STL mesh into a filled 3D voxel volume."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import trimesh


def load_stl_mesh(input_path: Path, closure: str = "reject") -> trimesh.Trimesh:
    """Load and validate an STL mesh, optionally closing it with a convex hull."""
    mesh = trimesh.load_mesh(input_path, file_type="stl")
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))

    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        raise ValueError("The STL does not contain any triangular faces.")
    if not np.isfinite(mesh.vertices).all():
        raise ValueError("The STL contains non-finite vertex coordinates.")
    if not mesh.is_watertight:
        if closure == "convex-hull":
            mesh = mesh.convex_hull
        else:
            raise ValueError(
                "The STL is not watertight. Choose convex-hull for an outer-envelope estimate."
            )
    return mesh


def calculate_volume(input_path: Path, closure: str = "reject") -> float:
    """Return the mesh volume in cubic units used by the STL."""
    return float(abs(load_stl_mesh(input_path, closure).volume))


def convert_stl(
    input_path: Path,
    output_path: Path,
    pitch: float,
    closure: str = "reject",
) -> dict[str, object]:
    """Voxelize an STL and write an NPZ volume with spatial metadata."""
    mesh = load_stl_mesh(input_path, closure)

    voxel_grid = mesh.voxelized(pitch).fill()
    volume = np.asarray(voxel_grid.matrix, dtype=np.uint8)
    origin = np.asarray(voxel_grid.transform[:3, 3], dtype=np.float64)
    geometric_volume = float(abs(mesh.volume))
    occupied_voxels = int(volume.sum())
    voxel_volume = occupied_voxels * pitch**3

    metadata = {
        "input": str(input_path),
        "closure": closure,
        "shape": list(volume.shape),
        "pitch": pitch,
        "origin": origin.tolist(),
        "occupied_voxels": occupied_voxels,
        "voxel_volume": voxel_volume,
        "geometric_volume": geometric_volume,
        "units": "the same units used by the STL",
    }
    np.savez_compressed(
        output_path,
        volume=volume,
        origin=origin,
        pitch=np.float64(pitch),
        metadata=json.dumps(metadata),
    )
    return metadata


def resolve_input_path(input_path: Path) -> Path:
    """Resolve an STL file path, accepting arbitrary filenames and directory inputs."""
    if input_path.is_file():
        if input_path.suffix.lower() != ".stl":
            raise ValueError(f"Input file is not an STL: {input_path}")
        return input_path

    if input_path.is_dir():
        stl_files = sorted(
            path for path in input_path.iterdir() if path.is_file() and path.suffix.lower() == ".stl"
        )
        if not stl_files:
            raise FileNotFoundError(f"No .stl files found in directory: {input_path}")
        if len(stl_files) > 1:
            raise ValueError(
                f"Multiple STL files found in {input_path}; please choose one explicitly."
            )
        return stl_files[0]

    raise FileNotFoundError(f"Input file not found: {input_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a closed STL mesh into a filled 3D voxel volume (.npz)."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input STL file or directory containing a single STL file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output NPZ path (default: input name with .npz)",
    )
    parser.add_argument(
        "--pitch",
        type=float,
        required=True,
        help="Voxel edge length in the STL's units",
    )
    parser.add_argument(
        "--closure",
        choices=("reject", "convex-hull"),
        default="reject",
        help="How to handle an open STL (default: reject; convex-hull estimates an outer envelope)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.pitch <= 0:
        raise SystemExit("--pitch must be greater than zero.")

    try:
        input_path = resolve_input_path(args.input)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(str(error)) from error

    output_path = args.output or input_path.with_suffix(".npz")
    try:
        metadata = convert_stl(input_path, output_path, args.pitch, args.closure)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print(f"{metadata['geometric_volume']:.12g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())