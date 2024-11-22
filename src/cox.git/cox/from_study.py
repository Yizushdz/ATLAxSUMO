from glob import glob
import os
from argparse import ArgumentParser
import shutil
'''utility script designed to import experiment directories from a study into 
a central output directory. It helps organize and manage experiment results, 
ensuring that they are easily accessible for analysis and comparison'''

def main():
    parser = ArgumentParser(description='Import cox directories from a study')
    parser.add_argument('-d', '--dir', type=str)
    parser.add_argument('-o', '--output-dir', type=str)
    parser.add_argument('-s', '--output-subdir', type=str, default='output/cox')
    args = parser.parse_args()

    if args.output_subdir[0] == '/':
        args = args[1:]
    if args.output_subdir[-1] == '/':
        args = args[:-1]

    for exp_dir in glob("%s/*/%s/*/" % (args.dir, args.output_subdir)):
        exp_name = exp_dir[:-1].split("/")[-1]
        assert os.path.exists(args.output_dir)
        shutil.copytree(exp_dir, os.path.join(args.output_dir, exp_name))

if __name__=='__main__':
    main()
