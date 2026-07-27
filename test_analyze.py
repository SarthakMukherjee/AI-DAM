import asyncio
import os
import json
from PIL import Image

# Create a dummy image
img = Image.new('RGB', (100, 100), color = 'red')
img.save('test.png')

print("Saved test.png")
