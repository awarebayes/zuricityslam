#!/bin/bash
bsub -o short_walk_zurich_test_sequential_fps2.out -n 16 -R "rusage[mem=4096,ngpus_excl_p=2]" "python3 src/mapping/single_video_pipeline.py --dataset datasets/short_walk_zurich --outputs outputs/short_walk_zurich_sequential_fps2 --num_loc 10"
