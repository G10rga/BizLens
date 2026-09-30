from app import create_app

app = create_app()

if __name__ == "__main__":
    # threaded=True so a slow Prophet fit doesn't freeze the whole SPA
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
