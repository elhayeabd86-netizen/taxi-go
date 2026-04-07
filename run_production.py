"""
Lance l'app comme en production.
- Sur Windows : utilise waitress (gunicorn ne fonctionne pas)
- Sur Render/Linux : utilise gunicorn via le Procfile
"""
import os
from routes import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    try:
        from waitress import serve
        print(f" * Serveur Waitress sur http://0.0.0.0:{port}")
        serve(app, host="0.0.0.0", port=port)
    except ImportError:
        app.run(host="0.0.0.0", port=port, debug=False)
