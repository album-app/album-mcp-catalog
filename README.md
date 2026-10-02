# album-mcp-catalog

This is an Album catalog for the ZebraHub remote-image example in the Album paper (Supplementary Section C, Fig. C1). It contains three study-authored demonstration solutions that are run in order through Album MCP:

| Solution | Role |
| --- | --- |
| `zebrahub-demo:retrieve-zarr-chunk:0.1.0` | Downloads one public ZebraHub OME-Zarr chunk over HTTPS, checks its SHA-256, and writes `image.tif` and `source.json` |
| `zebrahub-demo:segment-nuclei-watershed:0.1.0` | Segments nuclei on the CPU with Gaussian smoothing, thresholding, and distance-transform watershed, and writes `labels.tif` |
| `zebrahub-demo:measure-and-count:0.1.0` | Measures each object, writes `objects.csv` and `overlay.png`, and compares the object count with published track positions |

The catalog's internal name is `zebrahub-demo`; that name appears in the solution coordinates. Commit `4e7abb3` is the catalog state used for the paper's recorded runs. The three solutions were written for this example and are not reused community solutions.

## Add the catalog

```bash
album add-catalog https://github.com/album-app/album-mcp-catalog.git
```

From an MCP client, call `album_add_catalog` with the same URL.
