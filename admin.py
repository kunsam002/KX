import os
import uwsgi

from factories import create_app, initialize_api, initialize_blueprints

app = create_app('sme', 'config.AdminProdConfig')

with app.app_context():
    from kx.views.admin import control

    # Initialize the app blueprints
    initialize_blueprints(app, control)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
