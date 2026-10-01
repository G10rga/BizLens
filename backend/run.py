import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_ENV", "development").lower() != "production"
    # threaded=True so a slow Prophet fit doesn't freeze the whole SPA
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
