from ...dialect_base import (
    DialectBase,
)


def size_array_intersect_sql(col_name_l, col_name_r):
    return f'''SELECT GET_ARRAY_LENGTH( ARRAY(
    SELECT {col_name_l}[i]
    FROM generate_series( array_lower({col_name_l}, 1), array_upper({col_name_l}, 1) ) i
    WHERE ARRAY[{col_name_l}[i]] && {col_name_r}
        )
    )'''


def regex_extract_sql(col_name, regex):
    return f"""
        regexp_substr({col_name}, '{regex}')
    """


def datediff_sql(
    col_name_l,
    col_name_r,
    date_threshold,
    date_metric,
    cast_str=False,
    date_format=None,
):
    if date_metric not in ("day", "month", "year"):
        raise ValueError("`date_metric` must be one of ('day', 'month', 'year')")

    if date_format is None:
        date_format = "yyyy-MM-dd"

    if cast_str:
        datediff_args = f"""
            to_date({col_name_l}, '{date_format}'),
            to_date({col_name_r}, '{date_format}')
        """
    else:
        datediff_args = f"{col_name_l}, {col_name_r}"

    date_f = f"""
        abs(
            datediff( 
                {date_metric},
                {datediff_args}
            )
        )
    """
    return f"""
        {date_f} <= {date_threshold}
    """


class RedshiftBase(DialectBase):
    @property
    def _sql_dialect(self):
        return "postgres"

    # @property
    # def _size_array_intersect_function(self):
    #     return size_array_intersect_sql

    @property
    def _regex_extract_function(self):
        return regex_extract_sql

    @property
    def _datediff_function(self):
        return datediff_sql
