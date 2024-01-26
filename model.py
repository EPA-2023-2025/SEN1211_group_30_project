# Importing necessary libraries
import networkx as nx
from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import geopandas as gpd
import rasterio as rs
import matplotlib.pyplot as plt
import numpy as np
import random
#import the RBB
from rbb import OrganizationInstrument
from rbb import RBBGovernment
from rbb import GovernmentStructure 

# Import the agent class(es) from agents.py
from agents import Households
from agents import Government
# Import functions from functions.py
from functions import get_flood_map_data, calculate_basic_flood_damage
from functions import map_domain_gdf, floodplain_gdf

dyke = OrganizationInstrument(name = 'Dyke', cost = 8, completion_time = 5, protection_level = 0.5, status = 1)
wetland = OrganizationInstrument(name = 'Wetland', cost = 5,  completion_time = 2, protection_level = 0.5, status = 1)  
options_list = [dyke, wetland]
public_concern_metric = 1 #public concern metric should be a likert scale like distribution 1-5

#could be defined in initialisation
flood_risk_treshold = 0.3
public_concern_treshold = 3


# Define the AdaptationModel class
class AdaptationModel(Model):
    """
    The main model running the simulation. It sets up the network of household agents,
    simulates their behavior, and collects data. The network type can be adjusted based on study requirements.
    """

    def __init__(self, 
                 seed = None,
                 number_of_households = 25, # number of household agents
                 # Simplified argument for choosing flood map. Can currently be "harvey", "100yr", or "500yr".
                 flood_map_choice='harvey',
                 # ### network related parameters ###
                 # The social network structure that is used.
                 # Can currently be "erdos_renyi", "barabasi_albert", "watts_strogatz", or "no_network"
                 network = 'watts_strogatz',
                 # likeliness of edge being created between two nodes
                 probability_of_network_connection = 0.4,
                 # number of edges for BA network
                 number_of_edges = 3,
                 # number of nearest neighbours for WS social network
                 number_of_nearest_neighbours = 5,
                 
                 # Probability of flood occurence
                 flood_probability = 1,
                 #severity of flood
                 flood_impact = 4,
                 
                #intention action gap which ensures that only a certain percentage of households can implement a measure
                intention_action_gap = 0.3,
                low_threshold = 0.6, 
                medium_threshold = 0.7,
                high_threshold = 0.8,
                
                upper_budget_threshold = 7000,
                lower_budget_threshold = 3000,
                
                # upper_threat_threshold = 4,
                # lower_threat_threshold = 1,
                
                elevation_time = 4, #time steps
                elevation_cost = 5000, # cost of implementing elevation
                elevation_protection = 0.3, #inundation level in meters
                elevation_effectiveness = 1, #effectiveness of elevation
                
                wet_proofing_time = 2, #time steps
                wet_proofing_cost = 3000, # cost of implementing wet_proofing
                wet_proofing_protection = 3, #inundation level in meters
                wet_proofing_effectiveness = 0.4, #effectiveness of wet_proofing
                
                dry_proofing_time = 1, #time steps
                dry_proofing_cost = 1500, # cost of implementing dry_proofing
                dry_proofing_protection = 1, # inundation level in meters
                dry_proofing_effectiveness = 0.85, #effectiveness of dry_proofing
                
                max_damage_costs = 5000 #Maximum repair costs a household can make -> change later
                 ):
        
        super().__init__(seed = seed)
        
        # defining the variables and setting the values
        self.number_of_households = number_of_households  # Total number of household agents
        self.seed = seed

        # network
        self.network = network # Type of network to be created
        self.probability_of_network_connection = probability_of_network_connection
        self.number_of_edges = number_of_edges
        self.number_of_nearest_neighbours = number_of_nearest_neighbours
        
        self.flood_probability = flood_probability
        
        self.intention_action_gap = intention_action_gap
        self.elevation_cost = elevation_cost
        self.elevation_time = elevation_time
        self.elevation_protection = elevation_protection
        self.elevation_effectiveness = elevation_effectiveness
        
        self.wet_proofing_cost = wet_proofing_cost
        self.wet_proofing_time = wet_proofing_time
        self.wet_proofing_protection = wet_proofing_protection
        self.wet_proofing_effectiveness = wet_proofing_effectiveness
        
        self.dry_proofing_cost = dry_proofing_cost
        self.dry_proofing_time = dry_proofing_time
        self.dry_proofing_protection = dry_proofing_protection
        self.dry_proofing_effectiveness = dry_proofing_effectiveness
        
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold
        
        self.upper_budget_threshold = upper_budget_threshold
        self.lower_budget_threshold = lower_budget_threshold
        
        # self.upper_threat_threshold = upper_threat_threshold
        # self.lower_threat_threshold = lower_threat_threshold
        
        self.max_damage_costs = max_damage_costs
        self.avg_flood_damage = 0
        self.last_flood = 0
        self.avg_public_concern = 0
        self.infrastructure = False

        # generating the graph according to the network used and the network parameters specified
        self.G = self.initialize_network()
        # create grid out of network graph
        self.grid = NetworkGrid(self.G)

        # Initialize maps
        self.initialize_maps(flood_map_choice)

        # set schedule for agents
        self.schedule = RandomActivation(self)  # Schedule for activating agents

        # create households through initiating a household on each node of the network graph
        for i, node in enumerate(self.G.nodes(), start = 1):
            household = Households(unique_id=i, model=self)
            self.schedule.add(household)
            self.grid.place_agent(agent=household, node_id=node)

        
        #create government agent
        government = Government(unique_id=0, model=self,structure=GovernmentStructure.CENTRALISED, detector=1)
        #government.decision = dyke
        self.schedule.add(government)
        # Data collection setup to collect data
        model_metrics = {
                        "total_adapted_households": self.total_adapted_households,
                        # ... other reporters ...
                        }
        
        agent_metrics = {
                        # "FloodDepthEstimated": "flood_depth_estimated",
                        # "FloodDamageEstimated" : "flood_damage_estimated",
                        # "FloodDepthActual": "flood_depth_actual",
                         "FloodDamageActual" : (lambda a: a.flood_damage_actual if a.unique_id != 0 else None),
                         "IsAdapted": (lambda a: a.is_adapted if a.unique_id != 0 else None),
                        # #"NeighborsCount": lambda a: a.count_neighbors(radius=1),
                        # "location":"location",
                        "Adaptation_Motivation": (lambda a: a.AM if a.unique_id != 0 else None),
                        "Financial_Loss": (lambda a: a.financial_loss if a.unique_id != 0 else None)
                        # # ... other reporters ...
                        }
        #set up the data collector 
        self.datacollector = DataCollector(model_reporters=model_metrics , agent_reporters=agent_metrics)
            

    def initialize_network(self):
        """
        Initialize and return the social network graph based on the provided network type using pattern matching.
        """
        if self.network == 'erdos_renyi':
            return nx.erdos_renyi_graph(n=self.number_of_households,
                                        p=self.number_of_nearest_neighbours / self.number_of_households,
                                        seed=self.seed)
        elif self.network == 'barabasi_albert':
            return nx.barabasi_albert_graph(n=self.number_of_households,
                                            m=self.number_of_edges,
                                            seed=self.seed)
        elif self.network == 'watts_strogatz':
            return nx.watts_strogatz_graph(n=self.number_of_households,
                                        k=self.number_of_nearest_neighbours,
                                        p=self.probability_of_network_connection,
                                        seed=self.seed)
        elif self.network == 'no_network':
            G = nx.Graph()
            G.add_nodes_from(range(self.number_of_households))
            return G
        else:
            raise ValueError(f"Unknown network type: '{self.network}'. "
                            f"Currently implemented network types are: "
                            f"'erdos_renyi', 'barabasi_albert', 'watts_strogatz', and 'no_network'")


    def initialize_maps(self, flood_map_choice):
        """
        Initialize and set up the flood map related data based on the provided flood map choice.
        """
        # Define paths to flood maps
        flood_map_paths = {
            'harvey': r'../input_data/floodmaps/Harvey_depth_meters.tif',
            '100yr': r'../input_data/floodmaps/100yr_storm_depth_meters.tif',
            '500yr': r'../input_data/floodmaps/500yr_storm_depth_meters.tif'  # Example path for 500yr flood map
        }

        # Throw a ValueError if the flood map choice is not in the dictionary
        if flood_map_choice not in flood_map_paths.keys():
            raise ValueError(f"Unknown flood map choice: '{flood_map_choice}'. "
                             f"Currently implemented choices are: {list(flood_map_paths.keys())}")

        # Choose the appropriate flood map based on the input choice
        flood_map_path = flood_map_paths[flood_map_choice]

        # Loading and setting up the flood map
        self.flood_map = rs.open(flood_map_path)
        self.band_flood_img, self.bound_left, self.bound_right, self.bound_top, self.bound_bottom = get_flood_map_data(
            self.flood_map)

    def total_adapted_households(self):
        """Return the total number of households that have adapted."""
        #BE CAREFUL THAT YOU MAY HAVE DIFFERENT AGENT TYPES SO YOU NEED TO FIRST CHECK IF THE AGENT IS ACTUALLY A HOUSEHOLD AGENT USING "ISINSTANCE"
        adapted_count = sum([1 for agent in self.schedule.agents if isinstance(agent, Households) and agent.is_adapted])
        return adapted_count
    
    def plot_model_domain_with_agents(self):
        fig, ax = plt.subplots()
        # Plot the model domain
        map_domain_gdf.plot(ax=ax, color='lightgrey')
        # Plot the floodplain
        floodplain_gdf.plot(ax=ax, color='lightblue', edgecolor='k', alpha=0.5)

        # Collect agent locations and statuses
        households = [agent for agent in self.schedule.agents if agent.unique_id != 0]
        for agent in households:
            color = 'blue' if agent.is_adapted else 'red'
            ax.scatter(agent.location.x, agent.location.y, color=color, s=10, label=color.capitalize() if not ax.collections else "")
            ax.annotate(str(agent.unique_id), (agent.location.x, agent.location.y), textcoords="offset points", xytext=(0,1), ha='center', fontsize=9)
        # Create legend with unique entries
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), title="Red: not adapted, Blue: adapted")

        # Customize plot with titles and labels
        plt.title(f'Model Domain with Agents at Step {self.schedule.steps}')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.show()
        return
        
    
    def calculate_public_concern(self):
        public_concern = []
        for agent in self.schedule.agents: 
            if agent.unique_id != 0:
                public_concern.append(agent.threat_appraisal)
        self.avg_public_concern = np.mean(public_concern)
        return self.avg_public_concern


    def get_floodplain_pop(self):
        """Returns a list of the unique id's of all the households that are located in a floodplain. """
        
        floodplain_pop = []
        for agent in self.schedule.agents:
            if agent.unique_id != 0:
                if agent.in_floodplain: 
                    floodplain_pop.append(agent)
        #return the list of agents that is in the floodplain
        #print(type(floodplain_pop))
        return floodplain_pop
    
    
    def get_protected_pop(self):
        """Returns a list of the protected households in the floodplain, 
        based on the large infrastructure"""
        #first, determine which households are in the floodplain:
        floodplain_pop = self.get_floodplain_pop()
        print("Print floodplain pop: ", floodplain_pop)
        #print(type(floodplain_pop))
        #access the government agent
        gov = [agent for agent in self.schedule.agents if agent.unique_id==0][0]

        #print("agent: ", gov )
        #determine the sample size to be drawn from the floodplain population = protection level * size of floodplain population 
        sample_size = int(gov.decision.protection_level * len(floodplain_pop))
        print("Sample size: ", sample_size)
    
        #create a list of the population in the floodplain that is protected by the infrastructure. 
        protected_pop = random.sample(floodplain_pop, sample_size)
        #return the list of agents that is protected
        print("protected_pop: ", protected_pop)
        return protected_pop
            
    
    def assign_protection(self):
        """Assigns a protected status to households in the floodplain 
        if they are within the protection range of a certain infrastructure"""
        
        #get the list of households objects that are protected
        protected_pop = self.get_protected_pop()
        print(protected_pop)
        #for every household in the list
        for household in protected_pop:
            #assign their protected status
            household.is_protected = True
            
        return
    
        
        
            
    
            
            
            
    def step(self):
        """
        introducing a shock: 
        at time step 5, there will be a global flooding.
        This will result in actual flood depth. Here, we assume it is a random number
        between 0.5 and 1.2 of the estimated flood depth. In your model, you can replace this
        with a more sound procedure (e.g., you can devide the floop map into zones and 
        assume local flooding instead of global flooding). The actual flood depth can be 
        estimated differently
        """
        
        #if there is infrastructure:
        if self.infrastructure:        
            self.assign_protection()  #first, assign protection to households in the floodplain
        
        # for agent in self.schedule.agents:
        #     if agent.unique_id != 0: #if the agent in the scheduler is not the government
        #         if agent.in_floodplain:
        #             print("agent: ", agent.unique_id, "Is protected: ", agent.is_protected) 
        
        if self.schedule.steps >= 5:
            # Check if flood occurs
            if random.random() <= self.flood_probability:
                flood_damages = []
                print('A Flood occurs')
                self.last_flood = self.schedule.steps
                #check to see if there is an infrastructural protection measure: 
                # if there is a measure, check its protection level
                # depending on the protection level,, take the percentage of agents in the floodplain and do not account damage to that percentage
                
                for agent in self.schedule.agents:
                    if agent.unique_id != 0: #if the agent in the scheduler is not the government
                        if agent.in_floodplain:
                            print("agent: ", agent.unique_id, "Is protected: ", agent.is_protected)
                            if agent.is_protected == False:
                                
                                #if agent.is_protected == False:
                                #Agent experiences a food
                                # agent.prior_hazard_experience.append(1)
                                # Calculate the actual flood depth as a random number between 0.5 and 1.2 times the estimated flood depth
                                agent.flood_depth_actual = random.uniform(0.5, 1.2) * agent.flood_depth_estimated
                                # calculate the actual flood damage given the actual flood depth
                                agent.flood_damage_actual = calculate_basic_flood_damage(agent.flood_depth_actual)
                                print('Original flood damage', agent.flood_damage_actual)
                                if agent.flood_depth_actual <= self.elevation_protection:
                                    if agent.elevation == 3:
                                        agent.flood_damage_actual = agent.flood_damage_actual * (1-self.elevation_effectiveness)
                                    
                                    elif agent.dry_proofing == 3 and agent.wet_proofing == 3:
                                        agent.flood_damage_actual = agent.flood_damage_actual * (1-self.dry_proofing_effectiveness) * (1-self.wet_proofing_effectiveness)
                                        
                                    elif agent.wet_proofing ==3:
                                        agent.flood_damage_actual = agent.flood_damage_actual * (1-self.wet_proofing_effectiveness)
                                    
                                    elif agent.dry_proofing ==3:
                                        agent.flood_damage_actual = agent.flood_damage_actual * (1-self.dry_proofing_effectiveness)
                                
                                    
                                elif agent.flood_depth_actual <= self.dry_proofing_protection:
                                    agent.elevation = 1
                                    if agent.dry_proofing == 3 and agent.wet_proofing == 3:
                                        agent.flood_damage_actual = agent.flood_damage_actual * (1-self.dry_proofing_effectiveness) * (1-self.wet_proofing_effectiveness)
                                        
                                    elif agent.wet_proofing ==3:
                                        agent.flood_damage_actual = agent.flood_damage_actual * (1-self.wet_proofing_effectiveness)
                                    
                                    elif agent.dry_proofing ==3:
                                        agent.flood_damage_actual = agent.flood_damage_actual * (1-self.dry_proofing_effectiveness)
                                        
                                elif agent.flood_depth_actual <= self.wet_proofing_protection:
                                    # in case the agent had implemented/was implementing elevation and dry-proofing, 
                                    # reset them because they are destroyed by the flood
                                    agent.elevation = 1
                                    agent.dry_proofing = 1
                                    if agent.wet_proofing ==3:
                                        agent.flood_damage_actual = agent.flood_damage_actual * (1-self.wet_proofing_effectiveness)
                                
                                
                                # Reset all protection measures to 1 after flood because flood exceeds all measures' inundation level
                                else:
                                    agent.elevation = 1
                                    agent.wet_proofing = 1
                                    agent.dry_proofing = 1
                                print('New flood damage', agent.flood_damage_actual) 
                                flood_damages.append(agent.flood_damage_actual)
                                
                                damage_costs = self.max_damage_costs * agent.flood_damage_actual
                                agent.budget -= damage_costs
                                agent.financial_loss += damage_costs
                                if agent.budget < 0:
                                    agent.budget = 0
                                else:
                                    pass
                            else:
                                pass
                    else:
                        
                        pass
                    
                if not flood_damages :
                    self.avg_flood_damage = 0
                else:     
                    self.avg_flood_damage = np.mean(flood_damages)
                 

        # Collect data and advance the model by one step
        # print('Avg flood damage last step: ', self.avg_flood_damage)
        # print('Avg public concern: ', self.avg_public_concern)
        
        self.calculate_public_concern()
        self.datacollector.collect(self)
        self.schedule.step()
       
        
    # def run_model(self):
    #     for i in range(6):
    #         self.step()
            

        
