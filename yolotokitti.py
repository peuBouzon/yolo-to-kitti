import argparse
import pathlib
import shutil
from PIL import Image
from tqdm import tqdm
parser = argparse.ArgumentParser()
parser.add_argument('--labels', help="yolo labels folder",
                    type=str, required=True)
parser.add_argument('--height', help="images height")
parser.add_argument('--classes', help="classes map file")
parser.add_argument('--width', help="images width")
parser.add_argument('--images', help="yolo images folder", type=str)
args = parser.parse_args()

fixed_dimensions = True
if not args.images:
    if not (args.width or args.height):
        raise Exception(
            'Please provide --width and --height or specify the images folder with --images')
    else:
        print(f"Using fixed dimesions: ({args.height}, {args.width})")
else:
    print(f"Using images on {args.images} to get dimensions")
    fixed_dimensions = False

classes_map = dict()
with open(args.classes) as f:
    i = 0
    for line in f.readlines():
        classes_map[i] = line.strip()
        i += 1

labels_folder = pathlib.Path(args.labels)
images_folder = pathlib.Path(args.images)

kitti_folder = pathlib.Path.cwd() / 'kitti_labels'
if kitti_folder.is_dir():
    shutil.rmtree(kitti_folder)
kitti_folder.mkdir()

missed_images = []
for label_path in tqdm(list(labels_folder.iterdir())):
    if not fixed_dimensions:
        image_path = images_folder / label_path.stem
        suffixes = ['.jpg', '.png', '.jpeg']
        for suffix in suffixes:
            image_path = image_path.with_suffix(suffix)
            try:
                image_width, image_height = Image.open(image_path).size
                break
            except FileNotFoundError:
                continue
        else:
            missed_images.append(label_path)
            continue
    else:
        image_width, image_height = args.width, args.height

    kitti_lines = []
    with open(label_path) as f:
        for line in f.readlines():
            line = line.strip().split(' ')
            class_ = int(line[0])
            x_center = float(line[1])*image_width
            y_center = float(line[2])*image_height
            bbox_width = float(line[3])*image_width
            bbox_height = float(line[4])*image_height
            # kitti format: '-1 -1 -10 x_min y_min x_max y_max -1 -1 -1 -1000 -1000 -1000 -10\n'
            kitti_lines.append(
                f'{classes_map[class_]} -1 -1 -10 {x_center / 2:.2f} {y_center / 2:.2f} {(x_center / 2 + bbox_width):.2f} {(y_center / 2 + bbox_height):.2f} -1 -1 -1 -1000 -1000 -1000 -10\n')
    with open(kitti_folder / f'{label_path.stem}.txt', mode='w') as f:
        f.writelines(kitti_lines)
if not fixed_dimensions and missed_images:
    print(
        f'No images found for these labels: {missed_images}')
