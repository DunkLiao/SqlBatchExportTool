from app.models.config_model import AppConfig


def test_loads_current_db_config_format() -> None:
    config = AppConfig.from_dict(
        {
            "db": {
                "host": "10.9.1.223",
                "port": 1521,
                "service_name": "reportu",
                "username": "134719",
                "password": "secret",
            }
        }
    )

    assert config.db.host == "10.9.1.223"
    assert config.db.port == 1521
    assert config.db.service_name == "reportu"
    assert config.db.username == "134719"
    assert config.db.password == "secret"


def test_loads_legacy_database_dsn_format() -> None:
    config = AppConfig.from_dict(
        {
            "database": {
                "username": "134719",
                "password": "secret",
                "dsn": "10.9.1.223:1521/reportu",
            },
            "sql_folder_path": "d:\\sql",
            "output_excel_path": "d:\\output.xlsx",
        }
    )

    assert config.db.host == "10.9.1.223"
    assert config.db.port == 1521
    assert config.db.service_name == "reportu"
    assert config.db.username == "134719"
    assert config.db.password == "secret"
    assert config.last_sql_folder == "d:\\sql"
    assert config.last_output_excel == "d:\\output.xlsx"
