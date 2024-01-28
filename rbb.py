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
            structure: GovernmentStructure, #what kind of organisational structure the government has
            detector: int #whether a government has a detector resource yes (1) or no (0). A detector resource is a survey. 
            
            ):
        self = self
        self.structure = GovernmentStructure
        self.detector: int = detector
        self.agenda = False
        self.decision_made = False
        self.decision = None
        self.flood_risk_threshold = 1.5
        self.public_concern_threshold = 0.6
        
        
    def assess_risk(self, flood_probability: float, flood_impact: int): 
        """Assess the risk of a flooding"""
        flood_risk = flood_probability * flood_impact 
        print("flood risk: ", flood_risk)
        return flood_risk
    
    
    def take_survey(self, public_concern_metric): #take public concern metric from model metrics. 
        """If a government has the ability to conduct surveys, 
        this method takes a survey about its citizen's level of concern
        """
        if self.detector == 1:
            public_concern = public_concern_metric  #public concern metric should be a float in the range [0,1]
            
        else: 
            public_concern = 0 # neutral level of concern. public concern is set to 0, because the government is unable to detect what the actual public concern is.
        #print("public concern: ", public_concern)
        return public_concern
    
        
    def put_on_agenda(self, public_concern, flood_risk):
        
        """Government decides to put flood risk management on agenda, based on risk and public concern"""
        
        if self.decision_made: #if a decision has already been made
            pass
        else:
         if flood_risk > self.flood_risk_threshold: #if the flood risk is higher than the threshold
             self.agenda = True
         else:
             if public_concern > self.public_concern_threshold: 
                 self.agenda = True
             else:
                 self.agenda = False
         #print("Agenda: ", self.agenda)
         return self.agenda
    
    
    def change_agenda(self):
        if self.agenda:
            self.agenda = False
        return self.agenda
    
    def make_decision(self):
        """Government makes a decision on whether to build infrastructure or not"""
        pass 


    def implement_decision(self):
        pass
    
    def check_status(self):
        if self.agenda: 
            status = 'Flood measure decision is on agenda'
        else: 
            status = 'Flood measure decision is NOT on agenda'
        return status   
            
    def step(self):
        print('Status:', self.check_status() )
        
        


class OrganizationInstrument():
    """ 
    An OrganizationInstrument represents a government's organisational
    tool (resource)
    """
    def __init__(
        self, 
        name: str,
        cost: int,  
        completion_time: int, #due to lengthy government procedures and construction times, the time that it takes to complete
        protection_level: float,
        status: int = 1, #1 = not implemented, 2 = implementing, 3 = implemented-> security is dan 'full'
        implementation_counter:int = 0 #counter that keeps track of an instrument's implementation duration 
        ):
        
        self.name: str = name
        self.status: int = status
        self.cost: int = cost
        self.completion_time: int = completion_time
        self.implementation_counter: int  = implementation_counter #time counter per step laten toevoegen, als gelijk aan planning dan status = 2
        self.protection_level: int = protection_level #level of protection: how much it will cover the floodplane


    def impact_planning(self, structure, centralised_factor = 4, decentralised_factor = 4 ):
        """Depending on a governments organisational structure, duration of project procedures
        such as government approval differs. This method estimates the duration based on government structure. 
        """
        if structure == GovernmentStructure.CENTRALISED:
            #increase planning with certain factor
            self.completion_time = self.completion_time + centralised_factor
            
        elif structure == GovernmentStructure.DECENTRALISED:
            #decrease planning with certain factor
            self.completion_time = self.completion_time - decentralised_factor
        else:
            #planning stays the same
            self.completion_time = self.completion_time
            
        return self.completion_time
    
    
    def change_status(self):
        """Changes an instrument's implementation status."""
        if self.status == 1:#if the status is 'not implemented'
            self.status = 2 #set the status to 'implementing...'
            self.implementation_counter+=1
        elif self.status == 2: #if the status is 'implementing...'
            if self.implementation_counter != self.completion_time: #if it is not finished implementing yet
                self.status = 2 #keep the status on 'implementing'
                self.implementation_counter+=1 #and increase the time counter of the implementation duration
            else:
                self.status = 3 #if the implementation is complete, change status to 'implemented' 
        else: 
            self.status = 3
        print("Status of ", self.name, ": ", self.status, "\n implementation counter: ", self.implementation_counter )
        return self.status
    
            
             
        
