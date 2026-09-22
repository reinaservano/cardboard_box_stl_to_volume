"""Convert a closed STL mesh into a filled 3D voxel volume."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import trimesh


STL_UNIT_TO_LITERS = {
    "mm": 1e-6,
    "cm": 1e-3,
    "m": 1e3,
}


def convert_stl(
    input_path: Path,
    output_path: Path,
    pitch: float,
    closure: str = "reject",
    stl_units: str = "mm",
) -> dict[str, object]:
    """Voxelize an STL and write an NPZ volume with spatial metadata."""
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
                "The STL is not watertight. Use --closure convex-hull for an outer-envelope estimate."
            )

    voxel_grid = mesh.voxelized(pitch).fill()
    volume = np.asarray(voxel_grid.matrix, dtype=np.uint8)
    origin = np.asarray(voxel_grid.transform[:3, 3], dtype=np.float64)
    geometric_volume = float(abs(mesh.volume))
    occupied_voxels = int(volume.sum())
    voxel_volume = occupied_voxels * pitch**3
    liters_per_cubic_unit = STL_UNIT_TO_LITERS[stl_units]

    metadata = {
        "input": str(input_path),
        "closure": closure,
        "shape": list(volume.shape),
        "pitch": pitch,
        "origin": origin.tolist(),
        "occupied_voxels": occupied_voxels,
        "voxel_volume": voxel_volume,
        "geometric_volume": geometric_volume,
        "voxel_volume_liters": voxel_volume * liters_per_cubic_unit,
        "geometric_volume_liters": geometric_volume * liters_per_cubic_unit,
        "stl_units": stl_units,
    }
    np.savez_compressed(
        output_path,
        volume=volume,
        origin=origin,
        pitch=np.float64(pitch),
        metadata=json.dumps(metadata),
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a closed STL mesh into a filled 3D voxel volume (.npz)."
    )
    parser.add_argument("input", type=Path, help="Input STL file")
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
    parser.add_argument(
        "--stl-units",
        choices=tuple(STL_UNIT_TO_LITERS),
        default="mm",
        help="Units used by the STL coordinates (default: mm)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.pitch <= 0:
        raise SystemExit("--pitch must be greater than zero.")

    if not args.input.is_file():
        raise SystemExit(f"Input file not found: {args.input}")

    output_path = args.output or args.input.with_suffix(".npz")
    try:
        metadata = convert_stl(args.input, output_path, args.pitch, args.closure, args.stl_units)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print(f"Wrote: {output_path}")
    print(f"Closure: {metadata['closure']}")
    print(f"Grid: {metadata['shape'][0]} x {metadata['shape'][1]} x {metadata['shape'][2]}")
    print(f"Occupied voxels: {metadata['occupied_voxels']}")
    print(f"Voxel volume: {metadata['voxel_volume']:.6g} cubic STL units")
    print(f"Geometric volume: {metadata['geometric_volume']:.6g} cubic STL units")
    print(f"Voxelized volume: {metadata['voxel_volume_liters']:.6g} liters")
    print(f"Geometric volume: {metadata['geometric_volume_liters']:.6g} liters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())