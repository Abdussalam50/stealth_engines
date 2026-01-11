import os
import sys

# Agar Python bisa menemukan folder 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# IMPORT UTAMA: Ini yang dicari Railway!
# Kita mengambil 'app' dari file main.py yang ada di dalam folder app
from app.main import app 

if __name__ == "__main__":
    import uvicorn
    # Bagian ini hanya jalan kalau kamu run di laptop (python server.py)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)