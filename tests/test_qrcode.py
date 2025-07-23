import os
from app.main import generate_qr

def test_generate_qr_creates_file(tmp_path):
    os.makedirs("static/qrcodes", exist_ok=True)  # 👈 Ordner sicherstellen

    link = "https://example.com/respond/abc123"
    filename = "testqr"
    path = generate_qr(link, filename)

    assert os.path.exists(path)
    assert path.endswith(".png")