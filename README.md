Contents  
  - [Overview](#overview)
  - [Quick Start](#quick-start)
  - [Pipeline](#pipeline)
  - [Input Files](#input-files)
      1. [`config.yaml`](#config-yaml)
      2. [`samples.json`](#samples-json)
      3. [`assets/repeats.RNA.combined.hg38.mm10.bed`](#blacklist-bed)
  - [Output Files](#output-files)

# Overview 

This pipeline performs a tiered RNA alignment first to repetitive and
structural RNAs (rRNAs, snRNAs, snoRNAs, tRNAs), followed by unique
alignment to an appropriate reference genome.

## Quick Start

This pipeline assumes an existing
[conda](https://conda.io) installation and is written as a
[Snakemake](https://snakemake.github.io/) workflow. To install Snakemake
with conda, run

```         
conda env create -f envs/snakemake.yaml
conda activate snakemake
```

to create and activate a conda environment named `snakemake`. Once all
the [input files](#input-files) are ready, run the pipeline on a SLURM
server environment with

```         
./run_pipeline.sh
```

After the pipeline finishes, you can explore mapped alignments in
(`workup/alignments`) and calculate enrichments using
(`scripts/Enrichment.jar`) by passing the arguments:

```         
java -jar Enrichment.jar <sample.bam> <input.bam> <genefile.bed> <savename.windows> <sample read count> <input read count>
```

Other common usage notes:

-   To run the pipeline for input RNA samples, replace `Snakefile` with
    `Snakefile_for_input` under `--snakefile` in `/run_pipeline.sh`.

-   To run the pipeline for on a local computer (e.g., laptop), comment
    out or remove the `--cluster-config cluster.yaml` and
    `--cluster "sbatch ..."` arguments within `./run_pipeline.sh`, and
    set the number of jobs `-j <#>` to the number of local processors
    available.

-   `run_pipeline.sh` passes any additional arguments to snakemake. For
    example, run `./run_pipeline.sh --dry-run` to perform a dry run, or
    `./run_pipeline.sh --forceall` to force (re)execution of all rules
    regardless of past output.

## Pipeline

The pipeline relies on scripts written in Java, Bash, and Python.
Versions of Python are specified in conda environments described in
`envs/`, along with other third-party programs and packages that this
pipeline depends on.

Workflow

0.  Define samples and paths to FASTQ files (`fastq2json.py` or manually
    generate `samples.json`)
1.  Split FASTQ files into chunks for parallel processing (set
    `num_chunks` in `config.yaml`)
2.  Adaptor trimming (Trim Galore!)
3.  Tiered RNA alignment workflow:
    1.  Alignment to repetitive and structural RNAs (Bowtie2)
    2.  Convert unmapped reads to FASTQ files (samtools)
    3.  Alignment to unique RNAs in reference genome (STAR)
4.  Chromosome relabeling (add "chr") and filtering (removing
    non-canonical chromosomes)
5.  PCR deduplication (Picard)
6.  Repeat masking (based on UCSC blacklists)
7.  Merge all BAMs from initial chunking (samtools)

# Directory structures

We will refer to 4 directories:

1.  <a name="working-directory">Working directory</a>: We follow the
    [Snakemake
    documentation](https://snakemake.readthedocs.io/en/stable/project_info/faq.html#how-does-snakemake-interpret-relative-paths)
    in using the term "working directory".
    -   This is also where Snakemake creates a `.snakemake` directory
        within which it installs conda environments and keeps track of
        metadata regarding the pipeline.
        
2.  <a name="pipeline-directory">Pipeline directory</a>: where the
    software (including the `Snakefile` and scripts) resides
    -   `envs/`
    -   `scripts/`
    -   `fastq2json.py`
    -   `Snakefile`
    
3.  <a name="input-directory">Input directory</a>: where configuration
    and data files reside
    -   `assets/`
    -   `data/`
    -   `cluster.yaml`
    -   [`config.yaml`](#config-yaml): paths are specified relative to
        the [working directory](#working-directory)
    -   `samples.json`: paths are specified
        relative to the [working directory](#working-directory)
    -   `run_pipeline.sh`: the paths in the arguments
        `--snakefile <path to Snakefile>`,
        `--cluster-config <path to cluster.yaml>`, and
        `--configfile <path to config.yaml>` are relative to where you
        run `run_pipeline.sh`
        
4.  <a name="output-directory">Output or workup directory</a>
    (`workup/`): where to place this `workup` directory can be changed
    in [`config.yaml`](#config-yaml)
    -   `alignments/`
    -   `fastqs/`
    -   `logs/`
    -   `splitfq/`
    -   `trimmed/`

For reproducibility, we recommend keeping the pipeline, input, and
output directories together. In other words, the complete directory
should look like this GitHub repository with an extra `workup`
subdirectory created upon running this pipeline.

# Input Files 

1.  <a name="config-yaml">`config.yaml`</a>: YAML file containing the
    processing settings and paths of required input files. As noted
    [above](#input-directory), paths are specified relative to the
    [working directory](#working-directory).

    -   `output_dir`: path to create the output directory
        `<output_dir>/workup` within which all intermediate and output
        files are placed.
    -   `temp_dir`: path to a temporary directory, such as used by the
        `-T` option of [GNU
        sort](https://www.gnu.org/software/coreutils/manual/html_node/sort-invocation.html)
    -   `samples`: path to [`samples.json` file](#samples-json)
    -   `repeat_bed`:
        -   `mm10`: path to mm10 genomic regions to ignore, such as
            [UCSC blacklist regions](#blacklist-bed); reads mapping to
            these regions are masked
        -   `hg38`: path to hg38 genomic regions to ignore, such as
            [UCSC blacklist regions](#blacklist-bed); reads mapping to
            these regions are masked
        -   `mixed`: path to mixed hg38+mm10 genomic regions to ignore,
            such as [UCSC blacklist regions](#blacklist-bed); reads
            mapping to these regions are masked
    -   `bowtie2_index`:
        -   `mm10`: path to [Bowtie 2 genome index](#index-bt2) for the
            GRCm38 (mm10) build
        -   `hg38`: path to [Bowtie 2 genome index](#index-bt2) for the
            GRCh38 (hg38) build
        -   `mixed`: path to [Bowtie 2 genome index](#index-bt2) for the
            combined GRCh38 (hg38) and GRCm38 (mm10) build
    -   `assembly`: currently supports either `"mm10"`,`"hg38"`, or `mixed`
    -   `star_index`:
        -   `mm10`: path to [STAR genome index](#index-star) for the
            GRCm38 (mm10) build
        -   `hg38`: path to [STAR genome index](#index-star) for the
            GRCh38 (hg38) build
        -   `mixed`: path to [STAR genome index](#index-star) for the
            combined GRCh38 (hg38) and GRCm38 (mm10) build
    -   `num_chunks`: integer giving the number of chunks to split FASTQ
        files from each sample into for parallel processing
        
2.  <a name="samples-json">`samples.json`</a>: JSON file with the
    location of FASTQ files (read1, read2) to process.
    -   [`config.yaml`](#config-yaml) key to specify the path to this
        file: `samples`
    -   This can be prepared using
        `fastq2json.py --fastq_dir <path_to_directory_of_FASTQs>` or
        manually formatted as follows:
        ```{json}
        
        {
           "sample1": {
             "R1": ["<path_to_data>/sample1_R1.fastq.gz"],
             "R2": ["<path_to_data>/sample1_R2.fastq.gz"]
           },
           "sample2": {
             "R1": ["<path_to_data>/sample2_R1.fastq.gz"],
             "R2": ["<path_to_data>/sample2_R2.fastq.gz"]
           },
           ...
        }
        ```
        
    -   The pipeline (in particular, the script
        `scripts/bash/split_fastq.sh`) currently only supports one read
        1 (R1) and one read 2 (R2) FASTQ file per sample.
        -   If there are multiple FASTQ files per read orientation per
            sample (for example, if the same sample was sequenced
            multiple times, or it was split across multiple lanes during
            sequencing), the FASTQ files will first need to be
            concatenated together, and the paths to the concatenated
            FASTQ files should be supplied in the JSON file.
    -   Each sample is processed independently, generating independent
        BAM files.

3.  <a name="blacklist-bed">`assets/repeats.RNA.mm10.bed`,
    `assets/repeats.RNA.hg38.bed`,
    `assets/repeats.RNA.combined.hg38.mm10.bed`</a>: blacklisted
    repetitive genomic regions (i.e., poor alignments to rRNA regions)
    for CLIP and CLAP data.

4.  <a name="index-bt2">`assets/index_mm10/*.bt2`,
    `assets/index_hg38/*.bt2`, `assets/index_mixed/*.bt2`</a>: Bowtie 2
    genome index
    -   [`config.yaml`](#config-yaml) key to specify the path to the
        index:
        `bowtie2_index: {'mm10': <mm10_index_prefix>, 'hg38': <hg38_index_prefix>, 'mixed': <mixed_index_prefix}`
        -   Bowtie2 indexes for repetitive and structural RNAs may be
            custom generated from a FASTA file containing desired
            annotations.

5.  <a name="index-star">`assets/index_mm10/*.star`,
    `assets/index_hg38/*.star`, `assets/index_mixed/*.star`</a>: STAR
    genome index

    -   [`config.yaml`](#config-yaml) key to specify the path to the
        index:
        `star_index: {'mm10': <mm10_index_prefix>, 'hg38': <hg38_index_prefix>, 'mixed': <mixed_index_prefix}`
        -   Combined (`mixed`) genome build can be concatenated from standard GRCm38 (mm10) and GRCh38 (hg38) builds. 

# Output Files 

1.  Merged mapped BAM Files for individual proteins
    (`workup/alignments/*.merged.mapped.bam`)

2.  Window enrichment tables computed from CLIP/CLAP sample BAMs and
    input BAMs
    -   These are generated independently of the Snakemake pipeline.
    -   Example BED files used to survey enrichments are provided in the
        `assets` folder.

# Credits

Adapted from the
[SPRITE](https://github.com/GuttmanLab/sprite-pipeline), [RNA-DNA
SPRITE](https://github.com/GuttmanLab/sprite2.0-pipeline), and
[ChIP-DIP](https://github.com/GuttmanLab/chipdip-pipeline) pipelines by
**Isabel Goronzy** ([\@igoronzy](https://github.com/igoronzy)).

Other contributors 
- **Jimmy Guo** ([\@jk-guo](https://github.com/jk-guo)) 
- Mitchell Guttman ([\@mitchguttman](https://github.com/mitchguttman))
