import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent import Agent
from my_sim.gym_simulation import *
from create_env import CreateEnv
import torch
from global_dir import root_dir

print(torch.version.cuda)
print(torch.cuda.is_available())

# Create environment
env,n_obs,n_actions,writer,config = CreateEnv(operation="train")

# Start Training 
agent1 = Agent(env,n_obs,n_actions,writer,**config)
agent2 = Agent(env,n_obs,n_actions,writer,**config)

agent1_reward = 0
agent2_reward = 0
adv_iters = config['adv_iter']

for adv_iter in range(adv_iters):
    print(f'Adversarial Episode {adv_iter+1}/{adv_iters}')

    print('Protagonist Turn')
    agent1.train_adv(adversary = agent2.rl_alg, player = "protagonist")
    print('Adversary Turn')
    agent2.train_adv(adversary = agent1.rl_alg, player = "adversary")

    # Save the model iteratively
    if ((adv_iter + 1) % config['save_every'] == 0) and adv_iter != 0:
        os.makedirs(os.path.join(root_dir,"models"), exist_ok=True)

        final_reward = round(float(agent1.total_reward/config['epochs']),5)
        model_dir = os.path.join(root_dir,"models",f"{config['gym_model']}_{agent1.rl_alg.name}_{final_reward}.pth")
        torch.save(agent1.rl_alg.state_dict(),model_dir)

        final_reward_adv = round(float(agent2.total_reward/config['epochs']),5)
        model_dir_adv = os.path.join(root_dir,"models",f"{config['gym_model']}_{agent2.rl_alg.name}_ADV_{final_reward_adv}.pth")
        torch.save(agent2.rl_alg.state_dict(),model_dir_adv)

    # Update tensorboard and terminal with mean rewards for each iteration
    writer.add_scalars("", {
        "Protagonist": agent1.total_reward/config['epochs'],
        "Adversary": agent2.total_reward/config['epochs']
    }, adv_iter)
    writer.flush()

env.close()

print("Training Complete!")