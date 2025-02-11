import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from torch.distributions import categorical

class PPO_ADV(nn.Module):
    '''
    The goal of PPO is to improve training stability of a policy by limiting the changes that can be made to a policy.
        - smaller updates are more likely to converge to an optimal solutions
        - large jumps can fall off of a cliff
    '''
    def __init__(self, input_dim, output_dim, epsilon):
        super(PPO_ADV, self).__init__()
        
        self.epsilon = epsilon
        self.name = "PPO_ADV"

        # Learns the mean
        self.policy = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

        # Learns the value
        self.critic = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
    
    def loss_func(self, buffer):

        logits = self.policy(buffer.states)
        value = self.critic(buffer.states)

        adv = buffer.returns - value.squeeze(-1)
        loss_value = torch.mean(adv**2)

        # importance sampling. logs turned this into a subtraction
        # First, get probability distribution of the updated policy. Second, get the log probabilities of the same actions taken in the old policy.
        probs = categorical.Categorical(logits=logits)
        new_log_probs = probs.log_prob(buffer.actions)

        r = torch.exp(new_log_probs - buffer.log_probs)

        loss_policy = -torch.mean(torch.min(r*adv, torch.clamp(r,1-self.epsilon, 1+self.epsilon)*adv))

        loss = loss_value + loss_policy

        return -loss