#!/bin/bash
#BSUB -J hierarchical_mapper
#BSUB -n 32
#BSUB -R rusage[mem=4096,ngpus_excl_p=1]
#BSUB -W 24:00             
####### -o .logs/hierarchical_mapper_%J.log

BASE=/cluster/project/infk/courses/252-0579-00L/group07
PAIRING=sequential+retrieval
DATASET=4k/long_walk_zurich
MODEL_DIR=${BASE}/outputs/${DATASET}_${PAIRING}_fps2/sfm_superpoint+superglue
OUTPUT=${MODEL_DIR}/colmap_hier

# Load required modules and variables for using colmap
source ./scripts/colmap_startup.sh

# Create output directories if they do not exist
mkdir -p ${OUTPUT}/snap

# Run hierarchical mapper
colmap hierarchical_mapper  --database_path ${MODEL_DIR}/database.db \
                            --image_path ${BASE}/datasets/${DATASET}/images-fps2 \
                            --output_path ${OUTPUT} \
                            --num_workers 4 \
                            --image_overlap 100 \
                            --leaf_max_num_images 500 \
                            --Mapper.num_threads 32 \
                            --Mapper.ba_global_use_pba 1 \
                            --Mapper.init_min_tri_angle 8 \
                            --Mapper.snapshot_images_freq 500 \
                            --Mapper.ba_global_pba_gpu_index -1 \
                            --Mapper.snapshot_path ${OUTPUT}/snap \
                            --Mapper.tri_ignore_two_view_tracks 0 \