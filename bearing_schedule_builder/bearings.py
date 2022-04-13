class Bearings:
    def __init__(self) -> None:
        self.bearings = {
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
