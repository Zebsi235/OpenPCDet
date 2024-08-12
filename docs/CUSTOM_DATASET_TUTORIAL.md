# Custom Dataset Tutorial
For the custom dataset template, we only consider the basic scenario: raw point clouds and 
their corresponding annotations. Point clouds are supposed to be stored in `.npy` format.

## Label format
We only consider the most basic information -- category and bounding box in the label template.
Annotations are stored in the `.txt`. Each line represents a box in a given scene as below:
```
# format: [x y z dx dy dz heading_angle category_name]
1.50 1.46 0.10 5.12 1.85 4.13 1.56 Vehicle
5.54 0.57 0.41 1.08 0.74 1.95 1.57 Pedestrian
```
The box should in the unified 3D box definition (see [README](../README.md))

## Files structure
Files should be placed as the following folder structure:
```
OpenPCDet
├── data
│   ├── custom
│   │   │── ImageSets
│   │   │   │── train.txt
│   │   │   │── val.txt
│   │   │── points
│   │   │   │── 000000.npy
│   │   │   │── 999999.npy
│   │   │── labels
│   │   │   │── 000000.txt
│   │   │   │── 999999.txt
├── pcdet
├── tools
```
Dataset splits need to be pre-defined and placed in `ImageSets`

## Hyper-parameters Configurations

### Point cloud features
Modify following configurations in `custom_dataset.yaml` to 
suit your own point clouds.
```yaml
POINT_FEATURE_ENCODING: {
    encoding_type: absolute_coordinates_encoding,
    used_feature_list: ['x', 'y', 'z', 'intensity'],
    src_feature_list: ['x', 'y', 'z', 'intensity'],
}
...
# In gt_sampling data augmentation
NUM_POINT_FEATURES: 4

```

#### Point cloud range and voxel sizes
For voxel based detectors such as SECOND, PV-RCNN and CenterPoint, the point cloud range and voxel size should follow:
1. Point cloud range along z-axis / voxel_size is 40
2. Point cloud range along x&y-axis / voxel_size is the multiple of 16.

Notice that the second rule also suit pillar based detectors such as PointPillar and CenterPoint-Pillar.

### Category names and anchor sizes
Category names and anchor size are need to be adapted to custom datasets.
 ```yaml
CLASS_NAMES: ['Vehicle', 'Pedestrian', 'Cyclist']  
...
MAP_CLASS_TO_KITTI: {
    'Vehicle': 'Car',
    'Pedestrian': 'Pedestrian',
    'Cyclist': 'Cyclist',
}
...
'anchor_sizes': [[3.9, 1.6, 1.56]],
...
# In gt sampling data augmentation
PREPARE: {
 filter_by_min_points: ['Vehicle:5', 'Pedestrian:5', 'Cyclist:5'],
 filter_by_difficulty: [-1],
}
SAMPLE_GROUPS: ['Vehicle:20','Pedestrian:15', 'Cyclist:15']
...
 ```
In addition, please also modify the default category names for creating infos in `custom_dataset.py`
```
create_custom_infos(
    dataset_cfg=dataset_cfg,
    class_names=['Vehicle', 'Pedestrian', 'Cyclist'],
    data_path=ROOT_DIR / 'data' / 'custom',
    save_path=ROOT_DIR / 'data' / 'custom',
)
```


## Create data info
Generate the data infos by running the following command:
```shell
python -m pcdet.datasets.custom.custom_dataset create_custom_infos tools/cfgs/dataset_configs/custom_dataset.yaml
```




## Training
To start the training with a custom model configuration, the config has to exist in ```/app/OpenPCDet/tools/cfgs/custom_models/```

It can be executed with: 
``` cd /app/OpenPCDet/tools && python3 train.py --cfg_file cfgs/custom_models/model_config.yaml --epoch 50 ```





## Evaluation
Here, we only provide an implementation for KITTI stype evaluation.
The category mapping between custom dataset and KITTI need to be defined 
in the `custom_dataset.yaml`
```yaml
MAP_CLASS_TO_KITTI: {
    'Vehicle': 'Car',
    'Pedestrian': 'Pedestrian',
    'Cyclist': 'Cyclist',
}
```

## Get ssh connection for visualisation
1. ```docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' openpcdet ```
1. ```docker exec -it openpcdet  sh```
1. type ```passwd``` to change the root password
1. change the line "PermitRootLgin" in /etc/ssh/sshd_config to yes
1. restart ssh ```/etc/init.d/ssh restart``` and disconnect from the docker container 
1. login through ssh with ```ssh -X -p 2222 root@172.X.X.X```


## Test | this only shows prediction boxes 
```python3 demo.py --data_path <path to points (folder)> --ext .npy --ckpt <path to checkpoint file (.pth file)> --cfg_file <path to model configuration file (.yaml file)>```

## Test | this shows prediction boxes (green) and ground truth (blue) 
```python3 demo-gt.py --data_path <path to points (folder)> --ext .npy --ckpt <path to checkpoint file (.pth file)> --cfg_file <path to model configuration file (.yaml file)>```

# Re-evaluating the trained model/checkpoint
```python3 test.py --ckpt <path to checkpoint file (.pth file)> --cfg_file <path to model configuration file (.yaml file)>```