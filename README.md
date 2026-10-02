# album-mcp-catalog

This is an Album catalog for the ZebraHub remote-image example in the Album paper (Supplementary Section C, Fig. C1). It contains three study-authored demonstration solutions that are run in order through Album MCP:

| Solution | Role |
| --- | --- |
| `zebrahub-demo:retrieve-zarr-chunk:0.1.0` | Downloads one public ZebraHub OME-Zarr chunk over HTTPS, checks its SHA-256, and writes `image.tif` and `source.json` |
| `zebrahub-demo:segment-nuclei-watershed:0.1.0` | Segments nuclei on the CPU with Gaussian smoothing, thresholding, and distance-transform watershed, and writes `labels.tif` |
| `zebrahub-demo:measure-and-count:0.2.0` | Measures each object, writes `objects.csv` and `overlay.png`, and compares the object count with published track positions. Installing it downloads the ZebraHub track table (487 MB) once and checks its SHA-256. Each run extracts the rows for the image's time point. |

The catalog's internal name is `zebrahub-demo`; that name appears in the solution coordinates. Commit `4e7abb3` is the catalog state used for the paper's recorded runs. Those runs used `measure-and-count:0.1.0`, which needs the t=425 track extract supplied separately; 0.1.0 remains in the catalog for that record. The three solutions were written for this example and are not reused community solutions.

## Add the catalog

```bash
album add-catalog https://github.com/album-app/album-mcp-catalog.git
```

From an MCP client, call `album_add_catalog` with the same URL.

## Claude Code

Set up the Album MCP server as described in the [album-mcp README](https://gitlab.com/album-app/album-mcp#using-with-claude-code). Then ask, for example:

> Add the Album catalog at https://github.com/album-app/album-mcp-catalog.git, inspect its solutions and their arguments, then retrieve ZebraHub `ZSNS001_tail.ome.zarr` at level 0, time point 425, channel 0, chunk (z,y,x) = (1,1,1), segment the nuclei, and measure them against the published tracks. Save the outputs in `<directory>`.

With the parameters used in the paper (sigma_z=0.8, sigma_y=1.3, sigma_x=1.3, threshold=40, min_distance=4, peak_threshold_um=1.5, min_size=40), the run yields 1,240 objects and 1,623 track positions in the chunk.
