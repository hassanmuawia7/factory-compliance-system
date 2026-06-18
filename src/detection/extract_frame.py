import cv2
import os

def main():
    # Ensure the outputs directory exists
    os.makedirs("outputs", exist_ok=True)
    
    # Path to your test video
    video_path = "data/videos/test.mp4"
    output_path = "outputs/raw_frame.jpg"
    
    print(f"Opening video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("❌ ERROR: Could not open video file.")
        return
        
    # Read just the very first frame
    success, frame = cap.read()
    
    if success:
        # Save the frame as an image
        cv2.imwrite(output_path, frame)
        print(f"✅ Success! Raw frame saved to: {output_path}")
    else:
        print("❌ ERROR: Could not read a frame from the video.")
        
    cap.release()

if __name__ == "__main__":
    main()