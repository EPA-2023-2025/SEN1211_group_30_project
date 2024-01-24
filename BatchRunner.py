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
from mesa import batch_run
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

params = {"seed": None,
          "number_of_households":25,
          "flood_map_choice": 'harvey',
          "network": ["erdos_renyi", "barabasi_albert", "watts_strogatz"],
          "probability_of_network_connection": 0.4,
          "number_of_edges" : 3,"number_of_nearest_neighbours" : 5, "flood_probability" : 0.4,"intention_action_gap" : 0.3,"low_threshold" : 0.6,"medium_threshold" : 0.7,"high_threshold" : 0.8,"upper_budget_threshold" : 7000,"lower_budget_threshold" : 3000,
          "elevation_time" : 4,
          "elevation_cost" : 5000,
          "elevation_protection" : 0.3,
          "elevation_effectiveness" : 1,
          "wet_proofing_time" : 2,
          "wet_proofing_cost" : 3000,
          "wet_proofing_effectiveness" : 0.4,
          "dry_proofing_time" : 1,
          "dry_proofing_cost" : 1500,
          "dry_proofing_protection" : 1,
          "dry_proofing_effectiveness" : 0.85,
          "max_damage_costs" : 5000}

results = batch_run(
    AdaptationModel,
    parameters=params,
    iterations=5,
    max_steps=5,
    number_processes=1,
    data_collection_period=1,
    display_progress=True,
)


