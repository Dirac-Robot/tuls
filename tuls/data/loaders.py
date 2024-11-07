import glob
import os
import cv2
from typing import overload

from tuls.data.constants import IMAGE_EXTENSIONS


def load_all_image_paths(source):
    if not source.endswith('{ext}'):
        source = os.path.join(source, '*.{ext}')
    image_paths = []
    for ext in IMAGE_EXTENSIONS:
        image_paths.extend(glob.glob(source.format(ext=ext)))
    return image_paths


@overload
def extract_images_from_video(source, output_dir, sampling_rate):
    pass


@overload
def extract_images_from_video(source, output_dir, num_frames):
    pass


def extract_images_from_video(source, output_dir, sampling_rate=None, num_frames=None):
    os.makedirs(output_dir, exist_ok=True)
    video = cv2.VideoCapture(source)
    frames = []
    frame_index = 0
    while True:
        result, frame = video.read()
        if not result:
            break
        frames.append(dict(index=frame_index, frame=frame))
        frame_index += 1
    if num_frames is not None:
        sampling_rate = len(frames)//num_frames
    frames = [frames[frame_index] for frame_index in range(0, sampling_rate, len(frames))]
    for frame_info in frames:
        file_path = os.path.join(output_dir, f'frame_{frame_info["index"]:06d}.png')
        cv2.imwrite(file_path, frame_info['frame'])
    video.release()
    cv2.destroyAllWindows()
