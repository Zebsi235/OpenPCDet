import argparse
import glob
from pathlib import Path

try:
    import open3d
    from visual_utils import open3d_vis_utils as V
    OPEN3D_FLAG = True
except:
    import mayavi.mlab as mlab
    from visual_utils import visualize_utils as V
    OPEN3D_FLAG = False

import numpy as np
import torch

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets import DatasetTemplate
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils


class DemoDataset(DatasetTemplate):
    def __init__(self, dataset_cfg, class_names, training=True, root_path=None, logger=None, ext='.bin'):
        """
        Args:
            root_path:
            dataset_cfg:
            class_names:
            training:
            logger:
        """
        super().__init__(
            dataset_cfg=dataset_cfg, class_names=class_names, training=training, root_path=root_path, logger=logger
        )
        self.root_path = root_path
        self.ext = ext
        data_file_list = glob.glob(str(root_path / f'*{self.ext}')) if self.root_path.is_dir() else [self.root_path]

        data_file_list.sort()
        self.sample_file_list = data_file_list

    def __len__(self):
        return len(self.sample_file_list)

    def __getitem__(self, index):
        if self.ext == '.bin':
            points = np.fromfile(self.sample_file_list[index], dtype=np.float32).reshape(-1, 4)
        elif self.ext == '.npy':
            points = np.load(self.sample_file_list[index])
        else:
            raise NotImplementedError

        input_dict = {
            'points': points,
            'frame_id': index,
        }

        # Retrieve ground truth boxes for the current sample
        gt_boxes = self.load_gt_boxes(index)

        data_dict = self.prepare_data(data_dict=input_dict)
        data_dict['gt_boxes'] = gt_boxes
        return data_dict

    def load_gt_boxes(self, index):
        # You need to implement this method based on how your ground truth is stored
        # For example, if it's stored in a corresponding file:
        gt_file_path = self.sample_file_list[index].replace('points', 'labels').replace(self.ext, '.txt')  # Assuming .gt as ground truth extension
        print(gt_file_path)
        
        gt_data = np.loadtxt(gt_file_path, dtype={'names': ('x', 'y', 'z', 'dx', 'dy', 'dz', 'yaw', 'label'), 'formats': ('f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'U10')})
        print(f"Checking shape 1{gt_data.shape}")

        if gt_data.shape != (2,):
            gt_boxes = np.array([gt_data['x'],gt_data['y'],gt_data['z'],gt_data['dx'],gt_data['dy'],gt_data['dz'],gt_data['yaw']])
            print("Not the right shape")
            return gt_boxes
        print(f"Checking shape 2{gt_data.shape}")
        print(gt_data)
        #print(len(gt_data))
#        if len(gt_data[idx]) > 1:
        gt_boxes = np.array([[gt['x'],gt['y'],gt['z'],gt['dx'],gt['dy'],gt['dz'],gt['yaw']] for gt in gt_data])
#        else:
#            gt_boxes = np.array([[gt['x'],gt['y'],gt['z'],gt['dx'],gt['dy'],gt['dz'],gt['yaw']] for gt_data])
        return gt_boxes

def parse_config():
    parser = argparse.ArgumentParser(description='arg parser')
    parser.add_argument('--cfg_file', type=str, default='cfgs/kitti_models/second.yaml',
                        help='specify the config for demo')
    parser.add_argument('--data_path', type=str, default='demo_data',
                        help='specify the point cloud data file or directory')
    parser.add_argument('--ckpt', type=str, default=None, help='specify the pretrained model')
    parser.add_argument('--ext', type=str, default='.bin', help='specify the extension of your point cloud data file')

    args = parser.parse_args()

    cfg_from_yaml_file(args.cfg_file, cfg)

    return args, cfg


def main():
    args, cfg = parse_config()
    logger = common_utils.create_logger()
    logger.info('-----------------Quick Demo of OpenPCDet-------------------------')
    demo_dataset = DemoDataset(
        dataset_cfg=cfg.DATA_CONFIG, class_names=cfg.CLASS_NAMES, training=False,
        root_path=Path(args.data_path), ext=args.ext, logger=logger
    )
    logger.info(f'Total number of samples: \t{len(demo_dataset)}')

    model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=demo_dataset)
    model.load_params_from_file(filename=args.ckpt, logger=logger, to_cpu=True)
    model.cuda()
    model.eval()
    if len(demo_dataset) > 10:
        start_idx = int(input("Please enter index to start\n"))
        if start_idx > len(demo_dataset):
            print("Error start_idx to big for dataset")
            return
        demo_dataset.sample_file_list = demo_dataset.sample_file_list[start_idx:]
    with torch.no_grad():
        for idx, data_dict in enumerate(demo_dataset):
            logger.info(f'Visualized sample index: \t{idx + 1}')
            data_dict = demo_dataset.collate_batch([data_dict])
            load_data_to_gpu(data_dict)
            pred_dicts, _ = model.forward(data_dict)

            # Visualizing both ground truth and predictions
            if OPEN3D_FLAG:
                print(pred_dicts[0]['pred_scores'])
                V.draw_scenes(
                points=data_dict['points'][:, 1:], ref_boxes=pred_dicts[0]['pred_boxes'],
                ref_scores=pred_dicts[0]['pred_scores'], ref_labels=pred_dicts[0]['pred_labels'], 
                gt_boxes=np.concatenate(data_dict['gt_boxes'].cpu().numpy())
                )
                #V.draw_scenes(
                #    points=data_dict['points'][:, 1:], 
                #    ref_boxes=np.concatenate(pred_dicts[0]['pred_boxes'].cpu().numpy()), 
                #    ref_scores=np.ones(len(pred_dicts[0]['pred_boxes']))
                #    gt_boxes=data_dict['gt_boxes']
                #)                V.draw_scenes(
               #     points=data_dict['points'][:, 1:], 
               #     ref_boxes=np.concatenate(data_dict['gt_boxes'].cpu().numpy()), 
                #    ref_scores=np.ones(len(data_dict['gt_boxes'])),
                #    point_colors=(1, 0, 0)
#                )
            else:
                print("SECOND CASE\n\n\n")
                mlab.points3d(data_dict['points'][:, 0], data_dict['points'][:, 1], data_dict['points'][:, 2], mode='point')
                V.draw_gt_boxes3d(data_dict['gt_boxes'], color=(1, 0, 0))  # Assuming red for GT
                V.draw_gt_boxes3d(pred_dicts[0]['pred_boxes'], color=(0, 1, 0))  # Assuming green for predictions

                mlab.show(stop=True)

    logger.info('Demo done.')



if __name__ == '__main__':
    main()
