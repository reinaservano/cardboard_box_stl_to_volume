# STL to 3D volume

Convert a closed box or other watertight STL mesh into a filled 3D voxel volume.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Convert

`--pitch` is the voxel edge length in the same units as the STL. Smaller values
produce a finer grid and use more memory.

```powershell
python stl_to_volume.py .\box.stl --pitch 1 --output .\box_volume.npz
```

For an open scan such as a box with a missing wall or hole, use the explicit
outer-envelope estimate:

```powershell
python stl_to_volume.py .\box.stl --pitch 5 --closure convex-hull --output .\box_volume.npz
```

This closes the scan with its convex hull. It is a reconstruction estimate,
not a measurement of the original missing surface; the metadata records the
closure method.

The compressed NPZ contains:

- `volume`: a `uint8` array with shape `(x, y, z)`; `1` means occupied.
- `origin`: world-space coordinate of the grid origin.
- `pitch`: voxel edge length.
- `metadata`: JSON summary, including geometric and voxelized volume.

Read it with NumPy:

```python
import numpy as np

data = np.load("box_volume.npz")
volume = data["volume"]
print(volume.shape, data["pitch"])
```

## GUI volume calculator

Launch the desktop GUI to upload an STL and calculate its volume in liters:

```powershell
python volume_gui.py
```

Choose the units used by the STL before reading the result. STL files do not
store dependable unit metadata, so the default is millimeters. Watertight
meshes are measured directly; for an open scan, enable the convex-hull option
to calculate an outer-envelope estimate.

By default, the STL must be watertight so the inside can be filled
unambiguously. The `convex-hull` mode is available when an open scan must still
produce a closed approximation.