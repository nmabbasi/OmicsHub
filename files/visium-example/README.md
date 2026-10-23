# One Visium input directory for R and Python

This example prepares the public 10x Genomics **V1_Adult_Mouse_Brain** conventional Visium sample from the Space Ranger 1.1.0 download path. It is not Visium HD.

Download `prepare_inputs.py` into an empty analysis project and run with Python 3.10 or later:

```sh
python3 prepare_inputs.py --output data/visium/V1_Adult_Mouse_Brain
```

The script uses only Python's standard library. It downloads about 30 MB, verifies both published fingerprints, safely extracts the spatial archive and refuses to overwrite an existing destination. If a source checksum changes, stop and inspect the new upstream dataset rather than removing the check.

The same output directory is used by both readers:

```text
data/visium/V1_Adult_Mouse_Brain/
    filtered_feature_bc_matrix.h5
    spatial.tar.gz
    source-manifest.json
    spatial/
        tissue_positions_list.csv
        scalefactors_json.json
        tissue_lowres_image.png
        tissue_hires_image.png
        ...
```

Python uses `sq.read.visium("data/visium/V1_Adult_Mouse_Brain", counts_file="filtered_feature_bc_matrix.h5")`. R uses `Load10X_Spatial(data.dir="data/visium/V1_Adult_Mouse_Brain", filename="filtered_feature_bc_matrix.h5")`.

## What was checked

Both source URLs were downloaded, their SHA256 checksums were recorded, the HDF5 file signature was checked, and preparation/extraction of the actual downloads was executed. The archive includes the images, scale factors and legacy `tissue_positions_list.csv` expected by this sample. This is an **input-preparation check only**: neither the Squidpy nor Seurat analysis/normalization/plotting branch was run in this check, and no biological finding is claimed.

`verified-inputs.json` preserves the original source URLs, sizes and hashes. A new execution writes its own `source-manifest.json` with the preparation timestamp. The input archives are not redistributed in this repository; they are downloaded from 10x Genomics.

For reader/API setup see the official [Squidpy Visium reader](https://squidpy.readthedocs.io/en/stable/api/squidpy.read.visium.html) and [Seurat Load10X_Spatial](https://satijalab.org/seurat/reference/load10x_spatial).
