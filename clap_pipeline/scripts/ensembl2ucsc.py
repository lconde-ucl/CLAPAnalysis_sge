#!/usr/bin/python
import argparse
import pysam
import assembly

def main():
    args = parse_arguments()
    do(args)

def parse_arguments():
    parser = argparse.ArgumentParser(description =
            "This program adds chr to alignments.")
    parser.add_argument('-i', '--input', action = 'store', metavar = 'FILE',
                        help = 'Input BAM file')
    parser.add_argument('-o', '--output', action = 'store', metavar = 'FILE',
                        help = 'Output BAM file containing reads that pass')
    parser.add_argument('--assembly', metavar = "ASSEMBLY",
                        action = "store",
                        choices = ["mixed", "mm9", "mm10", "hg19", "hg38", "none"],
                        default = "none",
                        help = "The genome assembly. (default mm9)")
    return parser.parse_args()


def add_chr_to_bam_header(bam_path, chroms):
    '''Add chr to alignments done with ensembl reference

        Args:
            bam_path (str): path to bam file
            chroms (list): list of core chromosomes to retain in the header

        Note:
            Assumes main chromosomes come first followed by alt, that will be removed 

        Return:
            header dict for pysam
    '''
    #get bam header
    with pysam.AlignmentFile(bam_path, 'rb') as input_file:
        bam_header = input_file.header.to_dict()
    #edit bam header
    for n, i in enumerate(bam_header['SQ']):
        chrom = i['SN']
        if 'chr' not in chrom:
            if 'chr' + chrom in chroms:
                bam_header['SQ'][n]['SN'] = 'chr' + chrom
            elif chrom == 'MT':
                bam_header['SQ'][n]['SN'] = 'chrM'

    return(bam_header)

def do(args):
    if args.assembly != 'none':
        #filter out reads that do not map to main assembly
        chroms = list(assembly.build(args.assembly, 1)._chromsizes.keys())
        #add chr to bam header
        bam_header = add_chr_to_bam_header(args.input, chroms)

    input_file = pysam.AlignmentFile(args.input, "rb")
    output_file = pysam.AlignmentFile(args.output, "wb", header = bam_header)

    for read in input_file.fetch(until_eof = True):
        output_file.write(read)
    output_file.close()


if __name__ == "__main__":
    main()
