from gsapy import GSA
import pandas as pd
import numpy as np
from datetime import datetime
from openpyxl import Workbook
import openpyxl
from modules import helper_funcs

# ============================================================================
# Bearing Information
# ============================================================================


bearings = {
    "bearing_1": {
        "name": "p9_e_free",
        "nodes": [32316, 32315],
        "type": "free",
        "reactions": 32316,
        "displacements": 32315,
    },
    "bearing_2": {
        "name": "p9_w_fixed",
        "nodes": [31307, 31306],
        "type": "fixed",
        "reactions": 31307,
        "displacements": 31306,
    },
    "bearing_3": {
        "name": "p10_e_free",
        "nodes": [30098, 30097],
        "type": "free",
        "reactions": 32316,
        "displacements": 32315,
    },
    "bearing_4": {
        "name": "p10_w_guided",
        "nodes": [17027, 12110],
        "type": "free",
        "reactions": 32316,
        "displacements": 32315,
    },
}


reaction_nodes = [17027, 30098, 31307, 32316]
displacement_nodes = [12110, 30097, 31306, 32315]

bearings_by_type = {"free": [17027, 31307], "fixed": [30098], "guided": [32316]}

bearings_by_name = {
    "p9_e_guided": [32316, 32315],
    "p9_w_free": [31307, 31306],
    "p10_e_fixed": [30098, 30097],
    "p10_w_free": [17027, 12110],
}

# ============================================================================
# Loading Information
# ============================================================================
# Dictionary of load types
reaction_cases_dict = {
    "G_Perm": ["C11", "C12"],
    "W_wind_no_traffic": [f"C{n}" for n in range(20, 32)],
    "W_wind_traffic": [f"C{n}" for n in range(32, 44)],
    "T_Temp": [f"C{n}" for n in range(95, 139)],
    "Traffic": [f"A{n}" for n in range(57, 74)],
}

disp_cases_dict = {
    "G_Perm": ["C11", "C12"],
    "G_Reverse": ["C6", "C7", "C8", "C9"],
    "W_wind_no_traffic": [f"C{n}" for n in range(20, 32)],
    "W_wind_traffic": [f"C{n}" for n in range(32, 44)],
    "T_Temp": [f"C{n}" for n in range(95, 139)],
    "Traffic": [f"A{n}" for n in range(33, 57)],
}

# ============================================================================
# Create Load Cases
# ============================================================================


def create_cases_df(cases):
    """
    Generate load cases dataframe from dictionary of load types and list of cases

    Parameters:
    ------------
    cases: dict
        dictionary of case types

    Returns:
    ---------
    df: DataFrame
        Dataframe of load cases with columns = ['type', 'case']
    """
    df = pd.DataFrame(columns=["type", "case"])
    row = 0
    for load_type in cases.keys():
        for load_case in cases[load_type]:
            df.loc[row] = [load_type, load_case]
            row += 1

    df.set_index("type", inplace=True)

    return df


reaction_cases = create_cases_df(reaction_cases_dict)
disp_cases = create_cases_df(disp_cases_dict)

# lists of reaction load cases to use to extract results from GSA
react_cases_static = (
    reaction_cases_dict["G_Perm"]
    + reaction_cases_dict["W_wind_no_traffic"]
    + reaction_cases_dict["W_wind_traffic"]
    + reaction_cases_dict["T_Temp"]
)

react_cases_traffic = reaction_cases_dict["Traffic"]


# lists of displacement load cases to use to extract results from GSA
disp_cases_static = (
    disp_cases_dict["G_Perm"]
    + disp_cases_dict["G_Reverse"]
    + disp_cases_dict["W_wind_no_traffic"]
    + disp_cases_dict["W_wind_traffic"]
    + disp_cases_dict["T_Temp"]
)

disp_cases_traffic = disp_cases_dict["Traffic"]


# ============================================================================
# Import GSA models as objects
# ============================================================================
static_model = GSA("models\WBBn_base_v48_base.gwb")
traffic_model = GSA("models\WBBn_base_v48_traffic (Node effects)_solved.gwb")

# ============================================================================
# Get results from GSA
# ============================================================================


def get_reactions_gsa(reaction_nodes, react_cases_static, react_cases_traffic):
    """
    get reactions from GSA. Store in dictionary of nodes as keys. Each node has a nested dictionary of cases and their reactions:

    reactions = {
      Node1: {
          case1: (Fx,Fy,Fz,Mx,My,Mz),
          case2: (Fx,Fy,Fz,Mx,My,Mz),
          ...},
      Node2: {
          ...},
      ...}

    parameters:
    -----------
    reaction_nodes: (list)
        dictionary of bearings to get results obtained from GSA
    static cases: (list)
        list of static cases
    traffic cases (list)
        list of traffic cases

    Returns:
    ---------
    reactions_by_node, reactions
    """
    node_reactions = {}
    for node in reaction_nodes:
        node_reactions[node] = {}
        for static_case in react_cases_static:
            reaction = static_model.get_node_reactions(node, static_case)
            node_reactions[node].update({static_case: reaction})

        for traffic_case in react_cases_traffic:
            reaction = traffic_model.get_node_reactions(node, traffic_case)
            node_reactions[node].update({traffic_case: reaction})

    # Convert dictionary of node reactions to dataframes, label columns and
    reactions_by_node = {}
    for node in node_reactions.keys():
        df = pd.DataFrame(data=node_reactions[node]).T
        df.columns = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]
        # add load type for each load case
        df = pd.merge(
            reaction_cases, df, how="outer", left_on="case", right_on=df.index
        )
        # add node column and move to column index '0'
        df["node"] = node

        helper_funcs.move_column_df(df, 0, "node")
        df.set_index(reaction_cases.index, inplace=True)
        reactions_by_node[node] = df

    reactions = pd.concat(list(reactions_by_node.values()))

    return reactions_by_node, reactions


reactions_by_node, reactions = get_reactions_gsa(
    reaction_nodes, react_cases_static, react_cases_traffic
)


reactions_by_type = (
    reactions.groupby(by=["node", reactions.index]).agg(["max", "min"]).stack()
)

reactions_by_type.drop(columns=["case"], inplace=True)


def get_displacements_gsa(displacement_nodes, disp_cases_static, disp_cases_traffic):
    """
    get displacements from GSA. Store in dictionary of nodes as keys. Each node has a nested dictionary of cases and their displacements:

    displacements = {
      Node1: {
          case1: (Dx,Dy,Dz,Rx,Ry,Rz),
          case2: (Dx,Dy,Dz,Rx,Ry,Rz),
          ...},
      Node2: {
          ...},
      ...}
    parameters:
    -----------
    displacement nodes: (list)
        dictionary of result types as keys and results obtained from GSA
    static cases: (list)
        list of static cases
    traffic cases (list)
        list of traffic cases

    Returns:
    ---------
    displacements
    """
    node_disp = {}
    for node in displacement_nodes:
        node_disp[node] = {}
        for static_case in disp_cases_static:
            disp = static_model.get_node_displacements(node, static_case)

            node_disp[node].update({static_case: disp})

        for traffic_case in disp_cases_traffic:
            disp = traffic_model.get_node_displacements(node, traffic_case)
            node_disp[node].update({traffic_case: disp})

    # Convert dictionary of node reactions to dataframes, one for each node
    displacements_by_node = {}
    for node in node_disp.keys():
        df = pd.DataFrame(data=node_disp[node]).T
        df.columns = ["Dx", "Dy", "Dz", "Rx", "Ry", "Rz"]
        # scale by 1000
        disp_scale = 1000
        df[df.columns] *= disp_scale
        # add load type for each load case
        df = pd.merge(disp_cases, df, how="outer", left_on="case", right_on=df.index)

        # add node column and move to column index '0'
        df["node"] = node
        helper_funcs.move_column_df(df, 0, "node")

        df.set_index(disp_cases.index, inplace=True)
        displacements_by_node[node] = df

    displacements = pd.concat(list(displacements_by_node.values()))

    return displacements_by_node, displacements


displacements_by_node, displacements = get_displacements_gsa(
    displacement_nodes, disp_cases_static, disp_cases_traffic
)

displacements_by_type = (
    displacements.groupby(by=["node", displacements.index]).agg(["max", "min"]).stack()
)

displacements_by_type.drop(columns=["case"], inplace=True)

# ============================================================================
# Calculate combinations for reactions and displacements
# ============================================================================


def combine_reactions(reaction_factors, reactions_by_node):
    """
    Combine reactions using combinations dictionary

    parameters:
    ------------
    combinations: dict
        Dictionary with combination factors to use
    reactions_by_node: dict
        Dictionary of Dataframes with reactions for each node

    Returns:
    ---------
    reaction_combinations_by_node: dict
        Dictionary of Dataframes with reactions for each node
    reaction_combinations: Dataframe
        Dataframes with combined reactions for all nodes

    """
    # obtain max and min reactions by load type for each node
    reaction_combinations_by_node = {}
    for node in reaction_nodes:
        reaction_columns = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]

        # Obtain maximum values for each load type
        max_G = reactions_by_node[node].loc["G_Perm", reaction_columns].max()
        max_LM1 = reactions_by_node[node].loc["Traffic", reaction_columns].max()

        # add minimum horizontal traffic load components for breaking,etc.
        if node in bearings_by_type["fixed"]:
            max_LM1[["Fx", "Fy"]] = [800, 200]
        elif node in bearings_by_type["guided"]:
            max_LM1[["Fy"]] = [200]

        max_W = reactions_by_node[node].loc["W_wind_no_traffic", reaction_columns].max()
        max_T = reactions_by_node[node].loc["T_Temp", reaction_columns].max()

        # Obtain minimum values for each load type
        min_G = reactions_by_node[node].loc["G_Perm", reaction_columns].max()
        min_LM1 = -reactions_by_node[node].loc["Traffic", reaction_columns].min()
        # add minimum horizontal traffic load components for breaking,etc.
        # min_LM1[['Fx', 'Fy']] = [-800, -200]

        min_W = (
            -reactions_by_node[node].loc["W_wind_no_traffic", reaction_columns].max()
        )
        min_W["Fz"] = -min_W["Fz"]
        min_T = -reactions_by_node[node].loc["T_Temp", reaction_columns].max()

        reaction_combinations = {}
        for comb in reaction_factors.keys():
            max_combs = [
                "uls_1",
                "uls_2",
                "uls_3",
                "uls_4",
                "slS_1",
                "sls_2",
                "sls_3",
                "sls_4",
            ]
            if comb in max_combs:
                factored_reaction = (
                    max_G.multiply(other=reaction_factors[comb]["G"])
                    + max_LM1.multiply(other=reaction_factors[comb]["LM1"])
                    + max_W.multiply(other=reaction_factors[comb]["W"])
                    + max_T.multiply(other=reaction_factors[comb]["T"])
                )
            else:
                factored_reaction = (
                    min_G.multiply(other=reaction_factors[comb]["G"])
                    + min_LM1.multiply(other=reaction_factors[comb]["LM1"])
                    + min_W.multiply(other=reaction_factors[comb]["W"])
                    + min_T.multiply(other=reaction_factors[comb]["T"])
                )
            factored_reaction["name"] = reaction_factors[comb]["name"]
            factored_reaction["limit_state"] = reaction_factors[comb]["type"]
            reaction_combinations[comb] = factored_reaction
        # convert combined reactions to df
        df = pd.DataFrame(reaction_combinations).T

        df.reset_index(level=0, inplace=True)
        df = df.rename(columns={"index": "combination"})

        # add node column and move to column index '0'
        df["node"] = node
        helper_funcs.move_column_df(df, 0, "node")
        helper_funcs.move_column_df(df, 1, "limit_state")
        helper_funcs.move_column_df(df, 2, "combination")
        helper_funcs.move_column_df(df, 3, "name")

        # create dictionary of combined reaction DataFrames per node
        reaction_combinations_by_node[node] = df

    # combine all node dataframes into one for export to excel
    reaction_combinations_df = pd.concat(list(reaction_combinations_by_node.values()))
    reaction_combinations_df.set_index("node", inplace=True)
    # Arrange table by node and limit state

    reaction_envelopes_df = (
        reaction_combinations_df.groupby(by=["node", "limit_state"])
        .agg(["max", "min"])
        .stack()
    )
    reaction_envelopes_df.drop(columns=["combination", "name"], inplace=True)
    return (
        reaction_combinations_by_node,
        reaction_combinations_df,
        reaction_envelopes_df,
    )


(
    reaction_combinations_by_node,
    reaction_combinations,
    reaction_envelopes,
) = combine_reactions(reaction_factors, reactions_by_node)


def combine_displacements(disp_factors, displacements_by_node):
    """
    Combine displacements using combinations dictionary

    parameters:
    ------------
    combinations: dict
        Dictionary with combination factors to use
    displacements_by_node: dict
        Dictionary of Dataframes with displacements for each node

    Returns:
    ---------
    combined_displacement_by_node: dict
        Dictionary of Dataframes with displacements for each node
    combined_displacement: Dataframe
        Dataframes with combined displacements for all nodes

    """
    # obtain max and min displacements by load type for each node
    displacement_combinations_by_node = {}
    for node in displacement_nodes:
        disp_cols = ["Dx", "Dy", "Dz", "Rx", "Ry", "Rz"]

        # Obtain maximum values for each load type
        max_G = displacements_by_node[node].loc["G_Perm", disp_cols].max()
        max_G_rev = displacements_by_node[node].loc["G_Reverse", disp_cols].sum()
        max_LM1 = displacements_by_node[node].loc["Traffic", disp_cols].max()
        max_W = displacements_by_node[node].loc["W_wind_no_traffic", disp_cols].max()
        max_T = displacements_by_node[node].loc["T_Temp", disp_cols].max()

        # Obtain minimum values for each load type
        min_G = displacements_by_node[node].loc["G_Perm", disp_cols].max()
        min_G_rev = displacements_by_node[node].loc["G_Reverse", disp_cols].sum()
        min_LM1 = displacements_by_node[node].loc["Traffic", disp_cols].min()
        min_W = -displacements_by_node[node].loc["W_wind_no_traffic", disp_cols].max()
        min_W["Dz"] = -min_W["Dz"]
        min_T = -displacements_by_node[node].loc["T_Temp", disp_cols].max()

        displacement_combinations = {}
        for comb in disp_factors.keys():
            max_combs = [
                "uls_1",
                "uls_2",
                "uls_3",
                "uls_4",
                "sls_1",
                "sls_2",
                "sls_3",
                "sls_4",
            ]
            if comb in max_combs:
                factored_displacement = 1 * (
                    +max_LM1.multiply(other=disp_factors[comb]["LM1"])
                    + max_W.multiply(other=disp_factors[comb]["W"])
                    + max_T.multiply(other=disp_factors[comb]["T"])
                )
            else:
                factored_displacement = 1 * (
                    +min_LM1.multiply(other=disp_factors[comb]["LM1"])
                    + min_W.multiply(other=disp_factors[comb]["W"])
                    + min_T.multiply(other=disp_factors[comb]["T"])
                )
            factored_displacement["name"] = reaction_factors[comb]["name"]
            factored_displacement["limit_state"] = reaction_factors[comb]["type"]
            displacement_combinations[comb] = factored_displacement
        # convert combined displacements to df
        df = pd.DataFrame(displacement_combinations).T

        df.reset_index(level=0, inplace=True)
        df = df.rename(columns={"index": "combination"})

        # add node column and move to column index '0'
        df["node"] = node
        helper_funcs.move_column_df(df, 0, "node")
        helper_funcs.move_column_df(df, 1, "limit_state")
        helper_funcs.move_column_df(df, 2, "combination")
        helper_funcs.move_column_df(df, 3, "name")

        # create dictionary of combined displacement DataFrames per node
        displacement_combinations_by_node[node] = df

    # combine all node dataframes into one for export to excel
    displacement_combinations_df = pd.concat(
        list(displacement_combinations_by_node.values())
    )
    displacement_combinations_df.set_index("node", inplace=True)

    # Arrange table by node and limit state for export to excel
    displacement_envelopes_df = (
        displacement_combinations_df.groupby(by=["node", "limit_state"])
        .agg(["max", "min"])
        .stack()
    )
    displacement_envelopes_df.drop(columns=["combination", "name"], inplace=True)

    return (
        displacement_combinations_by_node,
        displacement_combinations_df,
        displacement_envelopes_df,
    )


(
    displacement_combinations_by_node,
    displacement_combinations,
    displacement_envelopes,
) = combine_displacements(disp_factors, displacements_by_node)

# ============================================================================
# Save GSA Results as excel
# ============================================================================
bearing_reactions = {
    "cases": reaction_cases,
    "results": reactions,
    "results_by_type": reactions_by_type,
    "combinations": reaction_combinations,
    "envelopes": reaction_envelopes,
}

bearing_displacements = {
    "cases": disp_cases,
    "results": displacements,
    "results_by_type": displacements_by_type,
    "combinations": displacement_combinations,
    "envelopes": displacement_envelopes,
}


save_to_excel = True
if save_to_excel == True:
    helper_funcs.write_to_excel(bearing_reactions, "output/bearing_reactions")
    helper_funcs.write_to_excel(bearing_displacements, "output/bearing_displacements")


if __name__ == "__main__":
    print("\nOutputs successfully copied to bearing schedule")
