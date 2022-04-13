# bridge-bearings-schedule

Populate a bearing schedule from GSA results  


## Inputs
Information required to extract data from gsa:  

bearing nodes lists 
- Reaction nodes = [17027, 30098, 31307, 32316]  
- Displacement Nodes = [12110, 30097, 31306, 32315]

bearing references, location on structure 
- P9E_free = [32316, 32315]
- P9W_fixed = [31307, 31306]
- P10E_free = [30098, 30097]
- P10W_guided = [17027, 12110]

models
- static: self-weight, wind and temperature
- traffic: loads from node influence effects analysis

## Data to extract
Extract data for relevant nodes from gsa as .csv files for the following outputs:  
> use .txt file with GSA output strings in the folder

load cases 
- static
- traffic
- combination cases

forces
- static
- traffic

displacements
- static
- traffic

## Bearing Schedule Information

Run script to compile data:
- load cases and combinations
- reactions
- displacements

## Send to excel

output summary
- load cases and combination
- reactions
- displacements

or:  

- perform operations on load cases


# To Do

## data extraction  
- load csv from table start and end

    or 

- load data from gsa using gsa.py


## data sorting
- add load type label to load cases

## data processing

- send to excel for processing  
    or 
- perform operations on load cases
