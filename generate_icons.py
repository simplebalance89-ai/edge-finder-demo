"""
Generate Edge Finder app icons via Azure DALL-E 3.
"""
import os, time, httpx

AZURE_KEY = os.getenv("DALLE_API_KEY", "")
AZURE_ENDPOINT = "https://swedencentral.api.cognitive.microsoft.com"
DEPLOYMENT = "dall-e-3"
API_VERSION = "2024-02-01"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "assets")

IMAGES = [
    {
        "filename": "edge-finder-icon.png",
        "size": "1024x1024",
        "prompt": (
            "A sleek modern app icon for a sports betting analytics tool. "
            "Dark emerald green to black gradient background. "
            "A sharp geometric diamond or prism shape in the center made of clean white lines, "
            "with a subtle green glow effect around the edges. "
            "Minimalist, premium feel. No text. App store icon style, rounded corners. "
            "Professional, clean, modern design."
        ),
    },
    {
        "filename": "edge-finder-icon-alt.png",
        "size": "1024x1024",
        "prompt": (
            "A modern minimalist app icon. Deep black background with a single sharp angular line "
            "cutting diagonally across, transitioning from emerald green to bright white. "
            "Abstract geometric representation of finding an edge or advantage. "
            "Clean, geometric, minimal. No text. App store icon style with rounded corners. "
            "Premium fintech aesthetic."
        ),
    },
]

URL = f"{AZURE_ENDPOINT}/openai/deployments/{DEPLOYMENT}/images/generations?api-version={API_VERSION}"
HEADERS = {"api-key": AZURE_KEY, "Content-Type": "application/json"}

os.makedirs(OUTPUT_DIR, exist_ok=True)

for i, img in enumerate(IMAGES):
    print(f"\n[{i+1}/{len(IMAGES)}] Generating: {img['filename']}")
    body = {"prompt": img["prompt"], "size": img["size"], "quality": "hd", "n": 1}

    resp = httpx.post(URL, json=body, headers=HEADERS, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    image_url = data["data"][0]["url"]
    print(f"  URL received. Downloading...")

    img_resp = httpx.get(image_url, timeout=60)
    img_resp.raise_for_status()

    out_path = os.path.join(OUTPUT_DIR, img["filename"])
    with open(out_path, "wb") as f:
        f.write(img_resp.content)
    print(f"  Saved: {out_path} ({len(img_resp.content) // 1024} KB)")

    if i < len(IMAGES) - 1:
        print("  Waiting 12s for rate limit...")
        time.sleep(12)

print("\nDone! All icons generated.")
