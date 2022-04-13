import json
import pandas as pd

class LoadFactors:
    def __init__(self):
        self.factors = pd.read_csv(
            'bearing_schedule_builder\load_factors.csv')
        self.reaction_uls = (
            self.factors.loc[(
                (self.factors['limit_state'] == 'uls' ) &
                (self.factors['case'] == 'reaction')
            )]
        )
        self.reaction_sls = (
            self.factors.loc[(
                (self.factors['limit_state'] == 'sls' ) &
                (self.factors['case'] == 'reaction')
            )]
        )
        self.displacement_uls = (
            self.factors.loc[(
                (self.factors['limit_state'] == 'uls') &
                (self.factors['case'] == 'reaction')
            )]
        )
        self.displacement_sls = (
            self.factors.loc[(
                (self.factors['limit_state'] == 'sls') &
                (self.factors['case'] == 'reaction')
            )]
        )

if __name__ == "__main__":
    factors = LoadFactors()
    
    print(factors.reaction_uls)