from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from custom_session import M_scoped_session
from sqlalchemy import inspect
import Schema


engine = create_engine('sqlite:///database.db', echo=False)
inspector = inspect(engine)
schemas = inspector.get_schema_names()
Session_factory = sessionmaker(bind=engine)
Session = M_scoped_session(Session_factory)

with Session as session:
    # session.query()
    # result = session.query.count()
    # print(result)
    pass


# for schema in schemas:
#     print("schema: %s" % schema)
#     for table_name in inspector.get_table_names(schema=schema):
#         for column in inspector.get_columns(table_name, schema=schema):
#             print("Column: %s" % column)