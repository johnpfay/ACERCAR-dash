# App to interactively view lineplots of LDAS variables and malaria case counts
# This app has three widgets:
# - LDAS variable selector     [Dropdown]
# - District (ubigeo) selector [Dropdown]
# - Offset value               [Slider]

#Import packages
import pandas as pd
import matplotlib 
from pathlib import Path
#from shiny.express import input, render, ui
from shiny import ui, render, App

#Read in LDAS data (long format)
df_LDAS = pd.read_csv(
    Path(__file__).parent / "Peru_LDAS.csv",
    dtype={'ubigeo':'str'},             #Read the ubigeo field as string
    parse_dates=['EpiweekStartDate']    #Read the EpiweekStartDate as datetime
).set_index(['ubigeo','EpiweekStartDate','year','week'])

#Read in surveillance data
df_surveillance = (
    pd.read_csv(
        Path(__file__).parent / "datos_abiertos_vigilancia_malaria_processed.csv",
        dtype={'ubigeo':'str'},             #Read the ubigeo field as string
        parse_dates=['date']                #Read the date field as datetime
    )
    .rename(columns={'ano':'year','semana':'week'})
    .set_index(['ubigeo','date','year','week'])
)

#Create the LDAS variable list 
var_list = df_LDAS.columns.to_list() 
var_list.remove('DataType')
var_list.remove('DataType_max')

#Plot function
def line_plot(the_var, the_ubigeo, the_offset):
    #Create the plot title
    the_title = f"P. Vivax cases & {the_var} for district {the_ubigeo}: {the_offset} weeks offset"

    #Set the start and end times
    start_time = '2010-01-01'
    end_time = '2024-05-01'

    #Subset for the ubigeo and drop the year and week levels
    df_LDAS_subset = (
        df_LDAS
        .loc[(the_ubigeo)]
        .loc[slice(start_time,end_time)]
        .droplevel(['year','week'])
    )

    #Subset the surveillance data for the ubigeo
    df_cases_subset = (
        df_surveillance
        .loc[(the_ubigeo)]
        .loc[slice(start_time,end_time)]
        .droplevel(['year','week'])
    )

    # Compute the lagged variable
    df_LDAS_subset['lagged'] = df_LDAS_subset[the_var].shift(the_offset)

    ## Plot the LDAS variable, split into retrospective and forecast components
    ldas_plot = df_LDAS_subset.query('DataType=="retrospective"')['lagged'].plot(
        ylabel=the_var,color='grey',alpha=0.6,figsize=(15,5),legend=True,title=the_title)
    df_LDAS_subset.query('DataType=="forecast"')['lagged'].plot(ax=ldas_plot,color='red',alpha=0.8,label='Forecast',legend=True)

    #Set the legend
    ldas_plot.legend([the_var],loc='upper left')

    #Create a shared axis for the surveillance data
    shared_axis = ldas_plot.twinx()
    #shared_axis.set_xlim(pd.Timestamp(start_time), pd.Timestamp(end_time))

    #Plot the surveillance data on the same x-axis
    df_cases_subset['p_vivax'].plot(ax=shared_axis,ylabel='Cases',color='blue',label='P. Vivax',legend=True)
    shared_axis.legend(loc='upper right')

    #Set the x-limits
    ldas_plot.set_xlim(pd.Timestamp(start_time), pd.Timestamp(end_time))

##Create app layout
app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.panel_sidebar(   
        #LDAS selector
        ui.input_select(
            id="LDAS_select",
            label="LDAS variable:",
            choices=var_list 
        ),
        #ubigeo selector
        ui.input_select(
            id="district_select",  
            label="District ID:",  
            choices=list(df_LDAS.index.get_level_values(0).unique())
        ),
        #Offset slider
        ui.input_slider("offset_select", "Lag time (weeks)", min=-10, max=10, value=0)
        )
    ),
    ui.panel_main(
        ui.output_plot("line_plot2")
    ),  
)
     
def server(input, output, session):
    @render.plot(alt="A plot")
    def line_plot2():
        #Get inputs
        the_var = input.LDAS_select()
        the_ubigeo = input.district_select()
        the_offset = input.offset_select()
        the_plot = line_plot(the_var,the_ubigeo,the_offset)
        return the_plot

app = App(app_ui, server, debug=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)