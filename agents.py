# Importing necessary libraries
import numpy as np
import random
from mesa import Agent
from shapely.geometry import Point
from shapely import contains_xy
#import the government agent from the RBB and organizational measures:
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
    #initialize agent attributes
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_adapted = False  # Initial adaptation status set to False
        self.is_adapted_cumulatief = False

        # attributes related to Adaptation Motivation which is dervied from Protection Motivation Theory
        self.background = random.random()
        self.threat_appraisal = random.random()
        self.coping_appraisal = random.random()
        self.climate_related_beliefs = random.random()
        self.preceding_flood_engagement = random.random()
        self.external_influence = random.random()

        # An initial budget from which the agent can spend money
        self.budget = random.randint(1000, 7000)

        #Status for household measures with the following meaning
        #{1: Not Implemented, 2:Implementing, 3: Implemented}
        
        self.dry_proofing = 1
        self.wet_proofing = 1
        self.elevation = 1
        
        self.undergone_measures = [0 for i in range(8)] # history/memory of undergone measures during last eight steps, initialised as list of eight zeros
        
        self.financial_loss = 0 #cumulative sum of previous financial losses due to flood
        
        self.savings_income = random.randint(300, 700) #Assumption: Every agent gets a standard
        self.detached = random.choice([0, 1]) # #type of housing => 0 = not detached, 1 = detached

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
        self.flood_depth_actual = 0
        
        #calculate the actual flood damage given the actual flood depth. Flood damage is a factor between 0 and 1
        self.flood_damage_actual = 0  #calculate_basic_flood_damage(flood_depth=self.flood_depth_actual)
        self.AM = self.determine_AM()

    # calculate the adaptation motivation (AM) with the attributes that are described by Protection Motivation Theory
    # by taking the average of the attributes
    def determine_AM(self):
        self.AM = np.mean([self.background, self.threat_appraisal, 
                        self.coping_appraisal, self.climate_related_beliefs, 
                        self.preceding_flood_engagement, self.external_influence])
        # the AM has to be between the range 0 and 1
        if self.AM > 1:
            self.AM = 1
        elif self.AM < 0:
            self.AM = 0

        return self.AM
    
    def check_elevation(self):
        if self.detached == 1: #check if this household has detached detached housing type
            if self.elevation == 1: #if the agent has not implemented elevation
                #Agent can choose to elevate house in this timestep
                if self.budget >= self.model.elevation_cost:
                    # agent has sufficient budget to implement elevation
                    if random.random() >= 1 - self.model.intention_action_gap:
                        #If the the probability is larger than or equal to the probability of an action following from an intention
                        self.elevation = 2 #Implementing elevation as a measure
                        self.budget -= self.model.elevation_cost #Reduce the costs of elevation from the agent's budget
                        self.elevation_time_counter = 1 #this tick counts as one unit of time for implementing elevation
                        self.is_adapted = True #The agent is adapted
                        self.is_adapted_cumulatief = True
                
            elif self.elevation == 2:
                #Agent is still implementing elevation
                if self.elevation_time_counter >= self.model.elevation_time:
                    self.elevation = 3
                    
                else:
                    #Implementation time has not been reached, advance counter by 1
                    self.elevation_time_counter += 1

                #Check if implementation time has been reached during this step
            else:
                # Agent has implemented elevation as a measure already. Continue
                pass

    # Checks if agent has implemented wet-proofing as a measure
    def check_wet_proofing(self):
        # does not need to check if housing is detached, since this measure can be implemented anyways.
        if self.wet_proofing == 1: #if wet proofing has not been implemented yet
            #Agent can choose to implement wet_proofing in this timestep
            if self.budget >= self.model.wet_proofing_cost:
                if random.random() >= 1 - self.model.intention_action_gap:
                    # Intention and budget are high enough for wet-proofing
                    self.wet_proofing = 2
                    self.budget -= self.model.wet_proofing_cost
                    self.wet_proofing_time_counter = 1 #this tick counts as one unit of time for implementing elevation
                    self.is_adapted = True
                    self.is_adapted_cumulatief = True
            
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

    #check if agent can implement dry-proofing as a measure
    def check_dry_proofing(self):
        if self.dry_proofing == 1:
            #Agent can choose to implement dry_proofing in this timestep
            if self.budget >= self.model.dry_proofing_cost:

                if random.random() >= 1 - self.model.intention_action_gap:
                    #Intention and budget high enough for dry_proofing
                    self.dry_proofing = 2 #Update status for this measure to: Implementing
                    self.budget -= self.model.dry_proofing_cost #Adjust budget according to cost of the measure
                    self.dry_proofing_time_counter = 1 #this tick counts as one unit of time for implementing elevation
                    self.is_adapted = True
                    self.is_adapted_cumulatief = True
            
        elif self.dry_proofing == 2:
            #Agent is still implementing dry_proofing
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


    #Update Adaptation motivation parameters
    def update_threat_appraisal(self):
        # update threat_appraisal when flood has occurred
        if self.model.flood:
            if self.flood_depth_actual >= 6: # if the actual flood depth is higher than 6 meters
                self.threat_appraisal = random.uniform(0.8, 1.0) #the threat appraisal is a random float between 0.8 and 1, which could be considered as high
            elif 2 < self.flood_depth_actual < 6: # if the actual flood depth is lower than 6 meters but still higher than 2 meters,
                self.threat_appraisal = random.uniform(0.4, 0.8) #the threat appraisal is a random float between 0.4 and 0.8, which could be considered as a medium threat
            else:
                self.threat_appraisal = random.uniform(0.2, 0.4) # the flood is lower than 2 meters, threat appraisal is a random low float
        else:
            self.threat_appraisal -= 0.01 #Decay for the threat appraisal if no flood occurs
            
        if self.threat_appraisal < 0: #threat appraisal can't be lower than 0
            self.threat_appraisal = 0
            
        
    def update_coping_appraisal(self):
        #coping appraisal is related to the budget of a household and its abillity to implement measures
        if self.budget >= self.model.upper_budget_threshold: #Compare the budget to a high threshold
            self.coping_appraisal = 1.1 * self.coping_appraisal #increase the coping appraisal
        elif self.budget <= self.model.lower_budget_threshold: #compare the budget to a low threshold
            self.coping_appraisal = 0.9 * self.coping_appraisal #lower the coping appraisal

        if self.coping_appraisal > 1: #coping appraisal cant be higher than 1
            self.coping_appraisal = 1

    def update_preceding_flood_engagement(self):
        #preceeding floog engagement is related to the measures a household has undergone, and how recent the flood has occurred.
        # the agent has a memory of eight steps and each time it implements a measure, it adds a 1 to this list. The mean is then used to see if enough measures have been implementend
        if np.mean(self.undergone_measures) >= random.random():
            if self.model.last_flood != 0: #if no flood has occurred at all
                if self.model.flood_recency >= random.random(): # if the flood is recent
                    self.preceding_flood_engagement = self.preceding_flood_engagement * 1.1 #if it is very recent and measures have been taken, increase the PFE factor by 10%
            else:
                self.preceding_flood_engagement= self.preceding_flood_engagement * 1.05 # if the flood is not recent enough, increase the PFE factor by 5%, because measures have been taken
                
        elif self.model.flood_recency >= random.random():
                self.preceding_flood_engagement = self.preceding_flood_engagement * 1.05 #Update PFE factor by 5% if the age, but no measures have been taken
        else:
            self.preceding_flood_engagement = 0.9 * self.preceding_flood_engagement #Not enough measures taken and flood is not recent/not occurred

    def update_external_influence(self):
        neighbors = self.model.grid.get_neighbors(self.pos) #get the agents neighbor from social network

        avg_neighbor_AM = np.mean([neighbor.AM for neighbor in neighbors]) #take the average adaptation motivation from agents

        # Calculate the external influence based on the difference between self.AM and neighbors AM
        if self.AM < avg_neighbor_AM:
            self.external_influence = self.external_influence * 1.1 #increase your AM if neighbors have higher AM, by 10%
        else:
            self.external_influence = self.external_influence * 0.9 #External influence of the agent is lowered by 10%
    
    def update_AM(self):
       #update all Adaptation Motivation factors
        self.update_threat_appraisal()
        self.update_coping_appraisal()
        self.update_preceding_flood_engagement()
        self.update_external_influence()

       #after updating agent parameters, calcute the adaptation motivation
        self.determine_AM()

    #check if elevation protects from the flood depth
    def check_elevation_protection(self):
        if self.flood_depth_actual <= self.model.elevation_protection: #if flood depth is lower than the protection level of elevation
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.elevation_effectiveness) # the flood damage is reduced by the effectiveness of elevation
        else:
            self.elevation = 1 #elevation does not protect fully, thus this measure is destroyed by the flood damage
        return
                
    def check_wet_and_dry_proofing_protection(self):
        if self.flood_depth_actual <= self.model.dry_proofing_protection: #if flood depth is lower than the protection level of dry proofing
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.dry_proofing_effectiveness) * (1-self.model.wet_proofing_effectiveness) # the flood damage is reduced by the effectiveness of both dry and wet proofing
        elif self.flood_depth_actual <= self.model.wet_proofing_protection: #if flood depth is lower than the protection level of wet proofing
            self.dry_proofing = 1 #dry proofing was not effective, thus it is destroyed by the damage.
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.wet_proofing_effectiveness) # the flood damage is reduced by the effectiveness of wet proofing
        else: #both dry and wet proofing together were not able to protect against the damage, both are destroyed
            self.dry_proofing = 1
            self.wet_proofing = 1
        return
    
    def check_dry_proofing_protection(self):
        if self.flood_depth_actual <= self.model.dry_proofing_protection: #if flood depth is lower than the protection level of dry proofing
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.dry_proofing_effectiveness) #dry proofing is effective
        else:
            self.dry_proofing = 1 #dry proofing was not effective, it is destroyed by the flood damage
        return
    
    def check_wet_proofing_protection(self):
        if self.flood_depth_actual <= self.model.wet_proofing_protection: #if flood depth is lower than the protection level of wet proofing
            self.flood_damage_actual = self.flood_damage_actual * (1-self.model.wet_proofing_effectiveness)
        else:
            self.wet_proofing = 1 #wet proofing was not effective, it is destroyed by the flood damage
            
        return
    
    def income(self):
        #increase he agent's budget based on the economic circumstances. See this as savings
        if self.model.economic_status == 'growth':
            self.budget += random.randint(500, 700)
        elif self.model.economic_status == 'recession':
            self.budget += random.randint(0, 200)
        elif self.model.economic_status == 'neutral':
            self.budget += random.randint(200, 500)
        
    def step(self): # agent step
        self.is_adapted = False
        if self.elevation == 1 and self.dry_proofing ==1 and self.wet_proofing == 1: #cumulative count for adapted agents
            self.is_adapted_cumulatief = False

        self.determine_AM() #determines Adaptation motivation
        self.choose_measure() #choose to implement one of the household measures
        self.undergone_measures.pop(0) #remove the undergone measures to make space in the memory
        if self.is_adapted:
            self.undergone_measures.append(1) #add 1 if a measure is implemented to the memory
        else:
            self.undergone_measures.append(0) #add 0 if no measure is implemented to the memory
        self.update_AM() #update all adaptation motivation attributes
        self.income() #increase or decrease the income
        

        
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
        self.flood_risk_threshold = self.model.flood_risk_threshold
        self.public_concern_threshold = self.model.public_concern_threshold
        self.damage_threshold = self.model.damage_threshold

        self.high_risk_bound = self.model.high_risk_bound
        self.lower_risk_bound = self.model.lower_risk_bound
        
    def estimate_impact(self):
        """A government estimates the impact of a potential flood, 
        based on the damage from the previous flood"""
        if self.model.avg_flood_damage >= self.damage_threshold:
            self.estimated_flood_impact = random.randrange(5,10)
        else:
            self.estimated_flood_impact = random.randrange(1,5)
        return self.estimated_flood_impact
        
               
    def make_decision(self, flood_risk, options_list):
        """Government makes a decision on what kind of tool to deploy"""

        if self.decision_made:
            self.decision.change_status()
            
        else: #if no decision has been made yet
        #First, the topic needs to be on the agenda:
            if self.agenda:#if a topic is on the agenda
        
                if flood_risk >= self.high_risk_bound:
                    # if the estimated risk is high, government will prioritise avg implementation time
                    lowest_planning = min([option.completion_time for option in options_list])
                    self.decision = [option for option in options_list if option.completion_time == lowest_planning][0]
                elif self.lower_risk_bound<=flood_risk< self.high_risk_bound:
                    # if the estimated risk is medium, government will prioritise protection level
                    highest_protection = max([option.protection_level for option in options_list])
                    self.decision = [option for option in options_list if option.protection_level == highest_protection][0]
                elif flood_risk < self.lower_risk_bound:
                    lowest_cost = min([option.cost for option in options_list])
                    self.decision = [option for option in options_list if option.cost == lowest_cost][0]
                    
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
        if self.model.options_list:
            self.estimate_impact()
            flood_risk = self.assess_risk(self.model.flood_probability, self.estimated_flood_impact) #take flood probability and flood impact from model
            public_concern = self.take_survey(self.model.avg_public_concern)
            self.put_on_agenda(public_concern,flood_risk)
            self.make_decision(flood_risk, self.model.options_list)
            self.implement_decision()
        else:
            pass

