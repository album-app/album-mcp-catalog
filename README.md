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

Set up the Album MCP server as described in the [album-mcp README](https://gitlab.com/album-app/album-mcp#using-with-claude-code). Then start Claude Code and give it this prompt, replacing `<output directory>` with an absolute path:

```text
Use the Album tools. Add the Album catalog at https://github.com/album-app/album-mcp-catalog.git if it is not already registered, then inspect the available solutions and their arguments before running anything.

Analyze one public ZebraHub image volume:
1. Retrieve ZSNS001_tail.ome.zarr from https://public.czbiohub.org/royerlab/zebrahub/imaging/single-objective/ZSNS001_tail.ome.zarr/ at resolution level 0, time point 425, channel 0, chunk (z,y,x) = (1,1,1). The compressed chunk must have SHA-256 0030b18d5f382045612e397c2e41059b5c3b229583ee5f97aec691b4ca6bbb76.
2. Segment nuclei on the CPU with sigma_z=0.8, sigma_y=1.3, sigma_x=1.3, threshold=40, min_distance=4, peak_threshold_um=1.5, min_size=40.
3. Measure the segmented objects and compare their count with the published ZebraHub track positions for the same time point.

Save all outputs in <output directory>. When finished, report the solution versions you used, the exact arguments of each run, the output files, the number of segmented objects and track positions, and any calls that failed.
```

The expected result is 1,240 segmented objects and 1,623 track positions in the chunk. The first run installs three solution environments and downloads the 487 MB track table, so it takes a few minutes.
