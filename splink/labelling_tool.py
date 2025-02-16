import json
import logging
import os
import pkgutil
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from jinja2 import Template

from .misc import EverythingEncoder
from .splink_dataframe import SplinkDataFrame

# https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
if TYPE_CHECKING:
    from .linker import Linker

logger = logging.getLogger(__name__)


def generate_labelling_tool_comparisons(
    linker: "Linker", unique_id, source_dataset, match_weight_threshold=-4
):

    # ensure the tf table exists
    concat_with_tf = linker._initialise_df_concat_with_tf()

    settings = linker._settings_obj

    source_dataset_condition = ""

    if source_dataset is not None:
        sds_col = settings._source_dataset_input_column
        source_dataset_condition = f"""
          and {sds_col} = '{source_dataset}'
        """

    sql = f"""
    select *
    from __splink__df_concat_with_tf
    where {settings._unique_id_column_name} = '{unique_id}'
    {source_dataset_condition}
    """

    linker._enqueue_sql(sql, "__splink__df_labelling_tool_record")
    splink_df = linker._execute_sql_pipeline([concat_with_tf])

    matches = linker.find_matches_to_new_records(
        splink_df.physical_name, match_weight_threshold=match_weight_threshold
    )

    return matches


def render_labelling_tool_html(
    linker: "Linker",
    df_comparisons: SplinkDataFrame,
    out_path="labelling_tool.html",
    view_in_jupyter=False,
    show_splink_predictions_in_interface=True,
    overwrite: bool = True,
):

    settings: dict = linker._settings_obj.as_dict()

    logger.warning(
        "\nWARNING:\n"
        "The Splink labelling tool is still in development, which means some "
        "features may change and there may be bugs.\nYour feedback will help us "
        "improve it. Go to\n"
        "github.com/moj-analytical-services/splink/discussions/new?category=general"
        "\nto give us feedback."
    )

    comparisons_recs = df_comparisons.as_pandas_dataframe()

    comparisons_recs = comparisons_recs.replace(r"^\s*$", "", regex=True)

    comparisons_recs = comparisons_recs.fillna(np.nan).replace(
        [np.nan, pd.NA], ["", ""]
    )

    comparisons_recs = comparisons_recs.to_dict(orient="records")
    # Render template with cluster, nodes and edges
    template_path = "files/labelling_tool/template.j2"
    template = pkgutil.get_data(__name__, template_path).decode("utf-8")
    template = Template(template)

    slt_text = pkgutil.get_data(__name__, "files/labelling_tool/slt.js")
    slt_text = slt_text.decode("utf-8")

    template_data = {
        "slt": slt_text,
        "pairwise_comparison_data": json.dumps(comparisons_recs, cls=EverythingEncoder),
        "splink_settings_data": json.dumps(settings, cls=EverythingEncoder),
        "view_in_jupyter": view_in_jupyter,
        "show_splink_predictions_in_interface": show_splink_predictions_in_interface,
    }

    rendered = template.render(**template_data)

    if os.path.isfile(out_path) and not overwrite:
        raise ValueError(
            f"The path {out_path} already exists. Please provide a different path."
        )
    else:

        with open(out_path, "w", encoding="utf-8") as html_file:
            html_file.write(rendered)
        # return the rendered dashboard html for inline viewing in the notebook
        return rendered
