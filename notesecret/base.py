import warnings

from sqlalchemy import MetaData, Table, create_engine, select, inspect

meta = MetaData()


def create_engines(url, **kwargs):
    return create_engine(url, **kwargs)


class BaseTable:
    def __init__(self, table_name, engine, *args, **kwargs):
        self.table_name = table_name
        self.table: Table = None
        self.engine = engine

    def create(self):
        meta.create_all(self.engine)

    def insert(self, values, keys=None, *args, **kwargs):
        cols = [col.name for col in self.table.columns]
        if isinstance(values, dict):
            values = dict([(k, v) for k, v in values.items() if k in cols])
        elif isinstance(values, list):
            if isinstance(values[0], dict):
                values = [dict([(k, v) for k, v in item.items() if k in cols]) for item in values]
            elif isinstance(values[0], list):
                values = [dict(zip(keys, item)) for item in values]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # code here...
            if str(self.engine.url).startswith('sqlite'):
                ins = self.table.insert(values=values).prefix_with("OR IGNORE")
            else:
                ins = self.table.insert(values=values).prefix_with("IGNORE")
            self.engine.execute(ins)

    def upsert(self, values):
        if str(self.engine.url).startswith('mysql'):
            from sqlalchemy.dialects.mysql import insert
        elif str(self.engine.url).startswith('sqlite'):
            from sqlalchemy.dialects.sqlite import insert
        else:
            from sqlalchemy.dialects.postgresql import insert

        stmt = insert(self.table).values(values)
        primary_keys = [key.name for key in inspect(self.table).primary_key]
        update_dict = {c.name: c for c in stmt.excluded if
                       not c.primary_key and c.name not in ('gmt_create', 'gmt_creat')}
        stmt = stmt.on_conflict_do_update(index_elements=primary_keys, set_=update_dict)
        self.engine.execute(stmt)

    def select_all(self):
        return self.engine.execute(select([self.table]))
