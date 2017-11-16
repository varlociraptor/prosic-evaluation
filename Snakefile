import pandas as pd

from snakemake.remote import FTP

ftp = FTP.RemoteProvider()


configfile: "config.yaml"


gdc_manifest = pd.read_table(config["gdc-manifest"])
units = pd.DataFrame({
    "sample": gdc_manifest.filename.str.slice(5, 33),
    "path": expand("gdc-data/{bam}", bam=gdc_manifest.filename)})
units.index = gdc_manifest.id
CHROMOSOMES = list(range(1,23)) + ["M", "X", "Y"]


def get_bams(wildcards):
    tissues = ["tumor", "normal"]
    run = config["runs"][wildcards.run]
    return expand("mapped-{mapper}/{dataset}.{tissue}.{ref}.bam",
                  dataset=run["dataset"],
                  tissue=tissues,
                  ref=run["ref"],
                  mapper=run["mapper"])


def get_bais(wildcards):
    return ["{}.bai".format(f) for f in get_bams(wildcards)]


def get_ref(wildcards):
    ref = config["runs"][wildcards.run]["ref"]
    return config["ref"][ref]["fasta"]


def get_targets(run):
    t = expand("adhoc-{caller}/{run}.all.bcf",
               caller=config["caller"],
               run=run)
    t.extend(expand("lancet/{run}.all.bcf", run=run))
    t.extend(expand("prosic-{caller}/{run}.all.bcf",
                    run=run, caller=config["caller"]))
    return t


wildcard_constraints:
    caller="|".join(config["caller"])
    chrom="|".join(CHROMOSOMES)


rule all:
    input:
        [get_targets(run) for run in config["runs"]]


rule test:
    input:
        get_targets("test")


include: "rules/mapping.smk"
include: "rules/delly.smk"
include: "rules/pindel.smk"
include: "rules/lancet.smk"
include: "rules/prosic.smk"
include: "rules/adhoc.smk"
