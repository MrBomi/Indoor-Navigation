import os
from server import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8574))
    # Only use debug mode locally, not in production
    #debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=True)