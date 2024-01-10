# Importing necessary libraries
import numpy as np
import random
from mesa import Agent
from shapely.geometry import Point
from shapely import contains_xy

# Import functions from functions.py
from functions import generate_random_location_within_map_domain, get_flood_depth, calculate_basic_flood_damage, floodplain_multipolygon


# Define the Households agent class
class Households(Agent):
    """
    An agent representing a household in the model.
    Each household has a flood depth attribute which is randomly assigned for demonstration purposes.
    In a real scenario, this would be based on actual geographical data or more complex logic.
    """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_adapted = False  # Initial adaptation status set to False
        
        self.background = random.random()
        self.threat_appraisal = random.random()
        self.coping_appraisal = random.random()
        self.climate_related_beliefs = random.random()
        self.preceding_flood_engagement = random.random()
        self.external_influence = random.random()
      
        self.budget = random.randint(1000, 7000) #maybe two additional model parameters
        
        #{1: Not Implemented, 2:Implementing, 3: Implemented}
        
        self.dry_proofing = 1
        self.wet_proofing = 1
        self.elevation = 1
        
        self.prior_hazard_experience = 0 #cumulative sum of previous financial losses due to flood
        
        # self.protection_level -> maybe add later
        
        # self.damaged -> add later
        
        self.detached = random.choice([0, 1]) # 0 = not detached, 1 = detached

        # getting flood map values
        # Get a random location on the map
        loc_x, loc_y = generate_random_location_within_map_domain()
        self.location = Point(loc_x, loc_y)

        # Check whether the location is within floodplain
        self.in_floodplain = False
        if contains_xy(geom=floodplain_multipolygon, x=self.location.x, y=self.location.y):
            self.in_floodplain = True

        # Get the estimated flood depth at those coordinates. 
        # the estimated flood depth is calculated based on the flood map (i.e., past data) so this is not the actual flood depth
        # Flood depth can be negative if the location is at a high elevation
        self.flood_depth_estimated = get_flood_depth(corresponding_map=model.flood_map, location=self.location, band=model.band_flood_img)
        # handle negative values of flood depth
        if self.flood_depth_estimated < 0:
            self.flood_depth_estimated = 0
        
        # calculate the estimated flood damage given the estimated flood depth. Flood damage is a factor between 0 and 1
        self.flood_damage_estimated = calculate_basic_flood_damage(flood_depth=self.flood_depth_estimated)

        # Add an attribute for the actual flood depth. This is set to zero at the beginning of the simulation since there is not flood yet
        # and will update its value when there is a shock (i.e., actual flood). Shock happens at some point during the simulation
        self.flood_depth_actual = 0
        
        #calculate the actual flood damage given the actual flood depth. Flood damage is a factor between 0 and 1
        self.flood_damage_actual = calculate_basic_flood_damage(flood_depth=self.flood_depth_actual)
    
    def determine_AM(self):
        self.AM = np.mean([self.background, self.threat_appraisal, 
                        self.coping_appraisal, self.climate_related_beliefs, 
                        self.preceding_flood_engagement, self.external_influence])
        return self.AM
    
    def check_elevation(self):
        if self.detached == 1: #check if this household is detached
            if self.elevation == 1:
                #Agent can choose to elevate house in this timestep
                # DETERMINE COST_ELEVATION
                if self.budget >= self.model.elevation_cost:
                        print("Agent has sufficient budget for elevation, starts implementing here, budget=", self.budget)
                        self.elevation = 2
                        self.budget -= self.model.elevation_cost
                        self.elevation_time_counter = 1 #this tick counts as one unit of time for implementing elevation
                
                
            elif self.elevation == 2:
                #Agent is implementing elevation
                print('this agent is implementing elevation', self.elevation_time_counter)
                if self.elevation_time_counter >= self.model.elevation_time:
                    self.elevation = 3
                else:
                    #Implementation time has not been reached, advance counter by 1
                    self.elevation_time_counter += 1
                #Check if implementation time has been reached during this step
            
            else:
                # Agent has implemented elevation as a measure already
                print("Elevation implementation complete")
                

    # def check_wet_proofing(self):
    #     # check whether wet_proofing and elevation are not already implemented
    #     if not self.wet_proofing and not self.check_elevation():
    #         #DETERMINE COST_WET_PROOFING
    #         if self.budget >= cost_wet_proofing:
    #             self.wet_proofing = True
    #             self.budget -= cost_wet_proofing
    #             return True
    #     return False
            
    # def check_dry_proofing(self):
    #     # check whether there are no measures implemented
    #     if not self.dry_proofing and not self.check_elevation() and not self.check_wet_proofing():
    #         #DETERMINE COST_DRY_PROOFING
    #         if self.budget >= cost_dry_proofing:
    #             self.dry_proofing = True
    #             self.budget -= cost_dry_proofing
    #             return True
    #     return False
        
    def choose_measure(self):
        # DETERMINE THRESHOLD
        # intention_action_gap = 0.3 #implement as model parameter
        threshold = 1-self.model.intention_action_gap
        if self.AM >= threshold:

            self.check_elevation()
            # self.check_wet_proofing()
            # self.check_dry_proofing()
              
    # Function to count friends who can be influencial.
    def count_neighbors(self, radius):
        """Count the number of neighbors within a given radius (number of edges away). This is social relation and not spatial"""
        neighbors = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)
        return len(neighbors)

    def step(self):
        self.determine_AM()
        self.choose_measure()
        
        # Logic for adaptation based on estimated flood damage and a random chance.
        # These conditions are examples and should be refined for real-world applications.
        if self.flood_damage_estimated > 0.15 and random.random() < 0.2:
            self.is_adapted = True  # Agent adapts to flooding
        
# Define the Government agent class
class Government(Agent):
    """
    A government agent that currently doesn't perform any actions.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        # The government agent doesn't perform any actions.
        pass

# More agent classes can be added here, e.g. for insurance agents.
