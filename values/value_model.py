import gym
import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.functional as F
import torch.nn.functional as F
import numpy as np
from utils import *
import random

class Value(nn.module):
    def __init__(self, state_dim, hidden_dim, value_range, eta, epsilon):
        super(Value, self).__init__()
        self.input_dim = state_dim
        self.hidden_dim = hidden_dim

        #MLP for the value network
        self.value_hidden_weights = Variable(value_range / 2 - value_range * torch.rand(self.hidden_dim, self.input_dim), requires_grad=True)
        self.value_hidden_bias = Variable(value_range / 2 - value_range * torch.rand(self.hidden_dim, 1), requires_grad=True)
        self.value_out_weights = Variable(value_range / 2 - value_range * torch.rand(1, self.hidden_dim), requires_grad=True)
        self.value_out_bias = Variable(value_range / 2 - value_range * torch.rand(1, 1), requires_grad=True)
        self.eta = Variable(torch.tensor([eta]), requires_grad=True)

        #Epsilon is the maximum KL divergence term, which is supposed to work well at 0.1.
        self.epsilon = epsilon

        #Initialize the adam optimizer and set its learning rate.
        self.value_optimizer = torch.optim.Adam(self.parameters(), lr = lr)

    def get_value(self, states):
        '''
        The value V(S) is a MLP function of the state with relu activation on the hidden layer
        '''
        hidden = torch.relu(torch.matmul(self.value_hidden_weights, states) + self.value_hidden_bias)
        return torch.matmul(self.value_out_weights, hidden) + self.value_out_bias

    def get_weights(self, begin_states, end_states, rewards):
        '''
        The weight looks at the importance of the samples and is determined by values/rewards
        '''
        begin_values = self.get_value(begin_states)
        end_values = self.get_value(end_states)

        exp_values = rewards - begin_values + end_values
        max_val = torch.max(exp_values)

        weights = torch.exp(exp_values - max_val) / self.eta
        return weights

    def back_prop_step(self, begin_states, end_states, rewards):
        '''
        This function calculates the loss for the value function.
        '''
        N = len(begin_states)
        begin_values = self.get_value(begin_states)
        end_values = self.get_value(end_states)
        check_values(begin_from_value=begin_values,end_from_value=end_values)

        #Calculate the loss according to the formula.
        loss = self.eta * self.epsilon + self.eta * logsumexponent((rewards - begin_values + end_values) / self.eta, N) #torch.log(torch.sum(torch.exp((rewards - begin_values + end_values) / self.eta) / N))
        check_values(loss_value=loss)

        #Take optimizer step
        self.value_optimizer.zero_grad()
        loss.backward(retain_graph = True)
        self.value_optimizer.step()
        return loss.data.item()
