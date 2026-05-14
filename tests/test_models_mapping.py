from sqlalchemy.orm import configure_mappers

import app.models


def test_models_mappers_configure() -> None:
    configure_mappers()
