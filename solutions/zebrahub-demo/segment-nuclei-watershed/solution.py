"""Study-authored Album solution: CPU 3D nuclear instance segmentation."""

from album.runner.api import setup


ENV = """
channels:
  - conda-forge
dependencies:
  - python=3.12
  - pip
  - pip:
    - numpy==2.5.3
    - scipy==1.18.1
    - scikit-image==0.26.0
    - tifffile==2026.9.20
"""


def run():
    import json
    from pathlib import Path

    import numpy as np
    import tifffile
    from album.runner.api import get_args
    from scipy import ndimage as ndi
    from skimage.feature import peak_local_max
    from skimage.segmentation import watershed

    args = get_args()
    image_path, source_path, labels_path = map(Path, (args.image_path, args.source_path, args.labels_path))
    image = tifffile.imread(image_path)
    source = json.loads(source_path.read_text())
    assert image.ndim == 3 and image.dtype == np.uint16
    assert tuple(source["shape"]) == image.shape
    spacing = np.array(source["spacing_um_zyx"], dtype=float)
    assert np.all(spacing > 0)
    sigma = tuple(map(float, (args.sigma_z, args.sigma_y, args.sigma_x)))
    threshold = float(args.threshold)
    min_distance = int(args.min_distance)
    peak_threshold_um = float(args.peak_threshold_um)
    min_size = int(args.min_size)
    assert all(s > 0 for s in sigma) and min_distance > 0 and peak_threshold_um > 0 and min_size > 0

    smoothed = ndi.gaussian_filter(image.astype(np.float32), sigma)
    mask = smoothed > threshold
    distance = ndi.distance_transform_edt(mask, sampling=spacing)
    peaks = peak_local_max(distance, min_distance=min_distance,
                           threshold_abs=peak_threshold_um, exclude_border=False)
    assert len(peaks) > 0, "no nuclei seeds found"
    seeds = np.zeros(image.shape, dtype=np.int32)
    seeds[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    raw_labels = watershed(-distance, seeds, mask=mask)
    sizes = np.bincount(raw_labels.ravel())
    keep = np.flatnonzero(sizes >= min_size)
    keep = keep[keep != 0]
    assert len(keep) > 0, "no objects meet minimum size"
    remap = np.zeros(len(sizes), dtype=np.uint32)
    remap[keep] = np.arange(1, len(keep) + 1, dtype=np.uint32)
    labels = remap[raw_labels]
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(labels_path, labels)
    metadata = {
        "method": "Gaussian threshold, distance transform, local-maxima watershed",
        "image_path": str(image_path), "source_path": str(source_path),
        "labels_path": str(labels_path), "sigma_voxels_zyx": sigma,
        "threshold": threshold, "min_distance_voxels": min_distance,
        "peak_threshold_um": peak_threshold_um, "min_size_voxels": min_size,
        "seed_count": len(peaks), "object_count": len(keep),
    }
    (labels_path.parent / "segmentation.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"labels": str(labels_path), "objects": len(keep)}))


setup(
    group="zebrahub-demo", name="segment-nuclei-watershed", version="0.1.0",
    album_api_version="0.7.1", run=run,
    title="Segment nuclei in a 3D ZebraHub image on CPU",
    description="Study-authored CPU demonstration solution. Gaussian threshold and watershed; no training or access to reference tracks.",
    solution_creators=["Album manuscript demonstration team"],
    tags=["demonstration", "segmentation", "nuclei", "cpu"],
    args=[
        {"name": "image_path", "type": "string", "required": True, "description": "Input 3D uint16 TIFF."},
        {"name": "source_path", "type": "string", "required": True, "description": "Source metadata JSON with voxel spacing."},
        {"name": "labels_path", "type": "string", "required": True, "description": "Output 3D uint32 labels TIFF."},
        {"name": "sigma_z", "type": "float", "required": True, "description": "Gaussian sigma along Z, voxels."},
        {"name": "sigma_y", "type": "float", "required": True, "description": "Gaussian sigma along Y, voxels."},
        {"name": "sigma_x", "type": "float", "required": True, "description": "Gaussian sigma along X, voxels."},
        {"name": "threshold", "type": "float", "required": True, "description": "Intensity threshold after smoothing."},
        {"name": "min_distance", "type": "integer", "required": True, "description": "Minimum separation of local maxima, voxels."},
        {"name": "peak_threshold_um", "type": "float", "required": True, "description": "Minimum distance-transform peak height, micrometers."},
        {"name": "min_size", "type": "integer", "required": True, "description": "Minimum object size, voxels."},
    ],
    dependencies={"environment_file": ENV},
)
