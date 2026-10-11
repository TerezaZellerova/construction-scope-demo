"""Fail deployment before application exposure if production settings are unsafe."""
import security
import core
security.validate_configuration()
core.initialize()
with core.connect() as db:
    assert db.execute('SELECT count(*) FROM projects').fetchone()[0]==3
print('Configuration and synthetic PostgreSQL schema validated')
