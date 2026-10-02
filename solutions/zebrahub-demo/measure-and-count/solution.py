"""Study-authored Album solution: measurements, overlay, and count comparison."""

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
    - pillow==12.3.0
"""


def run():
    import csv
    import hashlib
    import json
    from pathlib import Path

    import numpy as np
    import tifffile
    from album.runner.api import get_args
    from PIL import Image
    from scipy import ndimage as ndi
    from skimage.segmentation import find_boundaries

    args = get_args()
    image_path, labels_path, source_path, reference_path = map(
        Path, (args.image_path, args.labels_path, args.source_path, args.reference_path)
    )
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    image, labels = tifffile.imread(image_path), tifffile.imread(labels_path)
    source = json.loads(source_path.read_text())
    assert image.ndim == labels.ndim == 3 and image.shape == labels.shape
    assert image.dtype == np.uint16 and labels.dtype.kind in "ui"
    assert tuple(source["shape"]) == image.shape
    assert labels.min() == 0 and labels.max() > 0
    assert hashlib.sha256(image.tobytes()).hexdigest() == source["decoded_image_sha256"]
    assert hashlib.sha256((source_path.parent / "source_chunk.bin").read_bytes()).hexdigest() == source["source_chunk_sha256"]
    reference_hash = hashlib.sha256(reference_path.read_bytes()).hexdigest()
    assert reference_hash == args.expected_reference_sha256.lower(), "reference CSV checksum mismatch"
    spacing = np.array(source["spacing_um_zyx"], dtype=float)
    start = np.array(source["chunk_start_zyx"], dtype=float)
    assert spacing.shape == start.shape == (3,) and np.all(spacing > 0)

    ids = np.unique(labels)
    ids = ids[ids > 0]
    counts = np.bincount(labels.ravel().astype(np.int64))
    intensity = np.bincount(labels.ravel().astype(np.int64), weights=image.ravel())
    centers = np.array(ndi.center_of_mass(np.ones(image.shape), labels, ids))
    centers_um = (centers + start) * spacing
    csv_path = out / "objects.csv"
    with csv_path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("label", "voxel_count", "volume_um3", "z_um", "y_um", "x_um", "mean_intensity"))
        for ident, center in zip(ids, centers_um):
            ident = int(ident)
            writer.writerow((ident, int(counts[ident]), float(counts[ident] * np.prod(spacing)),
                             *map(float, center), float(intensity[ident] / counts[ident])))

    projection = image.max(axis=0)
    low, high = np.percentile(projection, (1, 99.5))
    assert high > low
    gray = np.uint8(np.clip((projection - low) / (high - low), 0, 1) * 255)
    overlay = np.repeat(gray[..., None], 3, axis=2)
    boundary = find_boundaries(labels.max(axis=0), mode="outer")
    assert boundary.any()
    overlay[boundary] = (255, 40, 40)
    Image.fromarray(overlay).save(out / "overlay.png")

    with reference_path.open(newline="") as file:
        tracks = list(csv.DictReader(file))
    assert tracks and all(float(track["t"]) == float(source["t"]) for track in tracks)
    physical = np.array([[float(track[k]) for k in ("z", "y", "x")] for track in tracks])
    local_voxels = physical / spacing - start
    inside = np.all((local_voxels >= 0) & (local_voxels < image.shape), axis=1)
    reference_count = int(inside.sum())
    assert reference_count > 0
    difference = len(ids) - reference_count
    report = {
        "passed": True, "image_shape": image.shape, "image_dtype": str(image.dtype),
        "label_dtype": str(labels.dtype), "objects": len(ids), "csv_rows": len(ids),
        "reference_t": source["t"], "reference_rows": len(tracks),
        "reference_in_chunk": reference_count, "reference_sha256": reference_hash,
        "count_difference": difference,
        "relative_count_difference": difference / reference_count,
        "overlay_shape": overlay.shape,
        "note": "Published track count comparison; no mask accuracy claim.",
    }
    (out / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"measurements": str(csv_path), "overlay": str(out / "overlay.png"),
                      "validation": str(out / "validation.json"), "objects": len(ids),
                      "reference_count": reference_count}))


setup(
    group="zebrahub-demo", name="measure-and-count", version="0.1.0",
    album_api_version="0.7.1", run=run,
    title="Measure nuclei and compare count with published tracks",
    description="Study-authored CPU demonstration solution. Saves object measurements, a projected label overlay, and count validation.",
    solution_creators=["Album manuscript demonstration team"],
    tags=["demonstration", "measurements", "validation", "microscopy"],
    args=[
        {"name": "image_path", "type": "string", "required": True, "description": "Input 3D uint16 TIFF."},
        {"name": "labels_path", "type": "string", "required": True, "description": "Input 3D integer labels TIFF."},
        {"name": "source_path", "type": "string", "required": True, "description": "Source metadata JSON."},
        {"name": "reference_path", "type": "string", "required": True, "description": "Separately supplied t=425 track CSV extract."},
        {"name": "expected_reference_sha256", "type": "string", "required": True, "description": "Expected SHA-256 of reference CSV."},
        {"name": "output_dir", "type": "string", "required": True, "description": "Output directory for CSV, overlay, and validation report."},
    ],
    dependencies={"environment_file": ENV},
)
