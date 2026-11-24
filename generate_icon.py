from PIL import Image, ImageDraw

def generate_icon(path="app_icon.ico"):
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []

    for size in sizes:
        w, h = size
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw dark rounded pill
        pill_h = int(h * 0.5)
        pill_y = int(h * 0.25)
        radius = pill_h // 2
        draw.rounded_rectangle(
            [2, pill_y, w - 3, pill_y + pill_h],
            radius=radius,
            fill=(14, 14, 18, 255),
            outline=(0, 122, 255, 255),
            width=max(1, w // 32)
        )

        # Glowing dynamic island dot
        dot_r = max(2, w // 10)
        dot_x = int(w * 0.28)
        dot_y = int(h * 0.5)
        draw.ellipse(
            [dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r],
            fill=(0, 122, 255, 255)
        )
        images.append(img)

    images[-1].save(path, format="ICO", sizes=[(s[0], s[1]) for s in sizes])
    print(f"Generated {path}")

if __name__ == "__main__":
    generate_icon()
