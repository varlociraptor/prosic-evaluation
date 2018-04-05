import pandas as pd
import numpy as np
import seaborn as sns
import math


def load_variants(path, minlen=None, maxlen=None, vartype=None, constrain=None, min_af=None, max_af=None):
    variants = pd.read_table(path, header=[0, 1])
    variants = variants["VARIANT"]
    variants["CHROM"] = variants["CHROM"].astype(str)

    variants.index = np.arange(variants.shape[0])

    # constrain type
    if vartype == "DEL":
        isdel = (variants["REF"].str.len() > 1) & (variants["ALT"].str.len() == 1)
        if "SVTYPE" in variants.columns:
            variants = variants[(variants["SVTYPE"].astype(str) == "DEL") | (isdel & variants["SVTYPE"].isnull())]
        else:
            variants = variants[isdel]
    elif vartype == "INS":
        isins = (variants["REF"].str.len() == 1) & (variants["ALT"].str.len() > 1)
        if "SVTYPE" in variants.columns:
            variants = variants[(variants["SVTYPE"].astype(str) == "INS") | (isins & variants["SVTYPE"].isnull())]
        else:
            variants = variants[isins]
    else:
        assert False, "Unsupported variant type"

    # constrain length
    if "SVLEN" not in variants.columns or variants["SVLEN"].isnull().any():
        if not (variants.columns == "END").any() or variants["END"].isnull().any():
            variants["SVLEN"] = (variants["ALT"].str.len() - variants["REF"].str.len()).abs()
            print("REF ALT comp")
        else:
            print("use END")
            variants["SVLEN"] = variants["END"] - variants["POS"]
            print(variants[["SVLEN", "POS", "END", "MATCHING"]].head())
    if minlen is not None and maxlen is not None:
        variants = variants[(variants["SVLEN"].abs() >= minlen) & (variants["SVLEN"].abs() < maxlen)]

    # only autosomes
    variants = variants[variants["CHROM"].str.match(r"(chr)?[0-9]+")]

    if constrain is not None:
        valid = (variants["MATCHING"] < 0) | (variants["MATCHING"].isin(constrain.index))
        variants = variants[valid]

    if min_af is not None and max_af is not None:
        valid = (variants["AF"] <= max_af) & (variants["AF"] >= min_af)
        variants = variants[valid]

    print("total variants", variants.shape[0])
    if "MATCHING" in variants.columns:
        print("matching variants", (variants["MATCHING"] >= 0).sum())

    return variants


def precision(calls):
    p = calls.shape[0]
    if p == 0:
        return 1.0
    tp = np.count_nonzero(calls.is_tp)
    precision = tp / p
    return precision


def recall(calls, truth):
    p = calls.shape[0]
    if p == 0:
        return 0.0
    matches = calls.loc[calls.MATCHING.isin(truth.index), "MATCHING"]
    tp = calls[calls.is_tp].MATCHING.unique().size
    t = truth.shape[0]
    recall = tp / t
    return recall

def get_colors(config):
    callers = [caller for caller in config["caller"] if caller != "prosic"]
    palette = sns.color_palette("colorblind", n_colors=len(callers))
    palette = sns.color_palette("tab10", n_colors=len(callers))
    return {caller: c for caller, c in zip(callers, palette)}


def phred_scale(prob):
    return -10 * math.log10(prob)
