# App to interactively view lineplots of LDAS variables and malaria case counts
# This app has three widgets:
# - LDAS variable selector     [Dropdown]
# - District (ubigeo) selector [Dropdown]
# - Offset value               [Slider]

#%%Import packages
#Import packages
import scipy
import pandas as pd
import geopandas as gpd
from pathlib import Path
import json
import matplotlib.pyplot as plt
from shinywidgets import output_widget, render_widget

import ipyleaflet
from branca.colormap import linear

#from shiny.express import input, render, ui
from shiny import ui, render, App

#%%Read in LDAS data (long format)
df_merged = pd.read_pickle(Path(__file__).parent / 'Loreto_merged_data')
gdf_districts = gpd.GeoDataFrame(pd.read_pickle(Path(__file__).parent / 'Peru_departamentos'))

#Filter function (whenever the LDAS variable changes)
def filter_data(df=df_merged, var='Rainfall(mm)', species='p_fal'):
    '''Filter data on LDAS variable and species'''
    #Filter the data for a single variable and species
    df_filtered = df.xs(var, level='LDAS_variable').xs(species, level='species')
    #Sort the data on ubigeo and EpiweekStartDate
    df_filtered.sort_values(['ubigeo','EpiweekStartDate'], inplace=True)
    return df_filtered

#%% FUNCTIONS
#Plot function
def line_plot(the_var, the_ubigeo, the_offset):
    '''Create a line plot'''
    #Create the plot title
    the_title = f"P. Vivax cases & {the_var} for district {the_ubigeo}: {the_offset} weeks offset"
    print(the_title)

    #Set the start and end times
    start_time = '2010-01-01'
    end_time = '2024-05-01'

    #Filter the data for the var and the ubigeo
    df_plot = (df_merged.xs(the_ubigeo, level='ubigeo').xs(the_var,level='LDAS_variable').xs('p_fal',level='species')).reset_index()

    #Apply the offset to the case rate values
    df_plot['case_rate'] = df_plot['case_rate'].shift(the_offset)

    ## Plot the LDAS variable, split into retrospective and forecast components
    fig, ax = plt.subplots()
    ax.plot(df_plot['EpiweekStartDate'], df_plot['case_rate'], label='Case Rate')
    ax.set_title(the_title)
    ax.set_ylabel('Case Rate')

    #Set the legend
    ax.legend([the_var],loc='upper left')

    #Create a shared axis for the surveillance data
    shared_axis = ax.twinx()
    shared_axis.set_xlim(pd.Timestamp(start_time), pd.Timestamp(end_time))

    #Plot the surveillance data on the same x-axis
    shared_axis.plot(df_plot['EpiweekStartDate'], df_plot['LDAS_value'],color='r',label=the_var,alpha=0.5,linewidth=0.3)
    #shared_axis.legend(loc='upper right')

    #Set the x-limits
    ax.set_xlim(pd.Timestamp(start_time), pd.Timestamp(end_time))

#Create map of correlations
def plot_correlations(the_var,the_offset,basemap):
    #FILTER DATA
    df_filtered = df_merged.xs(the_var,level='LDAS_variable').xs('p_fal',level='species')

    #COMPUTE CORRELATIONS
    df_correlation = pd.DataFrame(df_filtered
            .groupby(['ubigeo','name'])
            .apply(lambda x: x['case_rate'].shift(the_offset).corr(x['LDAS_value'], method='spearman'))
            ).reset_index().rename(columns={0:'correlation'})

    #JOIN WITH SPATIAL FEATURES
    gdf = pd.merge(
        left=gdf_districts,
        right=df_correlation, 
        left_on=['id','name'], 
        right_on=['ubigeo','name'], 
        how='left')
    gdf.set_index('ubigeo', inplace=True)

    #CREATE CHOROPLETH OBJECT
    # map key value dict
    geojson_gdf = json.loads(gdf.to_json())
    key_value_dict =  dict(zip(gdf.index.tolist(), gdf['correlation'].tolist()))

    # Create the ipyleaflet choropleth object
    choro_layer = ipyleaflet.Choropleth(
        geo_data=geojson_gdf,
        choro_data=key_value_dict,
        colormap=linear.viridis,
        nan_color="grey",
        nan_opacity=0.5,
        border_color='black',
        style={'fillOpacity': 0.8},
        scheme='EqualInterval', 
        k=5)

    # add to basemap
    basemap.add(choro_layer)
    

    return basemap

#%%Create app layout
app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.panel_sidebar(   
        #LDAS selector
        ui.input_select(
            id="LDAS_select",
            label="LDAS variable:",
            choices=list(df_merged.index.get_level_values('LDAS_variable').unique()) 
        ),
        #ubigeo selector
        ui.input_select(
            id="district_select",  
            label="District ID:",  
            choices=list(df_merged.index.get_level_values('ubigeo').unique())
        ),
        #Offset slider
        ui.input_slider("offset_select", "Lag time (weeks)", min=-10, max=10, value=0),
        ),
        #Map
        output_widget("create_basemap")
    ),
    ui.panel_main(
        ui.output_plot("line_plot2")
    ),  
)

#%% Server 
def server(input, output, session):
    @render.plot(alt="A plot")
    #Function to populate the line plot
    def line_plot2():
        #Get inputs
        the_var = input.LDAS_select()
        the_ubigeo = input.district_select()
        the_offset = input.offset_select()
        #Create output
        the_plot = line_plot(the_var,the_ubigeo,the_offset)
        return the_plot
    #Function to populate the basemap
    @render.plot(alt="A plot")
    def line_plot3():
        #Get inputs
        the_var = input.LDAS_select()
        the_ubigeo = input.district_select()
        the_offset = input.offset_select()
        #Create output
        the_plot = line_plot(the_var,the_ubigeo,the_offset)
        return the_plot
    @render_widget
    def create_basemap():
        #Create the basemap
        basemap = ipyleaflet.Map(center = (-4.2325,-74.2179), 
                max_zoom=8,
                min_zoom=6,
                zoom_control=True,
                zoom=4,
                scroll_wheel_zoom=True,
                dragging=True,
                #layout=Layout(width="60%",height='600px')
                )
        #Get inputs
        the_var = input.LDAS_select()
        the_offset = input.offset_select()
        #Create output
        the_map = plot_correlations(the_var,the_offset,basemap)
        return the_map

#%% Create the app
app = App(app_ui, server, debug=True)