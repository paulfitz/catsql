from __future__ import unicode_literals
import json
from sqlalchemy import asc, desc, text, types
from sqlalchemy.exc import OperationalError, InvalidRequestError
from sqlalchemy.sql import expression, functions


def recursive_find(data, key):
    result = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key:
                result.append(v)
            else:
                result += recursive_find(v, key)
    elif isinstance(data, list):
        for item in data:
            result += recursive_find(item, key)
    return result


class Filter(object):
    def __init__(self, database, columns=None):
        self.database = database
        self.queries = None
        self.selected_columns = columns
        self._query()

    def distinct(self, distinct=True):
        for query in self.queries:
            query['rows'] = query['rows'].distinct()
        return self

    def where_sql(self, sql):
        return self.where_sqls([sql])

    def where_sqls(self, sqls):
        # sqls is list of sql text 'where'-style conditions

        active_queries = []
        for query in self.queries:
            for sql in sqls:
                query['rows'] = query['rows'].filter(text(sql))
            try:
                query['rows'].limit(1).all()  # inefficient
                active_queries.append(query)
            except OperationalError:
                # should cache these and show if no results at all found
                continue
        self.queries = active_queries
        return self

    def where_kv(self, conditions):
        # conditions is a dict
        active_queries = []
        for query in self.queries:
            try:
                query['rows'] = query['rows'].filter_by(**conditions)
                active_queries.append(query)
            except InvalidRequestError:
                continue
        self.queries = active_queries
        return self

    def select_from(self, sql_text):
        rows = self.database.session.execute(text(sql_text))
        self.queries = [
            {
                'table_name': 'custom',
                'table': rows._metadata,
                'rows': rows
            }
        ]
        return self

    def grep(self, pattern, case_sensitive=False):
        for query in self.queries:
            query['rows'] = self._add_grep(query['table'], query['rows'], pattern,
                                           case_sensitive=case_sensitive)
        return self

    def limit(self, limit):
        for query in self.queries:
            query['rows'] = query['rows'].limit(limit)
        return self

    def _query(self):

        table_items = self.database.tables_metadata.items()

        self.queries = []

        for table_name, table in sorted(table_items):

            if self.database.schema:
                schema = self.database.schema + '.'
                if table_name.startswith(schema):
                    table_name = table_name[len(schema):]

            if self.database.tables is not None:
                if table_name not in self.database.tables:
                    continue

            if self.selected_columns is not None:
                ok = True
                for name in self.selected_columns:
                    if name not in table.c:
                        ok = False
                if not ok:
                    continue
                rows = self.database.session.query(*[table.c[name]
                                                     for name in self.selected_columns])
            else:
                rows = self.database.session.query(table)
            self.queries.append({
                'table_name': table_name,
                'table': table,
                'rows': rows
            })

    def _add_grep(self, table, query, sequence, case_sensitive):
        # functions.concat would be neater, but doesn't seem to translate
        # correctly on sqlite
        parts = ''
        for idx, column in enumerate(table.columns):
            if not self.ok_column(column.name):
                continue
            if parts != '':
                parts = parts + ' // '
            part = functions.coalesce(expression.cast(column,
                                        types.Unicode),
                                        '')
            parts = parts + part
        if case_sensitive:
            query = query.filter(parts.contains(sequence))
        else:
            query = query.filter(parts.ilike('%%' + sequence + '%%'))
        return query

    def _default_order(self):
        for query in self.queries:
            table = query['table']
            primary_key = table.primary_key
            if self.selected_columns:
                query['rows'] = query['rows'].order_by(*[table.c[name]
                                                         for name in self.selected_columns])
            elif len(primary_key) >= 1:
                query['rows'] = query['rows'].order_by(*primary_key)
            elif len(table.c) >= 1:
                query['rows'] = query['rows'].order_by(*table.c)
        return self

    def order(self, ordering=None):
        if ordering is None:
            return self._default_order()
        for query in self.queries:
            table = query['table']
            orders = []
            for name in ordering:
                c = name[-1]
                order = name
                if c == '+' or c == '-':
                    order = order[:-1]
                order = table.c[order]
                if c == '+':
                    order = asc(order)
                elif c == '-':
                    order = desc(order)
                orders.append(order)
            if len(orders) > 0:
                query['rows'] = query['rows'].order_by(*orders)
        return self

    def where_kv_with_expansion(self, conditions):
        # conditions is a dict
        active_queries = []
        for query in self.queries:
            try:
                table = query['table']
                for key, val in conditions.items():
                    if key not in table.c:
                        raise InvalidRequestError('key not present')
                    if val == "" or val[0] != '@':
                        query['rows'] = query['rows'].filter(table.c[key] == val)
                    else:
                        file_filter = val[1:]
                        with open(file_filter, 'r') as fin:
                            data = json.load(fin)
                            vals = recursive_find(data, key)
                            query['rows'] = query['rows'].filter(table.c[key].in_(vals))
                active_queries.append(query)
            except InvalidRequestError:
                continue
        self.queries = active_queries
        return self

    def __iter__(self):
        return self.queries.__iter__()

    def __len__(self):
        return len(self.queries)

    def __getitem__(self, idx):
        return self.queries[idx]

    def ok_column(self, name):
        if self.selected_columns:
            if name not in self.selected_columns:
                return False
        return True

    @property
    def rows(self):
        if len(self) > 1:
            raise KeyError("more than one table in results")
        if len(self) == 0:
            return []
        return self[0]['rows']

    @property
    def row(self):
        rows = self.rows.all()
        if len(rows) > 1:
            raise KeyError("more than one row in results")
        return rows[0]
