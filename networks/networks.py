import torch
import torch.nn as nn
import torch.nn.functional as F

from networks.layers import NoisyLinear
from networks.network_bodies import SimpleBody, AtariBody
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class DQN(nn.Module):
    def __init__(self, input_shape, num_actions, noisy=False, sigma_init=0.5, body=SimpleBody):
        super(DQN, self).__init__()
        
        self.input_shape = input_shape
        self.num_actions = num_actions
        self.noisy=noisy

        self.body = body(input_shape, num_actions, noisy, sigma_init)

        self.fc1 = nn.Linear(self.body.feature_size(), 512) if not self.noisy else NoisyLinear(self.body.feature_size(), 512, sigma_init)
        self.fc2 = nn.Linear(512, self.num_actions) if not self.noisy else NoisyLinear(512, self.num_actions, sigma_init)
        
    def forward(self, x):
        x = self.body(x)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)

        return x

    def sample_noise(self):
        if self.noisy:
            self.body.sample_noise()
            self.fc1.sample_noise()
            self.fc2.sample_noise()


class DuelingDQN(nn.Module):
    def __init__(self, input_shape, num_outputs, noisy=False, sigma_init=0.5, body=SimpleBody):
        super(DuelingDQN, self).__init__()
        
        self.input_shape = input_shape
        self.num_actions = num_outputs
        self.noisy=noisy

        self.body = body(input_shape, num_outputs, noisy, sigma_init)

        self.adv1 = nn.Linear(self.body.feature_size(), 512) if not self.noisy else NoisyLinear(self.body.feature_size(), 512, sigma_init)
        self.adv2 = nn.Linear(512, self.num_actions) if not self.noisy else NoisyLinear(512, self.num_actions, sigma_init)

        self.val1 = nn.Linear(self.body.feature_size(), 512) if not self.noisy else NoisyLinear(self.body.feature_size(), 512, sigma_init)
        self.val2 = nn.Linear(512, 1) if not self.noisy else NoisyLinear(512, 1, sigma_init)
        
    def forward(self, x):
        x = self.body(x)

        adv = F.relu(self.adv1(x))
        adv = self.adv2(adv)

        val = F.relu(self.val1(x))
        val = self.val2(val)

        return val + adv - adv.mean()
    
    def sample_noise(self):
        if self.noisy:
            self.body.sample_noise()
            self.adv1.sample_noise()
            self.adv2.sample_noise()
            self.val1.sample_noise()
            self.val2.sample_noise()

class CategoricalDQN(nn.Module):
    def __init__(self, input_shape, num_outputs, noisy=False, sigma_init=0.5, body=SimpleBody, atoms=51):
        super(CategoricalDQN, self).__init__()
        
        self.input_shape = input_shape
        self.num_actions = num_outputs
        self.noisy=noisy
        self.atoms=atoms

        self.body = body(input_shape, num_outputs, noisy, sigma_init)

        self.fc1 = nn.Linear(self.body.feature_size(), 512) if not self.noisy else NoisyLinear(self.body.feature_size(), 512, sigma_init)
        self.fc2 = nn.Linear(512, self.num_actions*self.atoms) if not self.noisy else NoisyLinear(512, self.num_actions*self.atoms, sigma_init)

        
    def forward(self, x):
        x = self.body(x)

        x = F.relu(self.fc1(x))
        x = self.fc2(x)

        return F.softmax(x.view(-1, self.num_actions, self.atoms), dim=2)
    
    def sample_noise(self):
        if self.noisy:
            self.body.sample_noise()
            self.fc1.sample_noise()
            self.fc2.sample_noise()

class CategoricalDuelingDQN(nn.Module):
    def __init__(self, input_shape, num_outputs, noisy=False, sigma_init=0.5, body=SimpleBody, atoms=51):
        super(CategoricalDuelingDQN, self).__init__()
        
        self.input_shape = input_shape
        self.num_actions = num_outputs
        self.noisy=noisy
        self.atoms=atoms

        self.body = body(input_shape, num_outputs, noisy, sigma_init)

        self.adv1 = nn.Linear(self.body.feature_size(), 512) if not self.noisy else NoisyLinear(self.body.feature_size(), 512, sigma_init)
        self.adv2 = nn.Linear(512, self.num_actions*self.atoms) if not self.noisy else NoisyLinear(512, self.num_actions*self.atoms, sigma_init)

        self.val1 = nn.Linear(self.body.feature_size(), 512) if not self.noisy else NoisyLinear(self.body.feature_size(), 512, sigma_init)
        self.val2 = nn.Linear(512, 1*self.atoms) if not self.noisy else NoisyLinear(512, 1*self.atoms, sigma_init)

        
    def forward(self, x):
        x = self.body(x)

        adv = F.relu(self.adv1(x))
        adv = self.adv2(adv).view(-1, self.num_actions, self.atoms)

        val = F.relu(self.val1(x))
        val = self.val2(val).view(-1, 1, self.atoms)

        final = val + adv - adv.mean(dim=1).view(-1, 1, self.atoms)

        return F.softmax(final, dim=2)
    
    def sample_noise(self):
        if self.noisy:
            self.body.sample_noise()
            self.adv1.sample_noise()
            self.adv2.sample_noise()
            self.val1.sample_noise()
            self.val2.sample_noise()


class QRDQN(nn.Module):
    def __init__(self, input_shape, num_outputs, noisy=False, sigma_init=0.5, body=SimpleBody, quantiles=51):
        super(QRDQN, self).__init__()
        
        self.input_shape = input_shape
        self.num_actions = num_outputs
        self.noisy=noisy
        self.quantiles=quantiles

        self.body = body(input_shape, num_outputs, noisy, sigma_init)

        self.fc1 = nn.Linear(self.body.feature_size(), 512) if not self.noisy else NoisyLinear(self.body.feature_size(), 512, sigma_init)
        self.fc2 = nn.Linear(512, self.num_actions*self.quantiles) if not self.noisy else NoisyLinear(512, self.num_actions*self.quantiles, sigma_init)

        
    def forward(self, x):
        x = self.body(x)

        x = F.relu(self.fc1(x))
        x = self.fc2(x)

        return x.view(-1, self.num_actions, self.quantiles)
    
    def sample_noise(self):
        if self.noisy:
            self.body.sample_noise()
            self.fc1.sample_noise()
            self.fc2.sample_noise()


class DuelingQRDQN(nn.Module):
    def __init__(self, input_shape, num_outputs, noisy=False, sigma_init=0.5, body=SimpleBody, quantiles=51):
        super(DuelingQRDQN, self).__init__()
        
        self.input_shape = input_shape
        self.num_actions = num_outputs
        self.noisy=noisy
        self.quantiles=quantiles

        self.body = body(input_shape, num_outputs, noisy, sigma_init)

        self.adv1 = nn.Linear(self.body.feature_size(), 512) if not self.noisy else NoisyLinear(self.body.feature_size(), 512, sigma_init)
        self.adv2 = nn.Linear(512, self.num_actions*self.quantiles) if not self.noisy else NoisyLinear(512, self.num_actions*self.quantiles, sigma_init)

        self.val1 = nn.Linear(self.body.feature_size(), 512) if not self.noisy else NoisyLinear(self.body.feature_size(), 512, sigma_init)
        self.val2 = nn.Linear(512, 1*self.quantiles) if not self.noisy else NoisyLinear(512, 1*self.quantiles, sigma_init)

        
    def forward(self, x):
        x = self.body(x)

        adv = F.relu(self.adv1(x))
        adv = self.adv2(adv).view(-1, self.num_actions, self.quantiles)

        val = F.relu(self.val1(x))
        val = self.val2(val).view(-1, 1, self.quantiles)

        final = val + adv - adv.mean(dim=1).view(-1, 1, self.quantiles)

        return final
    
    def sample_noise(self):
        if self.noisy:
            self.body.sample_noise()
            self.adv1.sample_noise()
            self.adv2.sample_noise()
            self.val1.sample_noise()
            self.val2.sample_noise()


########Recurrent Architectures#########

class DRQN(nn.Module):
    def __init__(self, input_shape, num_actions, noisy=False, sigma_init=0.5, gru_size=512, bidirectional=False, body=SimpleBody):
        super(DRQN, self).__init__()
        
        self.input_shape = input_shape
        self.num_actions = num_actions
        self.noisy = noisy
        self.gru_size = gru_size
        self.bidirectional = bidirectional
        self.num_directions = 2 if self.bidirectional else 1

        self.body = body(input_shape, num_actions, noisy=self.noisy, sigma_init=sigma_init)
        self.gru = nn.GRU(self.body.feature_size(), self.gru_size, num_layers=1, batch_first=True, bidirectional=bidirectional)
        self.fc2 = nn.Linear(self.gru_size, self.num_actions) if not self.noisy else NoisyLinear(self.gru_size, self.num_actions, sigma_init)
        
    def forward(self, x, hx=None):
        batch_size = x.size(0)
        sequence_length = x.size(1)
        
        x = x.view((-1,)+self.input_shape)
        
        #format outp for batch first gru
        feats = self.body(x).view(batch_size, sequence_length, -1)
        hidden = self.init_hidden(batch_size) if hx is None else hx
        out, hidden = self.gru(feats, hidden)
        x = self.fc2(out)

        return x, hidden

    def init_hidden(self, batch_size):
        return torch.zeros(1*self.num_directions, batch_size, self.gru_size, device=device, dtype=torch.float)
    
    def sample_noise(self):
        if self.noisy:
            self.body.sample_noise()
            self.fc2.sample_noise()


########Actor Critic Architectures#########
class ActorCritic(nn.Module):
    def __init__(self, input_shape, num_actions, conv_out=64, use_gru=False, gru_size=512, noisy_nets=False, sigma_init=0.5):
        super(ActorCritic, self).__init__()
        self.conv_out = conv_out
        self.use_gru = use_gru
        self.gru_size = gru_size
        self.noisy_nets = noisy_nets

        init_ = lambda m: self.layer_init(m, nn.init.orthogonal_,
                    lambda x: nn.init.constant_(x, 0),
                    nn.init.calculate_gain('relu'))

        self.conv1 = init_(nn.Conv2d(input_shape[0], 32, kernel_size=8, stride=4))
        self.conv2 = init_(nn.Conv2d(32, 64, kernel_size=4, stride=2))
        self.conv3 = init_(nn.Conv2d(64, self.conv_out, kernel_size=3, stride=1))

        if use_gru:
            self.fc1 = init_(nn.Linear(self.feature_size(input_shape), 512)) if not self.noisy_nets else init_(NoisyLinear(self.feature_size(input_shape), 512, sigma_init))
            self.gru = nn.GRUCell(512, self.gru_size)

            nn.init.orthogonal_(self.gru.weight_ih.data)
            nn.init.orthogonal_(self.gru.weight_hh.data)
            self.gru.bias_ih.data.fill_(0)
            self.gru.bias_hh.data.fill_(0)
        else:
            init_ = lambda m: self.layer_init(m, nn.init.orthogonal_,
                        lambda x: nn.init.constant_(x, 0),
                        nn.init.calculate_gain('relu'),
                        noisy_layer=self.noisy_nets)
            self.fc1 = init_(nn.Linear(self.feature_size(input_shape), self.gru_size)) if not self.noisy_nets else init_(NoisyLinear(self.feature_size(input_shape), self.gru_size, sigma_init))

        init_ = lambda m: self.layer_init(m, nn.init.orthogonal_,
                    lambda x: nn.init.constant_(x, 0), gain=1,
                    noisy_layer=self.noisy_nets)

        self.critic_linear = init_(nn.Linear(self.gru_size, 1)) if not self.noisy_nets else init_(NoisyLinear(self.gru_size, 1, sigma_init))

        init_ = lambda m: self.layer_init(m, nn.init.orthogonal_,
                    lambda x: nn.init.constant_(x, 0), gain=0.01,
                    noisy_layer=self.noisy_nets)

        self.actor_linear = init_(nn.Linear(self.gru_size, num_actions)) if not self.noisy_nets else init_(NoisyLinear(self.gru_size, num_actions, sigma_init))
        
        self.train()
        if self.noisy_nets:
            self.sample_noise()

    def forward(self, inputs, states, masks):
        x = F.relu(self.conv1(inputs))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))

        if self.use_gru:
            x = x.view(x.size(0), -1)
            if inputs.size(0) == states.size(0):
                x = F.relu(self.fc1(x))
                x = states = self.gru(x, states * masks)
            else:
                # x is a (T, N, -1) tensor that has been flatten to (T * N, -1)
                N = states.size(0)
                T = int(x.size(0) / N)

                # unflatten
                x = F.relu(self.fc1(x))
                x = x.view(T, N, x.size(1))

                # Same deal with masks
                masks = masks.view(T, N, 1)

                outputs = []
                for i in range(T):
                    hx = states = self.gru(x[i], states*masks[i])     
                    outputs.append(hx)

                # assert len(outputs) == T
                # x is a (T, N, -1) tensor
                x = torch.stack(outputs, dim=0)
                # flatten
                x = x.view(T * N, -1)
        else:
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))

        value = self.critic_linear(x)
        logits = self.actor_linear(x)

        return logits, value, states

    def layer_init(self, module, weight_init, bias_init, gain=1, noisy_layer=False):
        if not noisy_layer:
            weight_init(module.weight.data, gain=gain)
            bias_init(module.bias.data)
        else:
            weight_init(module.weight_mu.data, gain=gain)
            bias_init(module.bias_mu.data)
        return module

    def sample_noise(self):
        if self.noisy_nets:
            self.critic_linear.sample_noise()
            self.actor_linear.sample_noise()
            self.fc1.sample_noise()

    def feature_size(self, input_shape):
        return self.conv3(self.conv2(self.conv1(torch.zeros(1, *input_shape)))).view(1, -1).size(1)
    
    @property
    def state_size(self):
        if self.use_gru:
            return self.gru_size
        else:
            return 1