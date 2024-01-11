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


public_concern_metric = 4
flood_risk_treshold = 0.3
public_concern_treshold = 5
l_term_infra_treshold = 5
s_term_infra_treshold = 3

class GovernmentStructure(Enum): 
    CENTRALISED = 1 #A centralised government 
    DECENTRALISED = 2

class Government(Agent):
    """
    A government agent that can make decisions on flood risk management 
    tools / strategies.
    """
    def __init__(
            self,
            # unique_id,
            # model,
            budget,
            # structure, 
            # effector, 
            detector: int #whether a government has a detector resource yes (1) or no (0). A detector resource is a survey. 
            ):
        self = self
        
        #super().__init__(unique_id, model)
        # self.structure = GovernmentStructure
        # self.effector = OrganizationInstrument
        self.detector: int = detector
        self.budget:int = budget #budget is measured in x1000 dollar
        
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
            public_concern = public_concern_metric 
            
        else: 
            public_concern = 1 #public concern is set to 1, because the government is unable to detect what the actual public concern is.
        print("public concern: ", public_concern)
        return public_concern
                
            
    def put_on_agenda(self,flood_risk, public_concern, flood_risk_treshold, public_concern_treshold):
        """Government decides to put flood risk management on agenda, based on risk and public concern"""
        
        if flood_risk > flood_risk_treshold:
            agenda = True
        else:
            if public_concern > public_concern_treshold: 
                agenda = True
            else:
                agenda = False
        print("Agenda: ", agenda)
        return agenda
    
    
    
    def make_decision(self, agenda, l_term_infra_treshold, s_term_infra_treshold):
        """Government makes a decision on what kind of tool to deploy"""
        #the tresholds are based on the idea that a government knows beforehand that a long term infrastructural project needs at least a certain amount of available budget, same for short term infrastructural projects. 
        decision = {}
        if agenda: 
            if self.budget > l_term_infra_treshold: 
                decision = {'long_short_infra': 1,
                            'short_infra': 0,
                            'no_infra': 0}
                
            elif self.budget > s_term_infra_treshold:
                decision = {'long_short_infra': 0,
                            'short_infra': 1,
                            'no_infra': 0}
            else:
                decision = {'long_short_infra': 0,
                            'short_infra': 0,
                            'no_infra': 1}
        else:
            decision = {'long_short_infra': 0,
                        'short_infra': 0,
                        'no_infra': 1}
        print(decision)
        return decision
    
    def step(self):
        flood_risk = self.assess_risk(flood_probability=0.1, flood_impact = 9) #take flood probability and flood impact from model
        public_concern = self.take_survey(public_concern_metric)
        agenda = self.put_on_agenda(flood_risk, public_concern, flood_risk_treshold, public_concern_treshold)
        self.make_decision(agenda, l_term_infra_treshold,s_term_infra_treshold)


    
class OrganizationInstrument():
    """ 
    An OrganizationInstrument represents a government's organisational
    tool (resource)
    """
    def __init__(
        self, 
        name: str,
        cost: int, 
        planning: int, 
        protection_level: int
        ):
        
        self.name: str = name
        self.cost: int = cost
        self.planning: int = planning 
        self.protection_level: int = protection_level #level of protection: how much it will cover the floodplane


government = Government(budget=8, detector = 1)
government.step()   
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
#         self.implementation = implementation
        