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

#should be imported from model:
flood_probability = 0.1
flood_impact = 9 #int [1-10]
public_concern_metric = 1 #public concern metric should be a likert scale like distribution 1-5

#could be defined in initialisation
flood_risk_treshold = 0.3
public_concern_treshold = 3
eng_infra_treshold = 5
nat_infra_treshold = 3
timeframe = 5 #(1-flood_prob) * max_time



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
        
        # history of floods during last 20 steps (5 years)
        #self.prior_harard_experience = [0 for i in range(20)] # to use self.prior_harard_experience / (self.model.schedule.steps / 4)
        
        # self.protection_level -> maybe add later
        
        # self.damaged -> add later
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
        #self.flood_damage_actual = calculate_basic_flood_damage(flood_depth=self.flood_depth_actual)
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
                        self.elevation_time_counter = 0 #initialize time_counter to 0, time_counter will be increased by 1 later in the step function
                        self.is_adapted = True
                
            else:
                # Agent has implemented elevation or is implementing elevation
                print("Elevation cannot be implemented")
            
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
        
        else:
            # Agent has implemented or is implementing wet_proofing as a measure already
            print("Wet_proofing cannot be implemented")
                
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
        
        else:
            # Agent has implemented or is implementing dry_proofing as a measure already
            print("Dry proofing cannot be implemented")
        
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
            
    def update_measure_implementation(self):
        if self.elevation == 2:
            #Agent is implementing elevation
                if self.elevation_time_counter >= self.model.elevation_time:
                    self.elevation = 3
                    
                else:
                    #Implementation time has not been reached, advance counter by 1
                    self.elevation_time_counter += 1
                    
        if self.wet_proofing == 2:
            #Agent is implementing wet_proofing
                if self.wet_proofing_time_counter >= self.model.wet_proofing_time:
                    self.wet_proofing = 3
                    
                else:
                    #Implementation time has not been reached, advance counter by 1
                    self.wet_proofing_time_counter += 1
                    
        if self.dry_proofing == 2:
            #Agent is implementing dry_proofing
                if self.dry_proofing_time_counter >= self.model.dry_proofing_time:
                    self.dry_proofing = 3
                    
                else:
                    #Implementation time has not been reached, advance counter by 1
                    self.dry_proofing_time_counter += 1
       
    def update_threat_appraisal(self):
        # if self.flood_depth_estimated >= self.model.upper_threat_threshold:
        #     self.threat_appraisal = 1.1 * self.threat_appraisal
        # elif self.flood_depth_estimated <= self.model.lower_threat_threshold:
        #     self.threat_appraisal = 0.9 * self.threat_appraisal
        
        # Needs to be dependent on government measures
        if self.flood_depth_estimated >= random.uniform(0, 10):
            #estimated flood damage kan 
            self.threat_appraisal = 1.1 * self.threat_appraisal
        else:
            self.threat_appraisal = 0.9 * self.threat_appraisal
        
    def update_coping_appraisal(self):
        if self.budget >= self.model.upper_budget_threshold:
            self.coping_appraisal = 1.1 * self.coping_appraisal
        elif self.budget <= self.model.lower_budget_threshold:
            self.coping_appraisal = 0.9 * self.coping_appraisal 
        # if self.budget >= random.random(1000,10000):
        #     self.coping_appraisal = 1.1 * self.coping_appraisal
        # else:
        #     self.coping_appraisal = 0.9 * self.coping_appraisal
       
    def update_preceding_flood_engagement(self):
        flood_recency = 1 - ((self.model.schedule.steps - self.model.last_flood) / 20)
        if np.mean(self.undergone_measures) >= random.random():
            # factor = sum(self.prior_hazard_experience) / (self.model.schedule.steps/4)
            # if self.prior_hazard_experience >= random.random():
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
        print('id:', self.unique_id, 'am:', self.AM)
        self.update_threat_appraisal()
        self.update_coping_appraisal()
        self.update_preceding_flood_engagement()
        self.update_external_influence()
        self.determine_AM()
        print('id:', self.unique_id, 'am updated:', self.AM)
              
    # Function to count friends who can be influencial.
    # def count_neighbors(self, radius):
    #     """Count the number of neighbors within a given radius (number of edges away). This is social relation and not spatial"""
    #     neighbors = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)
    #     return len(neighbors)

    def step(self):
        self.is_adapted = False
        self.determine_AM()
        self.choose_measure()
        self.update_measure_implementation()
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
    def __init__(self, unique_id, model, budget, structure, detector):
        #call the constructors of both parent classes
        Agent.__init__(self, unique_id, model)
        RBBGovernment.__init__(self, budget, structure, detector)
        self.time_gov_proc = self.estimate_planning()
        self.agenda = False
        
    def make_decision(self, timeframe, eng_infra_treshold, nat_infra_treshold):
        """Government makes a decision on what kind of tool to deploy"""
        #the tresholds are based on the idea that a government knows beforehand that a long term infrastructural project needs at least a certain amount of available budget, same for short term infrastructural projects. 
        
        if self.agenda: #if a topic is on the agenda
            if self.time_gov_proc <= timeframe: #if the estimated timeframe is lower or equal to length of government procedures
                if self.budget >= eng_infra_treshold: #if the budget is larger or equal to long term infrastructure budget
                 #add political influence here: are people against engineered projects? Then still choose nature based infrastructure
                    #ik heb het nu zo gedaan maar eigenlijk wil ik van te voren al twee objecten maken, EngineeredInfra en NatureBasedInfra, 
                    # en deze objecten vervolgens aanpassen nadat een beslissing is gemaakt. Voornamelijk op de attribute 'status'
                    decision = OrganizationInstrument(name = 'engineered_infra', protection_level = 9) #engineered infrastructure like levees and storm surge barriers
                    print('Decision: ', decision.name)
                    self.change_agenda()                 
                elif self.budget > nat_infra_treshold:
                    decision = OrganizationInstrument(name = 'nature_based_infra', protection_level = 5) #nature based infrastructure like dunes and wetlands
                    print('Decision: ', decision.name)
                    self.change_agenda()          
                else:
                    decision = OrganizationInstrument(name = 'no_infra') #no infra
                    print('Decision: ', decision.name)
                    self.change_agenda()
        else:#if the duration of government procedures takes longer than the estimated timeframe:
            print('Flood measure decision not on agenda')

        return decision
    
    def step(self):
        RBBGovernment.step(self)
        #if a decision has been made in the previous step, this doesnt have to happen anymore
        flood_risk = self.assess_risk(flood_probability, flood_impact) #take flood probability and flood impact from model
        public_concern = self.take_survey(public_concern_metric)
        self.put_on_agenda(flood_risk, public_concern, flood_risk_treshold, public_concern_treshold)
        self.make_decision(timeframe, eng_infra_treshold, nat_infra_treshold)
        

