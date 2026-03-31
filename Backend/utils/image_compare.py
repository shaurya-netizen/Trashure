import os
from PIL import Image, ImageChops, ImageStat


def images_are_different(image_path_1: str, image_path_2: str, threshold: float = 8.0) -> bool:
    """
    Compare two images and return True if they are meaningfully different.
    threshold = average pixel difference tolerance.
    """

    if not os.path.exists(image_path_1) or not os.path.exists(image_path_2):
        return True  # if one image missing, assume different

    try:
        img1 = Image.open(image_path_1).convert("RGB").resize((256, 256))
        img2 = Image.open(image_path_2).convert("RGB").resize((256, 256))

        diff = ImageChops.difference(img1, img2)
        stat = ImageStat.Stat(diff)

        # Mean difference across RGB channels
        mean_diff = sum(stat.mean) / len(stat.mean)

        print(f"🧪 Image difference score: {mean_diff}")

        return mean_diff > threshold

    except Exception as e:
        print(f"❌ Error comparing images: {e}")
        return True