# Importing necessary libraries
import numpy as np
import random
from mesa import Agent
from shapely.geometry import Point
from shapely import contains_xy
#import RBB: 
from rbb import RBBGovernment
from rbb import OrganizationInstrument
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
        
        self.undergone_measures = [0 for i in range(8)] # history of undergone measures during last eight steps
        
        self.financial_loss = 0 #cumulative sum of previous financial losses due to flood
        
        self.savings_income = random.randint(300, 700) #Assumption: Every agent gets a standard
        self.detached = random.choice([0, 1]) # 0 = not detached, 1 = detached

        # getting flood map values
        # Get a random location on the map
        loc_x, loc_y = generate_random_location_within_map_domain()
        self.location = Point(loc_x, loc_y)

        # Check whether the location is within floodplain
        self.in_floodplain = False
        if contains_xy(geom=floodplain_multipolygon, x=self.location.x, y=self.location.y):
            self.in_floodplain = True
        self.is_protected = False    
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
        #self.flood_depth_actual = 0
        
        #calculate the actual flood damage given the actual flood depth. Flood damage is a factor between 0 and 1
        self.flood_damage_actual = 0  #calculate_basic_flood_damage(flood_depth=self.flood_depth_actual)
        self.AM = self.determine_AM()
    
    def determine_AM(self):
        self.AM = np.mean([self.background, self.threat_appraisal, 
                        self.coping_appraisal, self.climate_related_beliefs, 
                        self.preceding_flood_engagement, self.external_influence])
        return self.AM
    
    def check_elevation(self):
        if self.detached == 1: #check if this household is detached
            if self.elevation == 1:
                #Agent can choose to elevate house in this timestep
                if self.budget >= self.model.elevation_cost:
                    # print("Agent has sufficient budget for elevation, starts implementing here, budget=", self.budget)
                    if random.random() >= 1 - self.model.intention_action_gap:
                        # print('Intention and budget high enough for elevation')
                        self.elevation = 2
                        self.budget -= self.model.elevation_cost
                        self.elevation_time_counter = 1 #this tick counts as one unit of time for implementing elevation
                        self.is_adapted = True
                
            elif self.elevation == 2:
                #Agent is implementing elevation
                #print('this agent is implementing elevation', self.elevation_time_counter)
                if self.elevation_time_counter >= self.model.elevation_time:
                    self.elevation = 3
                    
                else:
                    #Implementation time has not been reached, advance counter by 1
                    self.elevation_time_counter += 1
                #Check if implementation time has been reached during this step
            
            else:
                # Agent has implemented elevation as a measure already
                #print("Elevation implementation complete")
                pass
            
    def check_wet_proofing(self):
        if self.wet_proofing == 1:
            #Agent can choose to implement wet_proofing in this timestep
            if self.budget >= self.model.wet_proofing_cost:
                #print("Agent has sufficient budget for wet_proofing, starts implementing here, budget=", self.budget)
                if random.random() >= 1 - self.model.intention_action_gap:
                    #print('Intention and budget high enough for wet_proofing')
                    # print("Agent has sufficient budget for wet_proofing, starts implementing here, budget=", self.budget)
                    self.wet_proofing = 2
                    self.budget -= self.model.wet_proofing_cost
                    self.wet_proofing_time_counter = 1 #this tick counts as one unit of time for implementing elevation
                    self.is_adapted = True
            
        elif self.wet_proofing == 2:
            #Agent is implementing wet_proofing
            #print('this agent is implementing wet_proofing', self.wet_proofing_time_counter)
            if self.wet_proofing_time_counter >= self.model.wet_proofing_time:
                self.wet_proofing = 3
                
            else:
                #Implementation time has not been reached, advance counter by 1
                self.wet_proofing_time_counter += 1
            #Check if implementation time has been reached during this step
        
        else:
            pass
            # Agent has implemented wet_proofing as a measure already
            #print("Wet_proofing implementation complete")
                
    def check_dry_proofing(self):
        if self.dry_proofing == 1:
            #Agent can choose to implement dry_proofing in this timestep
            if self.budget >= self.model.dry_proofing_cost:
                #print("Agent has sufficient budget for dry_proofing, starts implementing here, budget=", self.budget)
                if random.random() >= 1 - self.model.intention_action_gap:
                    #print('Intention and budget high enough for dry_proofing')
                    self.dry_proofing = 2
                    self.budget -= self.model.dry_proofing_cost
                    self.dry_proofing_time_counter = 1 #this tick counts as one unit of time for implementing elevation
                    self.is_adapted = True
            
        elif self.dry_proofing == 2:
            #Agent is implementing dry_proofing
            #print('this agent is implementing dry_proofing', self.dry_proofing_time_counter)
            if self.dry_proofing_time_counter >= self.model.dry_proofing_time:
                self.dry_proofing = 3
            else:
                #Implementation time has not been reached, advance counter by 1
                self.dry_proofing_time_counter += 1
            #Check if implementation time has been reached during this step
        
        else:
            # Agent has implemented dry_proofing as a measure already
            #print("dry_proofing implementation complete")
            pass
        
    def choose_measure(self):
        # Check if AM is higher than highest threshold possible
        if self.AM >= self.model.high_threshold:
            # Define available measures for highest threshold
            available_measures = ['elevation', 'wet_proofing', 'dry_proofing']
            # Check for all available measures in random order
            while available_measures:
                # Make random choice of available measures
                choice = random.choice(available_measures)
                # Remove measure from available measures
                available_measures.remove(choice)
                
                # Call measure corresponding to choice
                if choice == 'elevation':
                    self.check_elevation()
                elif choice == 'wet_proofing':
                    self.check_wet_proofing()
                else:
                    self.check_dry_proofing()
        
        # Check if AM is higher than medium threshold
        elif self.AM >= self.model.medium_threshold:
            # Define available measures for medium threshold
            available_measures = ['wet_proofing', 'dry_proofing']
            # Check for all available measures in random order
            while available_measures:
                # Make random choice of available measures
                choice = random.choice(available_measures)
                # Remove measure from available measures
                available_measures.remove(choice)
                
                # Call measure corresponding to choice
                if choice == 'wet_proofing':
                    self.check_wet_proofing()
                else:
                    self.check_dry_proofing()
                
        # Check if AM is higher than lowest threshold    
        elif self.AM >= self.model.low_threshold:
            # Only available measure is dry_proofing
            self.check_dry_proofing()
       
    def update_threat_appraisal(self):
        # a household can think it is protected if there is infrastructure. 
        if self.model.infrastructure:
            self.threat_appraisal = random.choice([0.9, 0.95, 1.0]) * self.threat_appraisal
        else:
            self.threat_appraisal = random.choice([1.0, 1.05, 1.1]) * self.threat_appraisal
            
        
    def update_coping_appraisal(self):
        if self.budget >= self.model.upper_budget_threshold:
            self.coping_appraisal = 1.1 * self.coping_appraisal
        elif self.budget <= self.model.lower_budget_threshold:
            self.coping_appraisal = 0.9 * self.coping_appraisal 
       
    def update_preceding_flood_engagement(self):
        flood_recency = 1 - ((self.model.schedule.steps - self.model.last_flood) / 20)
        if np.mean(self.undergone_measures) >= random.random():
            if self.model.last_flood != 0:
                if flood_recency >= random.random():
                    self.preceding_flood_engagement = self.preceding_flood_engagement * 1.1
            else:
                self.preceding_flood_engagement= self.preceding_flood_engagement * 1.05
                
        elif flood_recency >= random.random():
                self.preceding_flood_engagement = self.preceding_flood_engagement * 1.05
        else:
            self.preceding_flood_engagement = 0.9 * self.preceding_flood_engagement
        
    def update_external_influence(self):
        neighbors = self.model.grid.get_neighbors(self.pos)
        #print('neighbors:', neighbors)
        avg_neighbor_AM = np.mean([neighbor.AM for neighbor in neighbors])
        #print('Avg neighbor AM:', avg_neighbor_AM)
        # Calculate the external influence based on the difference between self.AM and neighbors AM
        self.external_influence = self.external_influence * (1+(avg_neighbor_AM-self.AM))
    
    def update_AM(self):
       #print('id:', self.unique_id, 'am:', self.AM)
        self.update_threat_appraisal()
        self.update_coping_appraisal()
        self.update_preceding_flood_engagement()
        self.update_external_influence()
        self.determine_AM()
        #print('id:', self.unique_id, 'am updated:', self.AM)
              
    # # Function to count friends who can be influencial.
    # def count_neighbors(self, radius):
    #     """Count the number of neighbors within a given radius (number of edges away). This is social relation and not spatial"""
    #     neighbors = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)
    #     return len(neighbors)
    
    def check_elevation_protection(self):
        if self.flood_depth_actual <= self.model.elevation_protection:
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.elevation_effectiveness)
        else:
            self.elevation = 1
        return
                
    def check_wet_and_dry_proofing_protection(self):
        if self.flood_depth_actual <= self.model.dry_proofing_protection:
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.dry_proofing_effectiveness) * (1-self.model.wet_proofing_effectiveness)
        elif self.flood_depth_actual <= self.model.wet_proofing_protection:
            self.dry_proofing = 1
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.wet_proofing_effectiveness)
        else:
            self.dry_proofing = 1
            self.wet_proofing = 1
        return
    
    def check_dry_proofing_protection(self):
        if self.flood_depth_actual <= self.model.dry_proofing_protection:
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.dry_proofing_effectiveness)
        else:
            self.dry_proofing = 1
        return
    
    def check_wet_proofing_protection(self):
        if self.flood_depth_actual <= self.model.wet_proofing_protection:
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.wet_proofing_effectiveness)
        else:
            self.wet_proofing = 1
            
        return

    def step(self):
        self.is_adapted = False
        self.determine_AM()
        self.choose_measure()
        self.undergone_measures.pop(0)
        if self.is_adapted:
            self.undergone_measures.append(1)
        else:
            self.undergone_measures.append(0)
        self.update_AM()
        self.budget += self.savings_income
        
        # GIVEN
        # Logic for adaptation based on estimated flood damage and a random chance.
        # These conditions are examples and should be refined for real-world applications.
        # if self.flood_damage_estimated > 0.15 and random.random() < 0.2:
        #     self.is_adapted = True  # Agent adapts to flooding
        
# Define the Government agent class
class Government(Agent, RBBGovernment):#inherit from RBBGovernment)
    """
    A government agent that can make an infrastructural decision.
    """
    def __init__(self, unique_id, model,structure, detector):
        #call the constructors of both parent classes
        Agent.__init__(self, unique_id, model)
        RBBGovernment.__init__(self, structure, detector)
        self.estimated_flood_impact = 3
        self.agenda = False
        self.decision_made = False
        self.decision = None
        self.flood_risk_threshold = 1.5
        self.public_concern_threshold = 0.6
        self.damage_threshold = 0.3
        
    def estimate_impact(self):
        """A government estimates the impact of a potential flood, 
        based on the damage from the previous flood"""
        if self.model.avg_flood_damage >= self.damage_threshold:
            self.estimated_flood_impact = random.randrange(5,10)
        else:
            self.estimated_flood_impact = random.randrange(1,5)
        return self.estimated_flood_impact
        
               
    def make_decision(self, flood_risk, options_list, high, low):
        """Government makes a decision on what kind of tool to deploy"""
        if self.decision_made:
            self.decision.change_status()
            
        else: #if no decision has been made yet
        #First, the topic needs to be on the agenda:
            if self.agenda:#if a topic is on the agenda
        
                if flood_risk >= high:
                    # if the estimated risk is high, government will prioritise avg implementation time
                    lowest_planning = min([option.completion_time for option in options_list])
                    self.decision = [option for option in options_list if option.completion_time == lowest_planning][0]
                elif low<=flood_risk< high:
                    # if the estimated risk is medium, government will prioritise protection level
                    highest_protection = max([option.protection_level for option in options_list])
                    self.decision = [option for option in options_list if option.completion_time == highest_protection][0]
                elif flood_risk < low:
                    lowest_cost = min([option.cost for option in options_list])
                    self.decision = [option for option in options_list if option.completion_time == lowest_cost][0]
                    
                    # if the estimated risk is low, government will prioritise cost 
                    # based on the organisation of the government, the implementation time of the option will change.
                self.decision.impact_planning(self.structure)
                #change the status of the measure to ' implementing'
                self.decision.change_status()
                
                #print('Decision:', self.decision.name)
                #change agenda back to False
                self.change_agenda
                self.decision_made = True
            else:#if the topic was not on the agenda
                #print('Flood measure decision not on agenda')
                self.decision = None
        
        return self.decision
    
    
    def implement_decision(self):
        """Implement the infrastructe in the model"""
        if self.decision_made == True and self.decision.status == 3:
            self.model.infrastructure = True
        else:
            pass
        return 
    
        
    
    def step(self):
        
        self.estimate_impact()
        flood_risk = self.assess_risk(self.model.flood_probability, self.estimated_flood_impact) #take flood probability and flood impact from model
        public_concern = self.take_survey(self.model.avg_public_concern)
        self.put_on_agenda(public_concern,flood_risk)
        self.make_decision(flood_risk, self.model.options_list, high=2.9, low=1.9)
        self.implement_decision()
        

