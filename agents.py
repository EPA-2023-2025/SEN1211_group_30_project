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
        
        while True:
            self.age = np.random.normal(34, 20)
            
            if self.age >= 18: #if age is above 18, exit the loop. Age above 18 is set.
                break
        
        # self.age = random.triangular(18, 70, 34)
    
        education_level = {'low': 0.25, 'middle': 0.5, 'high': 0.75}
        self.education_level = random.choice(list(education_level.values()))
        
        self.budget = 1000
        
        self.self_efficacy = random.random()
        
        self.undergone_adaptation_measures = 0 #binary variable -> 0 = no measures undergone, 1 = measures undergone
        # self.undergone_adaptation_measures = {'dry-proofing': 0, 'wet-proofing': 0, 'elevation': 0} #previous measures taken
        
        self.dry_proofing = False
        self.wet_proofing = False
        self.elevation = False
        
        self.prior_hazard_experience = 0 #cumulative sum of previous financial losses due to flood
        
        self.climate_related_beliefs = random.random() #range between 0 and 1
        # self.climate_related_beliefs = random.choice([0, 1]) -> on or off
        
        self.social_network_influence = random.random()
        
        self.social_media_influence = random.random()
        
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
        # NEEDS TO BE SCALED
        background = self.age * self.education_level
        threat_appraisal = self.flood_damage_estimated
        coping_appraisal = self.budget * self.self_efficacy
        climate_related_beliefs = self.climate_related_beliefs
        preceding_flood_engagement = self.undergone_adaptation_measures * self.prior_hazard_experience
        external_influence = self.social_network_influence * self.social_media_influence
        # ADD WEIGHTS
        self.AM = w_background * background 
                + w_threat_appraisal * threat_appraisal 
                + w_coping_appraisal * coping_appraisal 
                + w_climate_related_beliefs * climate_related_beliefs 
                + w_preceding_flood_engagement * preceding_flood_engagement 
                + w_external_influence * external_influence
        return self.AM
    
    def check_elevation(self):
        # check whether the house is not already elevated
        if not self.elevation:
            # DETERMINE COST_ELEVATION
            if self.budget >= cost_elevation:
                self.elevation = True
                self.budget -= cost_elevation
                return True
        return False

    def check_wet_proofing(self):
        # check whether wet_proofing and elevation are not already implemented
        if not self.wet_proofing and not self.check_elevation():
            #DETERMINE COST_WET_PROOFING
            if self.budget >= cost_wet_proofing:
                self.wet_proofing = True
                self.budget -= cost_wet_proofing
                return True
        return False
            
    def check_dry_proofing(self):
        # check whether there are no measures implemented
        if not self.dry_proofing and not self.check_elevation() and not self.check_wet_proofing():
            #DETERMINE COST_DRY_PROOFING
            if self.budget >= cost_dry_proofing:
                self.dry_proofing = True
                self.budget -= cost_dry_proofing
                return True
        return False
        
    def choose_measure(self):
        # DETERMINE THRESHOLD
        if self.AM >= threshold:
            if self.detached == 1:
                self.check_elevation()
            self.check_wet_proofing()
            self.check_dry_proofing()
              
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
