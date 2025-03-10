import numpy as np
import cv2
import os
import pyrealsense2 as rs
from pathlib import Path

# Base directory containing folders with .bag files
BASE_DIR = "/media/airlab5/Crucial X6/Sawyer_experiemnt bags/"

def save_to_video(file_path):
    pipeline = None
    color_out = None
    try:
        file_name = Path(file_path).stem
        file_dir = Path(file_path).parent
        
        print(f"Converting {file_name} to video...")

        # Initialize RealSense pipeline
        pipeline = rs.pipeline()
        config = rs.config()

        # Load bag file
        rs.config.enable_device_from_file(config, str(file_path), False)

        # Enable color stream with default settings
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        pipeline.start(config)

        # Retrieve first frame for dimensions
        frame = pipeline.wait_for_frames()
        color_frame = frame.get_color_frame()
        
        if not color_frame:
            raise RuntimeError(f"No color stream found in {file_path}")

        width, height = color_frame.get_width(), color_frame.get_height()

        # Define MP4 codec and create video file
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        output_video_path = file_dir / f"{file_name}_rgb.mp4"
        color_out = cv2.VideoWriter(str(output_video_path), fourcc, 30.0, (width, height))
        
        print(f"Saving video to: {output_video_path}")

        # Process all frames
        while True:
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()

            if not color_frame:
                break

            color_image = np.asanyarray(color_frame.get_data())
            color_out.write(color_image)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    finally:
        if color_out:
            color_out.release()
        if pipeline:
            pipeline.stop()
        print(f"Finished converting {file_name}")

def process_all_bag_files(base_directory):
    """ Recursively finds and converts all .bag files in subdirectories. """
    base_path = Path(base_directory)

    if not base_path.exists():
        print(f"Error: Directory {base_directory} does not exist.")
        return

    for bag_file in base_path.rglob("*.bag"):  # Recursively find all .bag files
        save_to_video(bag_file)

if __name__ == "__main__":
    process_all_bag_files(BASE_DIR)

