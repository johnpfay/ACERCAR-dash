# ACERCAR Dash

This is the "official" repository for the ACERCAR Dashboard - a work in progress by John Fay. 

Summer 2024

## Conda Recipe

```conda
conda create --name shinyserver_01 python=3.9 -y
activate shinyserver_01
pip install geopandas
pip install ipywidgets
pip install matplotlib
pip install shinywidgets
pip install scipy
```

## Description
Code for a dashboard allowing the user to  select [1] an LDAS variable, [2] a district and [3] a lag time, and display a dual-Y-axis plot comparing LDAS values with case rates for that district as well as a map of the correlation strengths between case rates and lagged LDAS variable for each district. 

The data used in the dashboard, in pickled format, include

* `Loreto_merged_data`: a dataframe indexed by `ubigeo`, `name`, `EpiweekStartDate`, `DataType`, species`, year`, `epiweek`, and `LDAS_variable`, listing the *cases*, *case rate*, and *LDAS value*.
* `Peru_departamentos`: a geodataframe listing the area, name, id, and total population of each district in Loreto.

The code includes functions to:

* `filter_data`:  Filter data on LDAS variable and species
* `line_plot`: Create a line plot from the LDAS variable, district (ubigeo), and offset
* `plot_correlations`: Plots the correlations between the specified variable and LDAS values on a choropleth map.