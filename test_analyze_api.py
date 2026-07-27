import requests

url = "http://localhost:8000/assets/analyze"
file_path = "test.png"

with open(file_path, "rb") as f:
    files = {"file": (file_path, f, "image/png")}
    response = requests.post(url, files=files)
    print(response.status_code)
    print(response.json())
