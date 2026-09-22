import tempfile
import unittest
from pathlib import Path

import numpy as np
import trimesh

from stl_to_volume import resolve_input_path


class ResolveInputPathTests(unittest.TestCase):
    def test_resolve_input_path_accepts_any_stl_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            mesh_dir = Path(temp_dir) / "meshes"
            mesh_dir.mkdir()
            mesh_path = mesh_dir / "custom_model_name.STL"
            trimesh.creation.box().export(mesh_path)

            resolved = resolve_input_path(mesh_dir)

            self.assertEqual(resolved, mesh_path)
            self.assertTrue(resolved.is_file())
            self.assertEqual(resolved.suffix.lower(), ".stl")

            np.savez_compressed(mesh_dir / "output.npz", volume=np.array([1], dtype=np.uint8))


if __name__ == "__main__":
    unittest.main()
