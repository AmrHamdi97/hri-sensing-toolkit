import numpy as np
import cv2
import os
import pyrealsense2 as rs
from pathlib import Path

# Base directory containing folders with .bag files
BASE_DIR = "/media/airlab5/Z Slim/BAGS"

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
        try:
            rs.config.enable_device_from_file(config, str(file_path), repeat_playback=False)
        except RuntimeError as e:
            print(f"Error opening {file_path}: {e}")
            return  # Skip this file and continue with others

        # Create a temporary pipeline to check available streams
        temp_pipeline = rs.pipeline()
        temp_pipeline.start(config)
        profile = temp_pipeline.get_active_profile()

        # Get available streams
        streams = profile.get_streams()
        temp_pipeline.stop()

        # Ensure color stream exists
        color_stream = None
        for stream in streams:
            if stream.stream_type() == rs.stream.color:
                color_stream = stream
                break

        if not color_stream:
            print(f"Skipping {file_name}: No color stream found in the .bag file.")
            return

        # Get stream resolution
        width = color_stream.as_video_stream_profile().width()
        height = color_stream.as_video_stream_profile().height()

        # Configure the real pipeline
        config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, 30)

        # Start the actual pipeline
        pipeline.start(config)

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
            try:
                pipeline.stop()
            except RuntimeError:
                pass  # Avoid calling stop() if pipeline never started

        print(f"Finished processing {file_name}")

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

