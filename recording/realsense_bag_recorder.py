import pyrealsense2 as rs
import time
import os
import numpy as np
import cv2
from datetime import datetime
import signal

# Define a running global variable
running = True

# Signal handler function
def signal_handler(sig, frame):
    global running
    running = False

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

path = os.path.dirname(os.path.abspath(__file__))

print(path)

def get_depth_and_color_img(frame):
    # Create colorizer object
    colorizer = rs.colorizer()
    # depth_frame = frame.get_depth_frame()
    color_frame = frame.get_color_frame()
    # Convert images to numpy arrays
    color_image = np.asanyarray(color_frame.get_data())
    # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
    # depth_colormap_1 = colorizer.colorize(depth_frame)
    # depth_image = np.asanyarray(depth_colormap_1.get_data())
    
    # return depth_image, color_image
    return color_image

def main():
    global running
    pipelines = []
    profiles = []
    recorders = []
    try:
        ctx = rs.context()
        devices = ctx.query_devices()

        # Start camera streams
        for i in range(len(devices)):
            pipelines.append(rs.pipeline())
            
            config = rs.config()
            config.enable_device(str(devices[i].get_info(rs.camera_info.serial_number)))   
            # config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
            config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
            
            profiles.append(pipelines[i].start(config))
        
        # Allow cameras to stabilize
        time.sleep(5)
        
        # Start recording
        print("Recording Start")
        for i, profile in enumerate(profiles): 
            # Recorders now only for color streams
            recorders.append(rs.recorder(path + '/bags/' + str(datetime.now()) + '- cam' + str(i) + '.bag', profile.get_device()))
        
        # Streaming loop
        while running: 
            for i, pipeline in enumerate(pipelines):
                frame = pipeline.wait_for_frames()
                
                # depth_image, color_image = get_depth_and_color_img(frame)
                color_image = get_depth_and_color_img(frame)
                
                # images = np.hstack((color_image, depth_image))
                
                cv2.namedWindow('RealSense - cam' + str(i), cv2.WINDOW_NORMAL)
                cv2.imshow('RealSense - cam' + str(i), color_image)
            
            key = cv2.waitKey(1)
            # If pressed escape exit program
            if key == 27:
                break
        
    except Exception as e:
        print(e)
    finally:
        cv2.destroyAllWindows()
        for pipeline in pipelines: 
            pipeline.stop()
        print("Cleanup and exit.")

if __name__ == "__main__":
    main()

