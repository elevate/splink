from .model import Model

from .charts import load_chart_definition, altair_if_installed_else_json

initial_template = """
Initial probability of match (prior) = λ = {lam:.4g}
"""

col_template = [
    ("Comparison of {column_name}.  Values are:", ""),
    ("{column_name}_l:", "{value_l}"),
    ("{column_name}_r:", "{value_r}"),
    ("Comparison has:", "{num_levels} levels"),
    ("Level for this comparison:", "{gamma_column_name} = {gamma_index}"),
    ("m probability = P(level|match):", "{m_probability:.4g}"),
    ("u probability = P(level|non-match):", "{u_probability:.4g}"),
    ("Bayes factor = m/u:", "{bayes_factor:.4g}"),
    ("New probability of match (updated belief):", "{updated_belief:.4g}"),
]

end_template = """
Final probability of match = {final:.4g}

Reminder:

The m probability for a given level is the proportion of matches which are in this level.
We would generally expect the highest similarity level to have the largest proportion of matches.
For example, we would expect first name field to match exactly amongst most matching records, except where nicknames, aliases or typos have occurred.
For a comparison column that changes through time, like address, we may expect a lower proportion of comparisons to be in the highest similarity level.

The u probability for a given level is the proportion of non-matches which are in this level.
We would generally expect the lowest similarity level to have the highest proportion of non-matches, but the magnitude depends on the cardinality of the field.
For example, we would expect that in the vast majority of non-matching records, the date of birth field would not match.  However, we would expect it to be common for gender to match amongst non-matches.
"""


def intuition_report(row_dict: dict, model: Model):
    """Generate a text summary of a row in the comparison table which explains how the match_probability was computed

    Args:
        row_dict (dict): A python dictionary representing the comparison row
        model (Model): splink Model object

    Returns:
        string: The intuition report
    """

    lam = model.current_settings_obj["proportion_of_matches"]
    report = initial_template.format(lam=lam)
    current_prob = lam

    for cc in model.current_settings_obj.comparison_columns_list:
        d = cc.describe_row_dict(row_dict)

        bf = d["bayes_factor"]

        a = bf * current_prob
        new_p = a / (a + (1 - current_prob))
        d["updated_belief"] = new_p
        current_prob = new_p

        col_report = []
        col_report.append("------")
        for (blurb, value) in col_template:
            blurb_fmt = blurb.format(**d)

            value_fmt = value.format(**d)
            col_report.append(f"{blurb_fmt:<50} {value_fmt}")
        col_report.append("\n")
        col_report = "\n".join(col_report)
        report += col_report

    report += end_template.format(final=new_p)

    if len(model.current_settings_obj["blocking_rules"]) > 1:
        match_key = int(row_dict["match_key"])
        br = model.current_settings_obj["blocking_rules"][match_key]
        br = f"\nThis comparison was generated by the blocking rule: {br}"
        report += br

    return report


def _get_bayes_factors(row_dict, model):
    bayes_factors = []
    lam = model.current_settings_obj["proportion_of_matches"]
    for cc in model.current_settings_obj.comparison_columns_list:
        row_desc = cc.describe_row_dict(row_dict, lam)
        bayes_factors.append(row_desc)

    return bayes_factors


def bayes_factor_chart(row_dict, model):
    chart_path = "bayes_factor_chart_def.json"
    bayes_factor_chart_def = load_chart_definition(chart_path)
    bayes_factor_chart_def["data"]["values"] = _get_bayes_factors(row_dict, model)
    bayes_factor_chart_def["encoding"]["y"]["field"] = "column_name"
    del bayes_factor_chart_def["encoding"]["row"]

    return altair_if_installed_else_json(bayes_factor_chart_def)
