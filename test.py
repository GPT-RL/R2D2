import os
import random
import multiprocessing as mp
import torch
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
from model import Network
from environment import create_env
import config
device = torch.device('cpu')
torch.set_num_threads(4)

def test(game_name=config.game_name, save_interval = config.save_interval, test_epsilon=config.test_epsilon,
        show=False, save_plot=config.save_plot):

    env = create_env(noop_start=True, clip_rewards=False)
    test_round = 5
    pool = mp.Pool(test_round)
    x1, x2, y = [], [], []

    network = Network(env.action_space.n)
    network.to(device)
    network.share_memory()
    checkpoint = 0
    
    while os.path.exists(f'./models/{game_name}{checkpoint}.pth'):
        state_dict, training_steps, env_steps = torch.load(f'./models/{game_name}{checkpoint}.pth')
        x1.append(training_steps)
        x2.append(env_steps)
        network.load_state_dict(state_dict)

        args = [(network, env) for _ in range(test_round)]
        rewards = pool.map(test_one_case, args)

        print(' training_steps: {}' .format(training_steps))
        print(' env_steps: {}' .format(env_steps))
        print(' average reward: {}\n' .format(sum(rewards)/test_round))
        y.append(sum(rewards)/test_round)
        checkpoint += 1
    
    plt.figure(figsize=(12, 6))
    plt.title(game_name)

    plt.subplot(1, 2, 1)
    plt.xlabel('training steps')
    plt.ylabel('average reward')
    plt.plot(x1, y)

    plt.subplot(1, 2, 2)
    plt.xlabel('environment steps')
    plt.ylabel('average reward')
    plt.plot(x2, y)

    plt.show()
    
    if save_plot:
        plt.savefig('./{}.jpg'.format(game_name))

def test_one_case(args):
    network, env = args
    obs = env.reset()
    network.reset()
    done = False
    obs_history = deque([obs for _ in range(config.frame_stack)], maxlen=config.frame_stack)
    last_action = torch.zeros((1, env.action_space.n))
    sum_reward = 0
    while not done:

        obs = np.stack(obs_history).astype(np.float32)
        obs = torch.from_numpy(obs).unsqueeze(0)
        obs = obs / 255
        action, _, _ = network.step(obs, last_action)

        if random.random() < config.test_epsilon:
            action = env.action_space.sample()

        next_obs, reward, done, _ = env.step(action)
        # print(next_obs)
        obs_history.append(next_obs)
        last_action.fill_(0)
        last_action[0, action] = 1
        sum_reward += reward

    return sum_reward



if __name__ == '__main__':
    
    test()

