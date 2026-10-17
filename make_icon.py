# make_icon.py
import os
from PIL import Image, ImageDraw

def create_icons():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded dark obsidian background
    draw.rounded_rectangle([(8, 8), (size - 8, size - 8)], radius=56, fill=(18, 18, 22, 255), outline=(255, 0, 51, 200), width=6)

    # Draw YouTube-inspired crimson badge inside
    draw.rounded_rectangle([(44, 68), (size - 44, size - 68)], radius=32, fill=(255, 0, 51, 255))

    # Draw Play / Download hybrid triangle in white
    play_points = [(105, 96), (105, 160), (165, 128)]
    draw.polygon(play_points, fill=(255, 255, 255, 255))

    os.makedirs("web", exist_ok=True)
    img.save("icon.png", format="PNG")
    img.save("web/icon.png", format="PNG")
    img.save("icon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("Created icon.ico, icon.png, and web/icon.png successfully!")

if __name__ == "__main__":
    create_icons()