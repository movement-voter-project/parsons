import ast
import petl
import logging

logger = logging.getLogger(__name__)

# These are reserved words by Redshift and cannot be used as column names.
RESERVED_WORDS = ['AES128', 'AES256', 'ALL', 'ALLOWOVERWRITE', 'ANALYSE', 'ANALYZE', 'AND', 'ANY',
                  'ARRAY', 'AS', 'ASC', 'AUTHORIZATION', 'BACKUP', 'BETWEEN', 'BINARY',
                  'BLANKSASNULL', 'BOTH', 'BYTEDICT', 'BZIP2', 'CASE', 'CAST', 'CHECK', 'COLLATE',
                  'COLUMN', 'CONSTRAINT', 'CREATE', 'CREDENTIALS', 'CROSS', 'CURRENT_DATE',
                  'CURRENT_TIME', 'CURRENT_TIMESTAMP', 'CURRENT_USER', 'CURRENT_USER_ID',
                  'DEFAULT', 'DEFERRABLE', 'DEFLATE', 'DEFRAG', 'DELTA', 'DELTA32K', 'DESC',
                  'DISABLE', 'DISTINCT', 'DO', 'ELSE', 'EMPTYASNULL', 'ENABLE', 'ENCODE', 'ENCRYPT',
                  'ENCRYPTION', 'END', 'EXCEPT', 'EXPLICIT', 'FALSE', 'FOR', 'FOREIGN', 'FREEZE',
                  'FROM', 'FULL', 'GLOBALDICT256', 'GLOBALDICT64K', 'GRANT', 'GROUP', 'GZIP',
                  'HAVING', 'IDENTITY', 'IGNORE', 'ILIKE', 'IN', 'INITIALLY', 'INNER', 'INTERSECT',
                  'INTO', 'IS', 'ISNULL', 'JOIN', 'LEADING', 'LEFT', 'LIKE', 'LIMIT', 'LOCALTIME',
                  'LOCALTIMESTAMP', 'LUN', 'LUNS', 'LZO', 'LZOP', 'MINUS', 'MOSTLY13', 'MOSTLY32',
                  'MOSTLY8', 'NATURAL', 'NEW', 'NOT', 'NOTNULL', 'NULL', 'NULLS', 'OFF', 'OFFLINE',
                  'OFFSET', 'OLD', 'ON', 'ONLY', 'OPEN', 'OR', 'ORDER', 'OUTER', 'OVERLAPS',
                  'PARALLEL', 'PARTITION', 'PERCENT', 'PERMISSIONS', 'PLACING', 'PRIMARY', 'RAW',
                  'READRATIO', 'RECOVER', 'REFERENCES', 'RESPECT', 'REJECTLOG', 'RESORT', 'RESTORE',
                  'RIGHT', 'SELECT', 'SESSION_USER', 'SIMILAR', 'SOME', 'SYSDATE', 'SYSTEM',
                  'TABLE', 'TAG', 'TDES', 'TEXT255', 'TEXT32K', 'THEN', 'TIMESTAMP', 'TO', 'TOP',
                  'TRAILING', 'TRUE', 'TRUNCATECOLUMNS', 'UNION', 'UNIQUE', 'USER', 'USING',
                  'VERBOSE', 'WALLET', 'WHEN', 'WHERE', 'WITH', 'WITHOUT']


# Max length of a Redshift VARCHAR column
VARCHAR_MAX = 65535
# List of varchar lengths to use for columns -- this list needs to be in order from smallest to
# largest
VARCHAR_STEPS = [32, 64, 128, 256, 512, 1024, 4096, 8192, 16384]


class RedshiftCreateTable(object):

    def __init__(self):

        pass

    def create_statement(self, tbl, table_name, padding=None, distkey=None, sortkey=None,
                         varchar_max=None, varchar_truncate=True, columntypes=None):

        # Warn the user if they don't provide a DIST key or a SORT key
        self._log_key_warning(distkey=distkey, sortkey=sortkey, method='copy')

        # Generate a table create statement

        # Validate and rename column names if needed
        tbl.table = petl.setheader(tbl.table, self.column_name_validate(tbl.columns))

        if tbl.num_rows == 0:
            raise ValueError('Table is empty. Must have 1 or more rows.')

        mapping = self.generate_data_types(tbl)

        if padding:
            mapping['longest'] = self.vc_padding(mapping, padding)

        if varchar_max:
            mapping['longest'] = self.vc_max(mapping, varchar_max)

        if varchar_truncate:
            mapping['longest'] = self.vc_trunc(mapping)

        mapping['longest'] = self.vc_validate(mapping)

        # Add any provided column type overrides
        if columntypes:
            for i in range(len(mapping['headers'])):
                col = mapping['headers'][i]
                if columntypes.get(col):
                    mapping['type_list'][i] = columntypes[col]

        # Enclose in quotes
        mapping['headers'] = ['"{}"'.format(h) for h in mapping['headers']]

        return self.create_sql(table_name, mapping, distkey=distkey, sortkey=sortkey)

    def data_type(self, val, current_type):
        # Determine the Redshift data type of a given value

        try:
            # Convert to string to reevaluate data type
            t = ast.literal_eval(str(val))
        except ValueError:
            return 'varchar'
        except SyntaxError:
            return 'varchar'

        if type(t) in [int, float]:
            if (type(t) in [int] and
                    current_type not in ['decimal', 'varchar']):

                # Make sure that it is a valid integer
                if not self.is_valid_integer(val):
                    return 'varchar'

                # Use smallest possible int type (but don't bother with smallint)
                if (-2147483648 < t < 2147483647) and current_type not in ['bigint']:
                    return 'int'
                else:
                    return 'bigint'
            if ((type(t) is float or current_type in ['decimal'])
                    and current_type not in ['varchar']):
                return 'decimal'
        else:
            return 'varchar'

    def is_valid_integer(self, val):

        # Valid ints in python can contain an underscore, but Redshift can't. This
        # checks to see if there is an underscore in the value and turns it into
        # a varchar if so.
        try:
            if '_' in val:
                return False

        except TypeError:
            return True

        # If it has a leading zero, we should treat it as a varchar, since it is
        # probably there for a good reason (e.g. zipcode)
        if val.isdigit():
            if val[0] == '0':
                return False

        return True

    def generate_data_types(self, table):
        # Generate column data types

        longest, type_list = [], []

        cont = petl.records(table.table)

        # Populate empty values for the columns
        for col in table.columns:
            longest.append(0)
            type_list.append('')

        for row in cont:
            for i in range(len(row)):
                # NA is the csv null value
                if type_list[i] == 'varchar' or row[i] in ['NA', '']:
                    pass
                else:
                    var_type = self.data_type(row[i], type_list[i])
                    type_list[i] = var_type

                # Calculate width
                if len(str(row[i]).encode('utf-8')) > longest[i]:
                    longest[i] = len(str(row[i]).encode('utf-8'))

        # In L138 'NA' and '' will be skipped
        # If the entire column is either one of those (or a mix of the two)
        # the type will be empty.
        # Fill with a default varchar
        type_list = [typ or 'varchar' for typ in type_list]

        return {'longest': longest,
                'headers': table.columns,
                'type_list': type_list}

    def vc_padding(self, mapping, padding):
        # Pad the width of a varchar column

        return [int(c + (c * padding)) for c in mapping['longest']]

    def vc_max(self, mapping, columns):
        # Set the varchar width of a column to the maximum

        for c in columns:

            try:
                idx = mapping['headers'].index(c)
                mapping['longest'][idx] = VARCHAR_MAX

            except KeyError as error:
                logger.error('Could not find column name provided.')
                raise error

        return mapping['longest']

    def vc_trunc(self, mapping):

        return [VARCHAR_MAX if c > VARCHAR_MAX else c for c in mapping['longest']]

    def vc_validate(self, mapping):

        return [1 if c == 0 else c for c in mapping['longest']]

    def create_sql(self, table_name, mapping, distkey=None, sortkey=None):
        # Generate the sql to create the table

        statement = 'create table {} ('.format(table_name)

        for i in range(len(mapping['headers'])):
            if mapping['type_list'][i] == 'varchar':
                varchar_length = mapping['longest'][i]
                statement = (statement + '\n  {} varchar({}),').format(str(mapping['headers'][i])
                                                                       .lower(),
                                                                       str(varchar_length))
            else:
                statement = (statement + '\n  ' + '{} {}' + ',').format(str(mapping['headers'][i])
                                                                        .lower(),
                                                                        mapping['type_list'][i])

        statement = statement[:-1] + ') '

        if distkey:
            statement += '\ndistkey({}) '.format(distkey)

        if sortkey:
            statement += '\nsortkey({})'.format(sortkey)

        statement += ';'

        return statement

    def column_name_validate(self, columns):
        # Validate the column names and rename if not valid

        clean_columns = []

        for idx, c in enumerate(columns):

            # Lowercase
            c = c.lower()

            # Remove spaces. Technically allowed with double quotes
            # but I think that it is bad practice.
            c = c.replace(' ', '')

            # if column is an empty string, replace with 'col_INDEX'
            if c == '':
                logger.info(f'Column is an empty string. Renaming column.')
                c = f'col_{idx}'

            # If column is a reserved word, replace with 'col_INDEX'. Technically
            # you can allow these with quotes, but I think that it is bad practice
            if c.upper()in RESERVED_WORDS:
                logger.info(f'{c} is a Redshift reserved word. Renaming column.')
                c = f'col_{idx}'

            # If column name begins with an integer, preprent with 'x_'
            if c[0].isdigit():
                logger.info(f'{c} begins with digit. Renaming column.')
                c = f'x_{c}'

            # If column name length is greater than 120 characters, truncate.
            # Technically, you can have up to 127 bytes, which might allow
            # for a few more characters, but playing it safe.
            if len(c) > 120:
                logger.info(f'Column {c[:10]}... too long. Truncating column name.')
                c = c[:120]

            # Check for duplicate column names and add index if a dupe is found.
            if c in clean_columns:
                c = f'{c}_{idx}'

            clean_columns.append(c)

        return clean_columns

    @staticmethod
    def _log_key_warning(distkey=None, sortkey=None, method=''):
        # Log a warning message advising the user about DIST and SORT keys

        if distkey and sortkey:
            return

        keys = [
            (distkey, "DIST", "https://aws.amazon.com/about-aws/whats-new/2019/08/amazon-redshift-"
                              "now-recommends-distribution-keys-for-improved-query-performance/"),
            (sortkey, "SORT", "https://docs.amazonaws.cn/en_us/redshift/latest/dg/c_best-practices-"
                              "sort-key.html")
        ]
        warning = "".join([
            "You didn't provide a {} key to method `parsons.redshift.Redshift.{}`.\n"
            "You can learn about best practices here:\n{}.\n".format(
                keyname, method, keyinfo
            ) for key, keyname, keyinfo in keys if not key])

        warning += "You may be able to further optimize your queries."

        logger.warning(warning)

    @staticmethod
    def _round_longest(longest):
        # Find the value that will work best to fit our longest column value
        for step in VARCHAR_STEPS:
            # Make sure we have padding
            if longest < step / 2:
                return step

        return VARCHAR_MAX
