"""Study-authored Album solution: retrieve one remote OME-Zarr chunk."""

from album.runner.api import setup


ENV = """
channels:
  - conda-forge
dependencies:
  - python=3.12
  - pip
  - pip:
    - numpy==2.5.3
    - numcodecs==0.15.1
    - tifffile==2026.9.20
"""


def run():
    import hashlib
    import json
    from datetime import datetime, timezone
    from pathlib import Path
    from urllib.request import urlopen

    import numpy as np
    import tifffile
    from album.runner.api import get_args
    from numcodecs import get_codec

    args = get_args()
    root = args.zarr_uri.rstrip("/") + "/"
    level, t, c = (int(args.level), int(args.timepoint), int(args.channel))
    cz, cy, cx = (int(args.chunk_z), int(args.chunk_y), int(args.chunk_x))
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    def fetch(url):
        with urlopen(url, timeout=120) as response:
            return response.read()

    zattrs_bytes = fetch(root + ".zattrs")
    zarray_bytes = fetch(root + str(level) + "/.zarray")
    zattrs, zarray = json.loads(zattrs_bytes), json.loads(zarray_bytes)
    assert zarray["zarr_format"] == 2
    assert zarray["order"] == "C" and zarray["filters"] is None
    assert zarray["dimension_separator"] == "/"
    assert [a["name"] for a in zattrs["multiscales"][0]["axes"]] == ["t", "c", "z", "y", "x"]
    chunks, shape = zarray["chunks"], zarray["shape"]
    indices = (t, c, cz, cy, cx)
    assert all(0 <= i * k < s for i, k, s in zip(indices, chunks, shape))
    assert chunks[0] == chunks[1] == 1
    chunk_key = "/".join(map(str, indices))
    url = root + str(level) + "/" + chunk_key
    compressed = fetch(url)
    digest = hashlib.sha256(compressed).hexdigest()
    assert digest == args.expected_sha256.lower(), "remote chunk SHA-256 mismatch"
    (out / "source_chunk.bin").write_bytes(compressed)

    decoded = get_codec(zarray["compressor"]).decode(compressed)
    chunk_shape = tuple(min(k, s - i * k) for i, k, s in zip(indices, chunks, shape))
    image = np.frombuffer(decoded, dtype=np.dtype(zarray["dtype"])).reshape(chunk_shape)[0, 0]
    assert image.ndim == 3 and image.dtype == np.uint16
    tifffile.imwrite(out / "image.tif", image)
    (out / "zarr_root_zattrs.json").write_bytes(zattrs_bytes)
    (out / "zarr_level_zarray.json").write_bytes(zarray_bytes)
    scale = zattrs["multiscales"][0]["datasets"][level]["coordinateTransformations"][0]["scale"]
    source = {
        "zarr_uri": root, "chunk_uri": url, "level": level, "t": t, "c": c,
        "chunk_index_zyx": [cz, cy, cx],
        "chunk_start_zyx": [cz * chunks[2], cy * chunks[3], cx * chunks[4]],
        "axes": ["z", "y", "x"], "shape": list(image.shape),
        "spacing_um_zyx": scale[2:],
        "source_chunk_sha256": digest,
        "decoded_image_sha256": hashlib.sha256(decoded).hexdigest(),
        "zattrs_sha256": hashlib.sha256(zattrs_bytes).hexdigest(),
        "zarray_sha256": hashlib.sha256(zarray_bytes).hexdigest(),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "source.json").write_text(json.dumps(source, indent=2) + "\n")
    print(json.dumps({"image": str(out / "image.tif"), "source": str(out / "source.json"), "shape": image.shape}))


setup(
    group="zebrahub-demo", name="retrieve-zarr-chunk", version="0.1.0",
    album_api_version="0.7.1", run=run,
    title="Retrieve a checksum-pinned remote OME-Zarr chunk",
    description="Study-authored CPU demonstration solution. Retrieves one 3D ZebraHub OME-Zarr chunk and saves TIFF plus source metadata.",
    solution_creators=["Album manuscript demonstration team"],
    tags=["demonstration", "remote-data", "ome-zarr", "microscopy"],
    args=[
        {"name": "zarr_uri", "type": "string", "required": True, "description": "Public HTTPS OME-Zarr root URI."},
        {"name": "level", "type": "integer", "required": True, "description": "Multiscale array level."},
        {"name": "timepoint", "type": "integer", "required": True, "description": "Timepoint index."},
        {"name": "channel", "type": "integer", "required": True, "description": "Channel index."},
        {"name": "chunk_z", "type": "integer", "required": True, "description": "Z chunk index."},
        {"name": "chunk_y", "type": "integer", "required": True, "description": "Y chunk index."},
        {"name": "chunk_x", "type": "integer", "required": True, "description": "X chunk index."},
        {"name": "expected_sha256", "type": "string", "required": True, "description": "Expected SHA-256 of the compressed remote chunk."},
        {"name": "output_dir", "type": "string", "required": True, "description": "Directory for image.tif and source.json."},
    ],
    dependencies={"environment_file": ENV},
)
