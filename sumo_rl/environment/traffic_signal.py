"""
This is the definition and configurations of the traffic lights structure in the simulator
"""

import os
import sys
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare the environment variable 'SUMO_HOME'")
import traci
import numpy as np
from gym import spaces


class TrafficSignal:
    """
    This class represents a Traffic Signal of an intersection
    It is responsible for retrieving information and changing the traffic phase using Traci API

    IMPORTANT: It assumes that the traffic phases defined in the .net file are of the form:
        [green_phase, yellow_phase, green_phase, yellow_phase, ...]
    Currently it is not supporting all-red phases (but should be easy to implement it).

    Default observation space is a vector R^(#greenPhases + 2 * #lanes)
    s = [current phase one-hot encoded, density for each lane, queue for each lane]
    You can change this by modifing self.observation_space and the method _compute_observations()

    Action space is which green phase is going to be open for the next delta_time seconds
    """
    def __init__(self, env, ts_id, delta_time, yellow_time, min_green, max_green, begin_time, sumo):
        self.id = ts_id
        self.env = env
        self.delta_time = delta_time
        self.yellow_time = yellow_time
        self.min_green = min_green
        self.max_green = max_green
        self.green_phase = 0
        self.is_yellow = False
        self.time_since_last_phase_change = 0
        self.next_action_time = begin_time
        self.last_measure = 0.0
        self.last_reward = None
        self.sumo = sumo

        self.build_phases() # num_green_phases is defined here

        self.lanes = list(dict.fromkeys(self.sumo.trafficlight.getControlledLanes(self.id)))  # Remove duplicates and keep order
        self.out_lanes = [link[0][1] for link in self.sumo.trafficlight.getControlledLinks(self.id) if link]
        self.out_lanes = list(set(self.out_lanes))
        self.lanes_length = {lane: self.sumo.lane.getLength(lane) for lane in self.lanes}
        # change this to change the state space
        '''
        Space.Box represents continous action space. The state space is (num_green_phases + 1 + 2*len(lanes))-dimensional vector.
        For each dimension, the range of valid values is defined by the lower and upper bounds, which are between 0 and 1.
        The first num_green_phases dimensions are one-hot encoded representation of the current green phase. For example, if 
        there are 4 green phases, the first 4 dimensions will be [1, 0, 0, 0] if the current green phase is 0, [0, 1, 0, 0] if
        the current green phase is 1, and so on. The next dimension is a binary variable that is active if the minimum green time
        has already elapsed. The next 2*len(lanes) dimensions are the density and stopped-density for each lane.
        '''
        self.observation_space = spaces.Box(low=np.zeros(self.num_green_phases+1+2*len(self.lanes), dtype=np.float32),
            high=np.ones(self.num_green_phases+1+2*len(self.lanes), dtype=np.float32))
        
        self.discrete_observation_space = spaces.Tuple((
            spaces.Discrete(self.num_green_phases),                       # Green Phase
            spaces.Discrete(2),                                           # Binary variable active if min_green seconds already elapsed
            *(spaces.Discrete(10) for _ in range(2*len(self.lanes)))      # Density and stopped-density for each lane
        ))
        # discrete action space, where we choose what will be the next green phase, out of the num_green_phases possibilities
        self.action_space = spaces.Discrete(self.num_green_phases)

    def build_phases(self):
        phases = self.sumo.trafficlight.getAllProgramLogics(self.id)[0].phases
        if self.env.fixed_ts:
            self.num_green_phases = len(phases)//2  # Number of green phases == number of phases (green+yellow) divided by 2
            return

        self.green_phases = []
        self.yellow_dict = {}
        for phase in phases:
            state = phase.state
            if 'y' not in state and (state.count('r') + state.count('s') != len(state)):
                self.green_phases.append(self.sumo.trafficlight.Phase(60, state))
        self.num_green_phases = len(self.green_phases)
        self.all_phases = self.green_phases.copy()

        for i, p1 in enumerate(self.green_phases):
            for j, p2 in enumerate(self.green_phases):
                if i == j: continue
                yellow_state = ''
                for s in range(len(p1.state)):
                    if (p1.state[s] == 'G' or p1.state[s] == 'g') and (p2.state[s] == 'r' or p2.state[s] == 's'):
                        yellow_state += 'y'
                    else:
                        yellow_state += p1.state[s]
                self.yellow_dict[(i,j)] = len(self.all_phases)
                self.all_phases.append(self.sumo.trafficlight.Phase(self.yellow_time, yellow_state))

        programs = self.sumo.trafficlight.getAllProgramLogics(self.id)
        logic = programs[0]
        logic.type = 0
        logic.phases = self.all_phases
        self.sumo.trafficlight.setProgramLogic(self.id, logic)
        self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[0].state)

    @property
    def time_to_act(self):
        return self.next_action_time == self.env.sim_step
    
    def update(self):
        self.time_since_last_phase_change += 1
        if self.is_yellow and self.time_since_last_phase_change == self.yellow_time:
            #self.sumo.trafficlight.setPhase(self.id, self.green_phase)
            self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[self.green_phase].state)
            self.is_yellow = False

    def set_next_phase(self, new_phase):
        """
        Sets what will be the next green phase and sets yellow phase if the next phase is different than the current

        :param new_phase: (int) Number between [0..num_green_phases] 
        """
        new_phase = int(new_phase)
        if self.green_phase == new_phase or self.time_since_last_phase_change < self.yellow_time + self.min_green:
            #self.sumo.trafficlight.setPhase(self.id, self.green_phase)
            self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[self.green_phase].state)
            self.next_action_time = self.env.sim_step + self.delta_time
        else:
            #self.sumo.trafficlight.setPhase(self.id, self.yellow_dict[(self.green_phase, new_phase)])  # turns yellow
            self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[self.yellow_dict[(self.green_phase, new_phase)]].state)
            self.green_phase = new_phase
            self.next_action_time = self.env.sim_step + self.delta_time
            self.is_yellow = True
            self.time_since_last_phase_change = 0
    
    # change to modify state space
    def compute_observation(self):
        phase_id = [1 if self.green_phase == i else 0 for i in range(self.num_green_phases)]  # one-hot encoding
        min_green = [0 if self.time_since_last_phase_change < self.min_green + self.yellow_time else 1]
        density = self.get_lanes_density()
        queue = self.get_lanes_queue()
        # change this to match the observation space
        observation = np.array(phase_id + min_green + density + queue, dtype=np.float32)
        return observation
    
    # gets the final reward of the traffic signal
    def compute_reward(self):
        self.last_reward = self._waiting_time_reward()
        return self.last_reward
    
    def _pressure_reward(self):
        return -self.get_pressure()

    def _queue_average_reward(self):
        new_average = np.mean(self.get_stopped_vehicles_num())
        reward = self.last_measure - new_average
        self.last_measure = new_average
        return reward

    def _queue_reward(self):
        return - (sum(self.get_stopped_vehicles_num()))**2

    # Used right before computing the final reward
    def _waiting_time_reward(self):
        ts_wait = sum(self.get_waiting_time_per_lane()) / 100.0
        reward = self.last_measure - ts_wait
        self.last_measure = ts_wait
        return reward

    def _waiting_time_reward2(self):
        ts_wait = sum(self.get_waiting_time())
        self.last_measure = ts_wait
        if ts_wait == 0:
            reward = 1.0
        else:
            reward = 1.0/ts_wait
        return reward

    def _waiting_time_reward3(self):
        ts_wait = sum(self.get_waiting_time())
        reward = -ts_wait
        self.last_measure = ts_wait
        return reward

    # gets the total waiting time of all vehicles in the intersection
    def get_waiting_time_per_lane(self):
        '''
        for each lane, get all vehicles per lane and sum their waiting time.
        append the sum of waiting time for each lane to the list wait_time_per_lane'''
        wait_time_per_lane = []
        for lane in self.lanes:
            # get all vehicles ID in the lane
            veh_list = self.sumo.lane.getLastStepVehicleIDs(lane)
            wait_time = 0.0
            for veh in veh_list:
                # get id of the lane where the vehicle is
                veh_lane = self.sumo.vehicle.getLaneID(veh)
                # acc holds the accumulated waiting time of the vehicle
                acc = self.sumo.vehicle.getAccumulatedWaitingTime(veh)
                if veh not in self.env.vehicles:
                    self.env.vehicles[veh] = {veh_lane: acc}
                else:
                    self.env.vehicles[veh][veh_lane] = acc - sum([self.env.vehicles[veh][lane] for lane in self.env.vehicles[veh].keys() if lane != veh_lane])
                # add the waiting time of the vehicle to the total waiting time of the lane
                wait_time += self.env.vehicles[veh][veh_lane]
            wait_time_per_lane.append(wait_time)
        return wait_time_per_lane

    def get_pressure(self):
        return abs(sum(self.sumo.lane.getLastStepVehicleNumber(lane) for lane in self.lanes) - sum(self.sumo.lane.getLastStepVehicleNumber(lane) for lane in self.out_lanes))

    def get_out_lanes_density(self):
        vehicle_size_min_gap = 7.5  # 5(vehSize) + 2.5(minGap)
        return [min(1, self.sumo.lane.getLastStepVehicleNumber(lane) / (self.sumo.lane.getLength(lane) / vehicle_size_min_gap)) for lane in self.out_lanes]

    def get_lanes_density(self):
        vehicle_size_min_gap = 7.5  # 5(vehSize) + 2.5(minGap)
        # getLastStepVehicleNumber(lane) returns the number of vehicles in the lane at the last simulation step
        return [min(1, self.sumo.lane.getLastStepVehicleNumber(lane) / (self.lanes_length[lane] / vehicle_size_min_gap)) for lane in self.lanes]

    def get_lanes_queue(self):
        vehicle_size_min_gap = 7.5  # 5(vehSize) + 2.5(minGap)
        return [min(1, self.sumo.lane.getLastStepHaltingNumber(lane) / (self.lanes_length[lane] / vehicle_size_min_gap)) for lane in self.lanes]
    
    def get_total_queued(self):
        return sum([self.sumo.lane.getLastStepHaltingNumber(lane) for lane in self.lanes])

    def _get_veh_list(self):
        veh_list = []
        for lane in self.lanes:
            veh_list += self.sumo.lane.getLastStepVehicleIDs(lane)
        return veh_list
