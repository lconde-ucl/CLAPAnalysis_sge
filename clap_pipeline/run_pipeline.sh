#!/bin/bash

snakemake \
--snakefile Snakefile \
--use-conda \
--rerun-incomplete \
-j 2 \
--configfile config.yaml \
--cluster-config cluster.yaml \
--cluster "qsub -pe smp {cluster.cpus} \
-l h_rt={cluster.time} \
-l mem={cluster.mem} \
-o {cluster.output} \
-e {cluster.error} \
-V -cwd"


