# -*- coding: utf-8 -*-
"""
Passkey Bot — Dynamic In-Discord Security Image CAPTCHA Generator.
Built with Pillow: Generates distorted high-contrast alphanumeric CAPTCHA images with noise.
"""
import io
import random
import string
from PIL import Image, ImageDraw, ImageFont

def generate_image_captcha() -> tuple[io.BytesIO, str]:
    """Generate a high-security visual CAPTCHA image."""
    width, height = 320, 110
    # Clean dark navy background
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    # 1. Generate random 5-character alphanumeric code (excluding ambiguous chars)
    charset = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    code = "".join(random.choices(charset, k=5))

    # 2. Draw background noise lines
    for _ in range(12):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        line_color = random.choice([
            (99, 102, 241, 100),   # Indigo
            (168, 85, 247, 100),  # Purple
            (6, 182, 212, 100),   # Cyan
            (56, 189, 248, 100)   # Sky
        ])
        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=random.randint(1, 2))

    # 3. Draw noise dots
    for _ in range(150):
        x = random.randint(0, width)
        y = random.randint(0, height)
        dot_color = random.choice([(147, 197, 253), (196, 181, 253), (165, 243, 252)])
        draw.point((x, y), fill=dot_color)

    # 4. Draw each character with slight offset & color variation
    char_colors = [
        (168, 85, 247),  # Vibrant Purple
        (6, 182, 212),   # Cyan
        (56, 189, 248),  # Sky Blue
        (129, 140, 248), # Indigo
        (244, 114, 182)  # Pink
    ]

    for i, char in enumerate(code):
        x = 35 + (i * 54) + random.randint(-4, 4)
        y = 30 + random.randint(-8, 8)
        color = random.choice(char_colors)
        
        # Draw character with bold drop shadow for readability
        draw.text((x + 2, y + 2), char, fill=(30, 41, 59), font_size=42)
        draw.text((x, y), char, fill=color, font_size=42)

    # 5. Draw decorative cyber border
    draw.rectangle([(2, 2), (width - 3, height - 3)], outline=(99, 102, 241), width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf, code
