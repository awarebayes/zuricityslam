#!/usr/bin/env python
# coding: utf-8

# Inspired from hloc example SfM_pipeline.py

from pathlib import Path
import argparse
from pycolmap import CameraMode


from hloc import extract_features, match_features, reconstruction, visualization, pairs_from_retrieval
from hloc.utils import viz
from hloc.utils.parsers import parse_image_list
from hloc import pairs_from_sequence


confs = {'pairing': ['sequential', 'retrieval', 'sequential+retrieval']}

# Run SfM reconstruction from scratch on a set of images.
def main(images_path, image_list_path, outputs, video_id, window_size, num_loc, pairing, run_reconstruction, retrieval_interval=5, overwrite=False):
    
    output_model = outputs / video_id
    if 'part' in video_id:
        output_model_base = output_model.parent

    retrieval_conf = extract_features.confs['netvlad']
    feature_conf = extract_features.confs['superpoint_aachen']
    matcher_conf = match_features.confs['superglue']

    output_model.mkdir(exist_ok=True, parents=True, mode=0o777)

    print("getting images...")
    # Image list is the the relative path to the image from the top most image root folder
    image_list = parse_image_list(image_list_path)
    print(f"num images : {len(image_list)}")

    # ## Find image pairs either via sequential pairing, image retrieval or eventually both
    if pairing in confs['pairing']:        
        if 'retrieval' in pairing:
            # We extract global descriptors with NetVLAD and find for each image the most similar ones.
            retrieval_path = extract_features.main(
                retrieval_conf, images_path, output_model_base, image_list=image_list, overwrite=overwrite)

        if pairing == 'sequential':
            sfm_pairs = output_model / f'pairs-sequential{window_size}.txt'

            pairs_from_sequence.main(
                sfm_pairs, image_list, features=None, window_size=window_size, quadratic=True)

        elif pairing == 'retrieval':
            sfm_pairs = output_model / f'pairs-retrieval-netvlad{num_loc}.txt'

            pairs_from_retrieval.main(
                retrieval_path, sfm_pairs, num_matched=num_loc)

        elif pairing == 'sequential+retrieval':
            sfm_pairs = output_model / f'pairs-sequential{window_size}-retrieval-netvlad{num_loc}.txt'

            pairs_from_sequence.main(
                sfm_pairs, image_list, features=None, window_size=window_size,
                loop_closure=True, quadratic=True, retrieval_path=retrieval_path, retrieval_interval=retrieval_interval, num_loc=num_loc)

    else:
        raise ValueError(f'Unknown pairing method')

    # ## Extract and match local features
    feature_path = extract_features.main(feature_conf, images_path, output_model_base, image_list=image_list, overwrite=overwrite)

    # output file for matches
    matches = Path(output_model_base, f'{feature_path.stem}_{matcher_conf["output"]}_{sfm_pairs.stem}.h5')
    
    match_path = match_features.main(
        matcher_conf, sfm_pairs, features=feature_path, matches=matches, overwrite=overwrite)

    # ## 3D reconstruction
    # Run COLMAP on the features and matches.

    # TODO add camera mode as a param, single works for now, but maybe per folder would be better when we start merging
    model = reconstruction.main(
        output_model, images_path, sfm_pairs, feature_path, match_path, image_list=image_list, camera_mode=CameraMode.SINGLE, run=run_reconstruction, overwrite=overwrite)

    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--images_path', type=Path, default='/cluster/project/infk/courses/252-0579-00L/group07/datasets/images',
                        help='Path to the dataset, default: %(default)s')
    parser.add_argument('--image_splits', type=Path, default='/cluster/project/infk/courses/252-0579-00L/group07/datasets/image_splits',
                        help='Path to the partioning of the datasets, default: %(default)s')
    parser.add_argument('--outputs', type=Path, default='/cluster/project/infk/courses/252-0579-00L/group07/datasets/outputs',
                        help='Path to the output directory, default: %(default)s')
    parser.add_argument('--video_id', type=str, default='W25QdyiFnh0/part0',
                        help='video id for subfolder, %(default)s')
    parser.add_argument('--window_size', type=int, default=6,
                        help="Size of the window of images to match sequentially, default: %(default)s")
    parser.add_argument('--num_loc', type=int, default=7,
                        help='Number of image pairs for retrieval, default: %(default)s')
    parser.add_argument('--retrieval_interval', type=int, default=5,
                        help='How often to trigger retrieval: %(default)s')
    parser.add_argument('--pairing', type=str, default='sequential+retrieval',
                        help=f'Pairing method, default: %(default)s', choices=confs['pairing'])
    parser.add_argument('--run_reconstruction', action="store_true",
                        help="If we want to run the pycolmap reconstruction or not")
    parser.add_argument('--overwrite', action="store_true")
    args = parser.parse_args()
    
    # Run mapping
    model = main(**args.__dict__)

    images = args.images_path / args.video_id
    outputs = args.outputs

    if model is not None:
        # We visualize some of the registered images, and color their keypoint by visibility, track length, or triangulated depth.
        
        print("Plotting some examples of sfm points")
        plt_dir = outputs / 'plots'
        plt_dir.mkdir(exist_ok=True, parents=True)

        visualization.visualize_sfm_2d(model, images, color_by='visibility', n=5)
        viz.save_plot(plt_dir / 'visibility.png')
        # plt.show()

        visualization.visualize_sfm_2d(model, images, color_by='track_length', n=5)
        viz.save_plot(plt_dir / 'track_length.png')
        # plt.show()

        visualization.visualize_sfm_2d(model, images, color_by='depth', n=5)
        viz.save_plot(plt_dir / 'depth.png')
        # plt.show()
    
    else:
        print("Model is not created!\n Run hloc or colmap reconstruction!")
