# ACERCAR Dash

This is the "official" repository for the ACERCAR Dashboard - a work in progress by John Fay. 

Summer 2024

## Conda Recipe

```
conda create --name shinyserver_01 python=3.9 -y
activate shinyserver_01
conda install -c esri geopandas ipyleaflet matplotlib -y
pip install shinywidgets
pip install shinylive
```

