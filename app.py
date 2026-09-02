"""Ponto de entrada da aplicação.

Uso:
    python app.py

Aplica as migrations pendentes antes de subir, para que um clone limpo
funcione sem comando extra. Ver AUTO_MIGRATE no .env.example.
"""

import logging

from app import aplicar_migrations, create_app

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = create_app()


if __name__ == "__main__":
    aplicar_migrations(app)

    print(f"\nSwagger em http://{app.config['HOST']}:{app.config['PORT']}/swagger\n")

    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
