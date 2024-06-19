import pyrealsense2 as rs
import numpy as np
import cv2
import os
from tkinter import filedialog as fd
from pathlib import Path

def save_to_video(file_path):
    pipeline = None
    color_out = None
    try:
        file_name = Path(file_path).stem
        file_dir = Path(file_path).parent
        
        print(f"Converting {file_name} to video")
        
        # Create pipeline
        pipeline = rs.pipeline()
    
        # Create a config object
        config = rs.config()
    
        rs.config.enable_device_from_file(config, str(file_path), False)
    
        # Configure the pipeline to stream only the color stream
        config.enable_stream(rs.stream.color, rs.format.bgr8, 30)
    
        # Start streaming from file
        pipeline_profile = pipeline.start(config)
        
        # Use first frame to get dimensions for the color frame
        frame = pipeline.wait_for_frames()
        color_frame = frame.get_color_frame()
        color_frame_width = color_frame.get_width()
        color_frame_height = color_frame.get_height()
        
        # MP4 Format
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        # Save the video in the same directory as the .bag file
        color_out = cv2.VideoWriter(str(file_dir / f"{file_name} - rgb.mp4"), fourcc, 30.0, (color_frame_width, color_frame_height))
        
        try: 
            # Streaming loop
            while True:
                frames = pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                if not color_frame:
                    break
                color_image = np.asanyarray(color_frame.get_data())
                
                color_out.write(color_image)
                
        except Exception as e:
            print(f"Error during frame processing: {e}")
            
    except Exception as e:
        print(f"Error during video conversion: {e}")
        
    finally:
        if color_out:
            color_out.release()
        if pipeline:
            try:
                pipeline.stop()
            except RuntimeError as e:
                print(f"Error stopping pipeline: {e}")
        print(f"Finished converting {file_name}")

def main():
    # Prompt user to select a directory
    folder_path = fd.askdirectory(initialdir="/media/amr/Crucial X6/bags", title="Select folder containing .bag files")
    
    if folder_path:
        folder_path = Path(folder_path)
        # Iterate through all .bag files in the selected directory
        for file_path in folder_path.glob("*.bag"):
            save_to_video(file_path)
    
if __name__ == "__main__":
    main()

