import os
import json
import numpy as np
from PIL import Image
from config import *
from understand_data import load_tables

def convert_nuscenes_to_training_format():
    """Convert nuScenes data to deep learning format"""
    
    # Output to results directory inside OUTPUT_DIR
    output_base = os.path.join(OUTPUT_DIR, 'results')
    images_dir = os.path.join(output_base, 'images')
    pointclouds_dir = os.path.join(output_base, 'point_clouds')
    annotations_dir = os.path.join(output_base, 'annotations')
    
    for dir_path in [images_dir, pointclouds_dir, annotations_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Load tables
    tables = load_tables(MINI_PATH, VERSION)
    
    # For CAM and LIDAR, we need to traverse from sample through sample_data references
    # Build a map of all sample_data by token
    sample_data_by_token = {sd['token']: sd for sd in tables['sample_data']}
    
    # Get sensor tokens for cameras and lidar
    sensor_map = {s['token']: s for s in tables['sensor']}
    cam_sensor_tokens = [s['token'] for s in tables['sensor'] if 'CAM' in s['channel']]
    lidar_sensor_tokens = [s['token'] for s in tables['sensor'] if 'LIDAR' in s['channel']]
    
    # Build calibrated sensor to sensor map
    calib_to_sensor = {cs['token']: cs['sensor_token'] for cs in tables['calibrated_sensor']}
    
    sample_to_annotations = {}
    for ann in tables['sample_annotation']:
        sample_token = ann['sample_token']
        if sample_token not in sample_to_annotations:
            sample_to_annotations[sample_token] = []
        sample_to_annotations[sample_token].append(ann)
    
    instance_map = {inst['token']: inst for inst in tables['instance']}
    category_map = {cat['token']: cat['name'] for cat in tables['category']}
    
    print(f"Processing {len(tables['sample'])} samples...")
    
    img_saved = 0
    pc_saved = 0
    
    # Process each sample
    for idx, sample in enumerate(tables['sample']):
        sample_token = sample['token']
        
        # Get all sample_data for this sample (traverse the linked list)
        sample_sensor_data = []
        for sd in tables['sample_data']:
            if sd.get('sample_token') == sample_token and sd.get('is_key_frame', False):
                sample_sensor_data.append(sd)
        
        # Process images (cameras) and point clouds (LIDAR)
        for sd in sample_sensor_data:
            calib_sensor_token = sd.get('calibrated_sensor_token')
            sensor_token = calib_to_sensor.get(calib_sensor_token)
            
            if sensor_token in cam_sensor_tokens:
                # This is a camera
                channel = sd.get('channel', '')
                img_path = os.path.join(MINI_PATH, sd['filename'])
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    img_array = np.array(img).astype(np.float32) / 255.0
                    
                    output_path = os.path.join(images_dir, f"{sample_token}_{channel}.npy")
                    np.save(output_path, img_array)
                    img_saved += 1
            
            elif sensor_token in lidar_sensor_tokens:
                # This is LIDAR
                pc_path = os.path.join(MINI_PATH, sd['filename'])
                if os.path.exists(pc_path):
                    pc = np.fromfile(pc_path, dtype=np.float32).reshape(-1, 5)
                    pc_xyz = pc[:, :3]
                    
                    output_path = os.path.join(pointclouds_dir, f"{sample_token}.npy")
                    np.save(output_path, pc_xyz)
                    pc_saved += 1
        
        # Process annotations
        annotations = sample_to_annotations.get(sample_token, [])
        ann_data = {
            'sample_token': sample_token,
            'timestamp': sample['timestamp'],
            'objects': []
        }
        
        for ann in annotations:
            instance = instance_map.get(ann['instance_token'], {})
            category_token = instance.get('category_token', '')
            category_name = category_map.get(category_token, 'unknown')
            
            obj = {
                'category': category_name,
                'translation': ann['translation'],
                'size': ann['size'],
                'rotation': ann['rotation'],
                'num_lidar_pts': ann.get('num_lidar_pts', 0),
                'num_radar_pts': ann.get('num_radar_pts', 0)
            }
            ann_data['objects'].append(obj)
        
        output_path = os.path.join(annotations_dir, f"{sample_token}.json")
        with open(output_path, 'w') as f:
            json.dump(ann_data, f, indent=2)
        
        if (idx + 1) % 50 == 0:
            print(f"Processed {idx + 1}/{len(tables['sample'])} samples - Images: {img_saved}, PC: {pc_saved}")
    
    # Create metadata file
    metadata = {
        'dataset': 'nuScenes-mini',
        'version': VERSION,
        'num_samples': len(tables['sample']),
        'num_scenes': len(tables['scene']),
        'categories': list(category_map.values()),
        'sensors': {s['channel']: s['modality'] for s in tables['sensor']},
        'format': {
            'images': 'numpy arrays (H, W, C), normalized to [0, 1]',
            'point_clouds': 'numpy arrays (N, 3), x, y, z coordinates',
            'annotations': 'JSON with 3D bounding boxes and metadata'
        }
    }
    
    with open(os.path.join(output_base, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nConversion complete!")
    print(f"Images saved: {img_saved}")
    print(f"Point clouds saved: {pc_saved}")
    print(f"Annotations saved: {len(tables['sample'])}")
    print(f"Output: {output_base}")

# Run conversion
convert_nuscenes_to_training_format()