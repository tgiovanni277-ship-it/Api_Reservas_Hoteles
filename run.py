from app import create_app
from app.config import DEBUG

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=DEBUG)
