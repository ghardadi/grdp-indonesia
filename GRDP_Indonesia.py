# -*- coding: utf-8 -*-
"""
Created on Thu Mar 25 23:25:54 2021

@author: ghardadi
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px
# import plotly
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from GRDP_Parser import GRDP_Parser

# Initial parameters for implementing GRDP_Parser class
file = 'Produk Domestik Regional Bruto Kabupaten_Kota di Indonesia 2014-2018-converted.xls'
nom_sheets = ['Table ' + str(i) for i in range(9, 43)]
pcp_sheets = ['Table ' + str(i) for i in range(145, 179)] 
years = [2014, 2015, 2016, 2017, 2018]

# Collecting data of GRDP and GRDP per capita
GRDP_nom = GRDP_Parser(file, nom_sheets, years)
GRDP_dta = GRDP_nom.data()

GRDP_pcp = GRDP_Parser(file, pcp_sheets, years)
GRDPpc_dta = GRDP_pcp.data()

# Merging both datasets
df_GRDP = pd.concat([GRDP_dta, GRDPpc_dta.iloc[:,1:]], axis=1)

grdp_list = ['GRDP_' + str(i) for i in years]
grdppc_list = ['GRDPpc_' + str(i) for i in years]
col_names = ['Kabupaten'] + grdp_list + grdppc_list

df_GRDP.columns = col_names

# Collecting geo-dataframe of Indonesian Municipalities from GADM
df_geo = gpd.read_file('gadm36_IDN_2.shp')

# Cleaning a pair of municipalities with identical names or different spellings
df_geo.loc[df_geo.HASC_2 == 'ID.JR.BA', 'NAME_2'] = "Kota Banjar"
df_geo.loc[df_geo.NAME_2 == 'Bireuen', 'NAME_2'] = "Bireun"
df_geo.loc[df_geo.NAME_2 == 'Tanjung Jabung B', 'NAME_2'] = "Tanjung Jabung Barat"
df_geo.loc[df_geo.NAME_2 == 'Tanjung Jabung T', 'NAME_2'] = "Tanjung Jabung Timur"
df_geo.loc[df_geo.NAME_2 == 'Kepulauan Anambas', 'NAME_2'] = "Kep. Anambas"
df_geo.loc[df_geo.NAME_2 == 'Padangsidimpuan', 'NAME_2'] = "Kota Padang Sidempuan"
df_geo.loc[df_geo.NAME_2 == 'Pakpak Barat', 'NAME_2'] = "Pakpak Bharat"

# Merging geo-dataframe and GRDP data
df_join = df_geo.merge(df_GRDP, how='inner', left_on="NAME_2", right_on="Kabupaten")

# Building function to strip spaces, dashes, and capitalizations
def strip(string):
    return string.replace(' ', '').replace('-', '').lower()

# Collect municipalities in stripped format
stripped = [strip(i) for i in list(df_GRDP['Kabupaten'])]

# Cleaning data
for i in df_geo['NAME_2']:
    if i not in list(df_GRDP['Kabupaten']):
        kota = df_geo['NAME_2']==i
        j = 'Kota ' + i
        if j not in list(df_GRDP['Kabupaten']):
            if strip(i) not in stripped:
                if strip(j) not in stripped:
                    pass # print('Not identified: ' + i)
                else:
                    # Concatenate with GRDP data which name is 'Kota ... ', 
                    # with slight name differences of space or dash
                    a = stripped.index(strip(j))
                    new_row = pd.concat([df_geo[kota].reset_index(drop=True),
                                  df_GRDP[df_GRDP['Kabupaten'] ==
                                          list(df_GRDP['Kabupaten'])[a]]], axis=1)
                    df_join = pd.concat([df_join, new_row], axis=0, ignore_index=True)
            else:
                # Concatenate with GRDP data with slight name differences of space or dash
                a = stripped.index(strip(i))
                new_row = pd.concat([df_geo[kota].reset_index(drop=True),
                                  df_GRDP[df_GRDP['Kabupaten'] ==
                                          list(df_GRDP['Kabupaten'])[a]]], axis=1)
                df_join = pd.concat([df_join, new_row], axis=0, ignore_index=True)
        else:
            # Concatenate with GRDP data which name is 'Kota ... '
            new_row = pd.concat([df_geo[kota].reset_index(drop=True),
                                 df_GRDP[df_GRDP['Kabupaten']==j]], axis=1)
            df_join = pd.concat([df_join, new_row], axis=0, ignore_index=True)
    else:
        pass
        
for i in range(2014, 2019):
    grdp = df_join['GRDP_' + str(i)]
    grdp_pc = df_join['GRDPpc_' + str(i)]
    df_join['Populasi_' + str(i)] = round(grdp / grdp_pc * 1e6)

# # The commands below is used to save the GADM geo-information into a JSON file

# kab_list = list(range(497))

# new_kabupaten = gpd.GeoSeries([df_join['geometry'][i] for i in kab_list]).__geo_interface__

# for i in kab_list:
#     new_kabupaten['features'][i]['properties'] = {'GID_0': df_join['GID_0'][i], 'NAME_0': df_join['NAME_0'][i],
#       'GID_1': df_join['GID_1'][i], 'NAME_1': df_join['NAME_1'][i], 'NL_NAME_1': df_join['NL_NAME_1'][i],
#       'GID_2': df_join['GID_2'][i], 'NAME_2': df_join['NAME_2'][i], 'NL_NAME_2': df_join['NL_NAME_2'][i],
#       'VARNAME_2': df_join['VARNAME_2'][i], 'HASC_2': df_join['HASC_2'][i], 
#       'CC_2': df_join['CC_2'][i], 'TYPE_2': df_join['TYPE_2'][i]}
    
# with open('IDN_level2.json', 'w') as json_file:
#     json.dump(new_kabupaten, json_file)
 
# # In this work, a simplified JSON file is used
f = open('IDN_level2_simplified.json')
kabupaten = json.load(f)
f.close()


# An example to execute choropleth map
fig = px.choropleth_mapbox(df_join, geojson=kabupaten, locations='NAME_2', featureidkey="properties.NAME_2",
                            color=round(np.log10(df_join['GRDPpc_2018']),2),
                            hover_name='NAME_2',
                            hover_data=['NAME_1', 'GRDPpc_2018'],
                            color_continuous_scale=px.colors.diverging.BrBG,
                            range_color=(min(np.log10(df_join['GRDPpc_2018'])), max(np.log10(df_join['GRDPpc_2018']))),
                            mapbox_style="carto-positron",
                            zoom=3.6, center = {"lat": 0, "lon": 118}, 
                            opacity=0.8,
                            labels={'NAME_2':'Kota/Kabupaten', 'NAME_1':'Provinsi',
                                    'color':'Log Scale', 'GRDPpc_2018': 'GRDPpc 2018 (K IDR)'})

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# fig.show()

# Deploying application
title = 'GRDP per Kapita Kabupaten di Indonesia Tahun 2018'

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1(id='Title', children=title,
            style={"font": "36px Arial, sans-serif", 'text-align':'center'}),
    # dcc.Markdown(
    #     title, id='Title',
    #     style={"font": "28px Arial, sans-serif", "margin-block": "0",
    #           'display': 'block', 'align-items': 'center', 'justify-content': 'center'}),
    html.Div([dcc.RadioItems(id='Parameter',
        options=[
        {'label': 'Population', 'value': 'Populasi'},
        {'label': 'GRDP', 'value': 'GRDP'},
        {'label': 'GRDP per kapita', 'value': 'GRDPpc'}],
        value='GRDPpc', labelStyle={'display': 'inline-block'},
        inputStyle={"margin-left": "25px","margin-right": "15px"},
        style={"margin-bottom": "0px", "font": "24px Arial, sans-serif",
              'display': 'flex', 'align-items': 'center', 'justify-content': 'left'}),
    dcc.Markdown('Tahun', style={"margin-bottom": "0px", "font": "24px Arial, sans-serif",
                                 'display': 'flex', 'align-items': 'center',
                                 'justify-content': 'center'}),
    html.Div([dcc.Slider(id='Year', min=2014, max=2018, step=1,
    marks={
        2014: {'label':'2014', 'style':{"font": "18px Arial, sans-serif"}},
        2015: {'label':'2015', 'style':{"font": "18px Arial, sans-serif"}},
        2016: {'label':'2016', 'style':{"font": "18px Arial, sans-serif"}},
        2017: {'label':'2017', 'style':{"font": "18px Arial, sans-serif"}},
        2018: {'label':'2018', 'style':{"font": "18px Arial, sans-serif"}}},
    value=2018)], style = {"display": "grid", "grid-template-columns": "100%",
                           "padding": "32px 24px 0px 24px"}),
    dcc.Markdown()],
    style={"margin-bottom": "14px", "display": "grid", "grid-template-columns": "41% 4% 53% 2%"}),
    dcc.Graph(id='GRDP Figure', figure=fig,
              style={"margin-top": "0px", "margin-bottom": "8px"}),
    dcc.Markdown('Created by Gilang Hardadi', id='Creator', 
        style={"font": "16px Arial, sans-serif",
              'display': 'flex'})
    ])

@app.callback(
    Output('Title', 'children'),
    Output('GRDP Figure', 'figure'),
    Input('Parameter', 'value'),
    Input('Year', 'value'))

def update_graph(par, year):
    
    select = par + '_' + str(year)
    unit, title = '', ''
    
    if par == 'GRDP':
        unit = ' (MM IDR)'
        title = 'GRDP Kabupaten di Indonesia Tahun ' + str(year)
    elif par == 'GRDPpc':
        unit = ' (K IDR)'
        title = 'GRDP per Kapita Kabupaten di Indonesia Tahun ' + str(year)
    else:
        title = 'Populasi Kabupaten di Indonesia Tahun ' + str(year)
    
    fig = px.choropleth_mapbox(df_join, geojson=kabupaten, locations='NAME_2', featureidkey="properties.NAME_2",
                            color=round(np.log10(df_join[select]),2),
                            hover_name='NAME_2',
                            hover_data=['NAME_1', select],
                            color_continuous_scale=px.colors.diverging.BrBG,
                            range_color=(min(np.log10(df_join[select])), max(np.log10(df_join[select]))),
                            mapbox_style="carto-positron",
                            zoom=3.6, center = {"lat": 0, "lon": 118}, 
                            opacity=0.8,
                            labels={'NAME_2':'Kota/Kabupaten', 'NAME_1':'Provinsi',
                                    'color':'Log Scale', select: par + ' ' + str(year) + unit})

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return title, fig

if __name__ == '__main__':
    app.run_server(debug=True)