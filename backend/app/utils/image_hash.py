"""
image_hash.py
-------------
Perceptual image hashing using the dHash (difference hash) algorithm.

dHash works by:
  1. Resizing the image to 9×8 pixels (grayscale)
  2. Comparing adjacent pixel pairs left-to-right across each row
  3. Producing a 64-bit fingerprint stored as a 16-char hex string

Hamming distance between two hashes gives near-duplicate detection:
  - distance 0   → identical images
  - distance 1-5 → very similar / same image, different compression/size
  - distance 6-10 → likely duplicate candidate
  - distance > 10 → different images

Usage:
    from app.utils.image_hash import compute_dhash, hamming_distance, similarity_score

    h = compute_dhash("/path/to/image.jpg")  # "3f4a8b..."
    dist = hamming_distance(h1, h2)          # 0-64
    sim  = similarity_score(h1, h2)          # 0.0 - 1.0
"""

from PIL import Image


def compute_dhash(image_path: str, hash_size: int = 8) -> str | None:
    """
    Compute the dHash (difference hash) of an image.

    Args:
        image_path: Absolute path to the image file on disk.
        hash_size:  Grid size (default 8 → 64-bit hash).

    Returns:
        16-character lowercase hex string (e.g. "3f4a8b2c9d1e0f7a"),
        or None if the file could not be processed.
    """
    try:
        img = Image.open(image_path)
        # Resize to (hash_size+1) × hash_size, convert to grayscale
        img = img.convert("L").resize(
            (hash_size + 1, hash_size),
            Image.Resampling.LANCZOS
        )
        pixels = list(img.getdata())

        # Build bit-string: compare adjacent pixels in each row
        bits = []
        for row in range(hash_size):
            for col in range(hash_size):
                left  = pixels[row * (hash_size + 1) + col]
                right = pixels[row * (hash_size + 1) + col + 1]
                bits.append(1 if left > right else 0)

        # Convert bits to int, then to hex string (zero-padded to 16 chars)
        hash_int = sum(b << i for i, b in enumerate(bits))
        return format(hash_int, "016x")

    except Exception as e:
        print(f"[IMAGE_HASH] Failed to compute dHash for {image_path}: {e}")
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Compute the Hamming distance between two 16-char hex hash strings.

    Args:
        hash1, hash2: Hex strings from compute_dhash().

    Returns:
        Integer 0-64. Lower means more similar.
    """
    try:
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        return bin(int1 ^ int2).count("1")
    except (ValueError, TypeError):
        return 64  # treat as maximally different on error


def similarity_score(hash1: str, hash2: str) -> float:
    """
    Convert Hamming distance to a 0.0–1.0 similarity score.

    Returns:
        1.0 → identical, 0.0 → completely different.
    """
    if not hash1 or not hash2:
        return 0.0
    dist = hamming_distance(hash1, hash2)
    return round(1.0 - dist / 64.0, 4)


# Near-duplicate threshold (used across services)
NEAR_DUPLICATE_THRESHOLD_DISTANCE = 10   # Hamming distance ≤ 10 → candidate
VISUAL_SIMILARITY_MIN_SCORE       = 0.80 # Score ≥ 0.80 → visually similar
