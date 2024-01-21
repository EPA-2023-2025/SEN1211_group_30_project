# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 11:44:51 2024

@author: nelen
"""
# Importing necessary libraries
import random
from mesa import Agent
from mesa import Model
from shapely.geometry import Point
from shapely import contains_xy
from enum import Enum

#should be imported from model:
flood_probability = 0.1 #float 0-1
flood_impact = 9 #int [1-10]
public_concern_metric = 1 #public concern metric should be a likert scale like distribution 1-5

#could be defined in initialisation
flood_risk_treshold = 0.3
public_concern_treshold = 3
eng_infra_treshold = 5
nat_infra_treshold = 3
timeframe = 5 #(1-flood_prob) * max_time

class GovernmentStructure(Enum): 
    CENTRALISED = 1 #A centralised government : federal / state
    DECENTRALISED = 2 #states / regional

class RBBGovernment():
    """
    A government agent that can make decisions on flood risk management 
    tools / strategies.
    """
    def __init__(
            self,
            budget,
            structure, 
            # effector, 
            detector: int #whether a government has a detector resource yes (1) or no (0). A detector resource is a survey. 
            ):
        self = self
        
        self.structure = GovernmentStructure
        # self.effector = OrganizationInstrument
        self.detector: int = detector
        self.budget:int = budget #budget is measured in x1000 dollar
        self.time_gov_proc = self.estimate_planning()
        
    def assess_risk(self, flood_probability: float, flood_impact: int): 
        """Assess the risk of a flooding"""
        flood_risk = flood_probability * flood_impact
        print("flood risk: ", flood_risk)
        return flood_risk
    
    def take_survey(self, public_concern_metric): #take public concern metric from model metrics. #public concern metric should be an int scale 1-10
        """If a government has the ability to conduct surveys, 
        this method takes a survey about its citizen's level of concern
        """
        
        if self.detector:
            public_concern = public_concern_metric  #public concern metric should be a likert scale like distribution 1-5
            
        else: 
            public_concern = 3 #according to Likert scale, 3 is neutral level of concern. public concern is set to 0, because the government is unable to detect what the actual public concern is.
        print("public concern: ", public_concern)
        return public_concern
    
    def estimate_planning(self):
        """Depending on a governments organisational structure, duration of project procedures
        such as government approval differs. This method estimates the duration based on government structure. 
        """
        if self.structure == GovernmentStructure.CENTRALISED:
            self.time_gov_proc = 4 #lengthy
        elif self.structure == GovernmentStructure.DECENTRALISED:
            self.time_gov_proc = 2 #fast
        else:
            self.time_gov_proc = 3 #average
        return self.time_gov_proc
              
            
    def put_on_agenda(self,flood_risk, public_concern, flood_risk_treshold, public_concern_treshold):
        """Government decides to put flood risk management on agenda, based on risk and public concern"""
        #eventueel toevoegen: extreme weather events / experience
        if flood_risk > flood_risk_treshold:
            agenda = True
        else:
            if public_concern > public_concern_treshold: 
                agenda = True
            else:
                agenda = False
        print("Agenda: ", agenda)
        return agenda
    
    
    
    def make_decision(self, agenda, timeframe, eng_infra_treshold, nat_infra_treshold):
        """Government makes a decision on what kind of tool to deploy"""
        #the tresholds are based on the idea that a government knows beforehand that a long term infrastructural project needs at least a certain amount of available budget, same for short term infrastructural projects. 
        decision = {}
        if agenda: #if a topic is on the agenda
            if self.time_gov_proc <= timeframe: #if the estimated timeframe is lower or equal to length of government procedures
                if self.budget >= eng_infra_treshold: #if the budget is larger or equal to long term infrastructure budget
                 #add political influence here: are people against engineered projects? Then still choose nature based infrastructure
                    decision = {'engineered_infra': 1,  #engineered infrastructure like levees and storm surge barriers
                                'nature_based_infra': 0, #nature based infrastructure like dunes and wetlands
                                'no_infra': 0} #no infra 
                
                elif self.budget > nat_infra_treshold:
                    decision = {'engineered_infra': 0,
                                'nature_based_infra': 1,
                                'no_infra': 0}
                else:
                    decision = {'engineered_infra': 0,
                                'nature_based_infra': 0,
                                'no_infra': 1}
            
        else:#if the duration of government procedures takes longer than the estimated timeframe:
            decision = {'engineered_infra': 0,
                        'nature_based_infra': 0,
                        'no_infra': 1}
        print(decision)
        return decision
    #if decision is made moet agenda weer false worden
    #decision aanpassen naar variabelen met 1 = not implemented, 2 = implementing, 3 = implemented-> security is dan 'full'
    
    def implement_decision(self):
        pass
    
    def step(self):
        pass


# government = RBBGovernment(structure=GovernmentStructure.CENTRALISED, budget=8, detector=1)    
# government.step()
class OrganizationInstrument():
    """ 
    An OrganizationInstrument represents a government's organisational
    tool (resource)
    """
    def __init__(
        self, 
        name: str,
        status: int, #1 = not implemented, 2 = implementing, 3 = implemented-> security is dan 'full'
        cost: int, 
        planning: int, #due to lengthy government procedures and construction times
        protection_level: int
        ):
        
        self.name: str = name
        self.status: int = status
        self.cost: int = cost
        self.planning: int = planning 
        self.protection_level: int = protection_level #level of protection: how much it will cover the floodplane



# class Strategy():
#     """ 
#     A Strategy object represents a set of tools that make up
#     a flood risk management strategy
#     """     
#     def __init__(
#             self, name, cost, planning, implementation ):
#         self.name = name
#         self.cost = cost
#         self.planning = planning
#         self.protection_level = protection_level 
        