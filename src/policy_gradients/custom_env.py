'''SUMO Environment Wrapper for ATLA implementation'''
from .torch_utils import RunningStat, ZFilter, Identity, StateWithTime, RewardFilter

class SUMOEnvWrapper:
    def __init__(self, env, norm_states=False, norm_rewards=None, add_t_with_horizon=None, 
                 clip_obs=None, clip_rew=None, gamma=0.99):
        """
        Wraps a SUMO env to add normalization and time-as-feature capabilities.
        - env: the original SUMO env instance
        - norm_states: whether to normalize states (True/False)
        - norm_rewards: "rewards", "returns", or None
        - add_t_with_horizon: int (horizon) or None
        """

        # Allow disabling clipping if value is negative
        clip_obs = None if clip_obs is not None and clip_obs < 0 else clip_obs
        clip_rew = None if clip_rew is not None and clip_rew < 0 else clip_rew

        self.env = env
        self.num_features = list(env.traffic_signals.values())[0].observation_space.shape[0]  # Assumes the base env has this attribute
        self.state_filter = Identity()
        self.reward_filter = Identity()

        # State normalization
        if norm_states:
            self.state_filter = ZFilter(self.state_filter, shape=[self.num_features], clip=clip_obs)

        # Add time step as feature
        if add_t_with_horizon is not None:
            self.state_filter = StateWithTime(self.state_filter, horizon=add_t_with_horizon)

        # Reward normalization
        if norm_rewards == "rewards":
            self.reward_filter = ZFilter(self.reward_filter, shape=(), center=False, clip=clip_rew)
        elif norm_rewards == "returns":
            self.reward_filter = RewardFilter(self.reward_filter, shape=(), gamma=gamma, clip=clip_rew)

    def reset(self):
        result = self.env.reset()
        if isinstance(result, tuple):
            state, info = result
        else:
            state = result
            info = {}

        if hasattr(self.state_filter, 'reset'):
            self.state_filter.reset()
        if hasattr(self.reward_filter, 'reset'):
            self.reward_filter.reset()

        return self.state_filter(state, reset=True), info


    def step(self, action):
        next_state, reward, terminated, truncated, info = self.env.step(action)
        
        # Handle state and reward normalization
        filtered_state = self.state_filter(next_state)
        filtered_reward = self.reward_filter(reward)
        
        if self.env.single_agent:  # If it's single-agent mode, return 5 values
            return filtered_state, filtered_reward, terminated, truncated, info
        else:  # If it's multi-agent mode, return 4 values (observations for each agent)
            return filtered_state, filtered_reward, truncated, info


    def render(self, *args, **kwargs):
        return self.env.render(*args, **kwargs)

    @property
    def normalizer_read_only(self):
        return getattr(self.state_filter, 'read_only', False)

    @normalizer_read_only.setter
    def normalizer_read_only(self, value):
        if hasattr(self.state_filter, 'read_only'):
            self.state_filter.read_only = value
        if hasattr(self.reward_filter, 'read_only'):
            self.reward_filter.read_only = value

    def __getattr__(self, name):
        # Fallback to the original env's attributes/methods
        return getattr(self.env, name)
