# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 09:06:32 2024

@author: nelen
"""
import numpy as np
# import np.random
from mesa import Agent
from shapely.geometry import Point
from shapely import contains_xy

# Import functions from functions.py
from functions import generate_random_location_within_map_domain, get_flood_depth, calculate_basic_flood_damage, floodplain_multipolygon
import networkx as nx
from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import geopandas as gpd
import rasterio as rs
import matplotlib.pyplot as plt
# Import the agent class(es) from agents.py
from agents import Households
from agents import Government

# Import functions from functions.py
from functions import get_flood_map_data, calculate_basic_flood_damage
from functions import map_domain_gdf, floodplain_gdf

from model import AdaptationModel

m1 = AdaptationModel()

for i in range(1, 8):
    print('WE ARE NOW AT STEP:', i)
    m1.step()
    
#agent_data = m1.datacollector.get_agent_vars_dataframe()
model_data = m1.datacollector.get_model_vars_dataframe()

#agent_data.head()
#model_data.head()

