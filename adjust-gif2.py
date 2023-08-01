## By the awesome idea of @Jeeftor https://github.com/jeeftor/HomeAssistant/blob/master/icons/dev/gifMaker.py

import requests
import time
from PIL import Image, ImageDraw
from typing import List
import asyncio
import sys
import os
from datetime import timedelta
# Defines the default AWTRIX device ip adres
DEFAULT_ENDPOINT_IP = "ulanzi3.graafnet.nl"
# Defines the border width around the pixels, will only be shown in the outputted gif, not in the live preview.
DEFAULT_BORDER_WIDTH = 1
# Defines the output gif filename.
DEFAULT_GIF_FILENAME = "output.gif"
# Defines the Width x Height of the outputted gif, will not been shown in the live preview.
# Can be: 2048x512 / 1024x256 / 512x128 / 256x64 / 128x32 / 64x16 / 32x8
DEFAULT_GIF_WIDTH = 512
DEFAULT_GIF_HEIGHT = 128



class ScreenCapture:
    def __init__(
        self,
        endpoint_url: str,
        width: int,
        height: int,
        gif_filename: str,
        initial_duration: int,
        max_duration: int,
        new_width: int,
        new_height: int,
        live_preview: bool = True,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.width = width
        self.height = height
        self.gif_filename = gif_filename
        self.initial_duration = initial_duration
        self.max_duration = max_duration
        self.new_width = new_width
        self.new_height = new_height
        self.live_preview = live_preview
        self.gif_frames: List[Image.Image] = []

    async def capture_frame(self) -> None:
        """Capture a frame from the endpoint and add it to the GIF frames."""
        frame_count = 0
        last_capture_time = time.time()

        border_color = (0, 0, 0)  # Set border color to black (you can change this)
        pixel_size = 32  # Size of one pixel (with border)
        border_width = DEFAULT_BORDER_WIDTH  # Border width (can be adjusted)

        while True:
            response = requests.get(self.endpoint_url)

            # Check if the request was successful
            if response.status_code == 200:
                # Get the RGB565 color values as a list
                rgb565_values = response.json()

                # Create a new PIL image with additional space for borders
                bordered_image_size = (
                    self.width * pixel_size, self.height * pixel_size
                )
                image = Image.new("RGB", bordered_image_size, border_color)
                draw = ImageDraw.Draw(image)

                # Set the color of each pixel in the image
                for y in range(self.height):
                    for x in range(self.width):
                        # Convert the decimal RGB565 value to RGB888
                        rgb565 = rgb565_values[y * self.width + x]
                        red = (rgb565 & 0xFF0000) >> 16
                        green = (rgb565 & 0x00FF00) >> 8
                        blue = rgb565 & 0x0000FF

                        # Calculate pixel position (with border)
                        pixel_position = (
                            x * pixel_size + border_width,
                            y * pixel_size + border_width,
                            (x + 1) * pixel_size - border_width,
                            (y + 1) * pixel_size - border_width
                        )

                        # Draw a pixel with the converted RGB value
                        draw.rectangle(pixel_position, fill=(red, green, blue))

                # Print live preview if enabled
                if self.live_preview:
                    self.print_live_preview(frame_count, image)
                
                # Resize image if necessary
                if self.width != self.new_width or self.height != self.new_height:
                    image = image.resize((self.new_width, self.new_height), Image.ANTIALIAS)
                
                # Add the current frame to the GIF
                self.gif_frames.append(image)
                frame_count += 1

                # Calculate the time since the last capture
                current_time = time.time()
                time_since_last_capture = current_time - last_capture_time
                target_frame_interval = 1.0 / 25  # Target frame interval of 40 milliseconds

                # Wait if necessary to maintain the target frame rate
                if time_since_last_capture < target_frame_interval:
                    await asyncio.sleep(target_frame_interval - time_since_last_capture)

                last_capture_time = current_time  # Update last capture time

    def print_live_preview(self, frame_count: int, image: Image.Image) -> None:
        """Print the live preview of the image, clearing the console screen."""
        os.system("cls" if os.name == "nt" else "clear")
        print(f"\033[32mFrames captured: {frame_count}\033[0m")

        pixel_size = 32  # Same value as defined in the capture_frame method
        border_width = DEFAULT_BORDER_WIDTH  # Same value as defined in the capture_frame method

        for y in range(self.height):
            for x in range(self.width):
                # Calculate the center position of the bordered pixel
                center_x = (x * pixel_size) + pixel_size // 2
                center_y = (y * pixel_size) + pixel_size // 2

                r, g, b = image.getpixel((center_x, center_y))
                sys.stdout.write(f"\033[48;2;{r};{g};{b}m  \033[0m")
            sys.stdout.write("\n")
        print("\033[32mctrl+c to exit\033[0m")

    def save_as_gif(self) -> None:
        """Save the captured frames as a GIF and print the duration."""
        if len(self.gif_frames) > 0:
            # Calculate the total duration of the GIF
            total_duration = len(self.gif_frames) * self.initial_duration

            # Save the frames as a GIF
            self.gif_frames[0].save(
                self.gif_filename,
                format="GIF",
                append_images=self.gif_frames[1:],
                save_all=True,
                duration=self.initial_duration,
                loop=0,
            )

            # Print the duration
            duration_str = str(timedelta(milliseconds=total_duration))
            print(f"\nGIF saved successfully. Duration: {duration_str}")
        else:
            print("\nNo frames captured. GIF not saved.")


async def capture_loop(screen_capture: ScreenCapture) -> None:
    await screen_capture.capture_frame()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Awtrix Clock Screen Capture")
    parser.add_argument(
        "--ip",
        type=str,
        default=argparse.SUPPRESS,  # Set the default value to suppress the prompt
        help="The IP address of your Awtrix Clock",
    )

    args = parser.parse_args()

    # Use the command line argument if provided, otherwise use the default IP
    endpoint_ip = args.ip if hasattr(args, "ip") else DEFAULT_ENDPOINT_IP

    # Endpoint URL
    endpoint_url = f"http://{endpoint_ip}/api/screen"

    # Image dimensions
    width = 32
    height = 8

    # GIF parameters
    gif_filename = DEFAULT_GIF_FILENAME
    initial_duration = 40  # in milliseconds (Approximately 25 frames per second)
    max_duration = 500  # in milliseconds

    # New dimensions for the GIF
    new_width = DEFAULT_GIF_WIDTH  # For example
    new_height = DEFAULT_GIF_HEIGHT  # For example


    # Create ScreenCapture instance
    screen_capture = ScreenCapture(
        endpoint_url, width, height, gif_filename, initial_duration, max_duration, new_width, new_height
    )

    # Prompt user to start capturing
    input("Press Enter to start capturing frames...")

    # Capture frames in an asyncio loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(capture_loop(screen_capture))
    except KeyboardInterrupt:
        print(f"\nInterrupted by user. \nSaving GIF.... \nGIF Resolution: {new_width}x{new_height}\nGIF Output: {gif_filename}\nAWTRIX Device: {endpoint_ip}")
    finally:
        # Save the frames as a GIF
        screen_capture.save_as_gif()


if __name__ == "__main__":
    main()
