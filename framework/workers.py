#!/usr/bin/env python
# coding=utf-8
'''
Author: JiangJi
Email: johnjim0816@gmail.com
Date: 2023-05-07 18:30:46
LastEditor: JiangJi
LastEditTime: 2023-05-08 23:50:45
Discription: 
'''
import ray

@ray.remote(num_cpus=1)
class Worker:
    def __init__(self, cfg, id = None, env = None, policy = None):
        self.cfg = cfg
        self.id = id # interactor id
        self.worker_seed = self.cfg.seed + self.id
        self.env = env
        self.local_policy = policy
    def run(self, data_server = None, learner = None, stats_recorder = None):
        while not ray.get(data_server.check_episode_limit.remote()):
            # print(f"Interactor {self.id} is running {await data_server.get_episode.remote()}")
            self.ep_reward, self.ep_step = 0, 0
            self.episode = ray.get(data_server.get_episode.remote())
            state = self.env.reset(seed = self.worker_seed)
            for _ in range(self.cfg.max_step):
                policy_params, optimizer_params = ray.get(learner.get_policy.remote()) # get policy params from learner
                self.load_policy(policy_params, optimizer_params) # load policy params to local policy
                action = self.get_action(state, data_server = data_server)
                # action = ray.get(learner.get_action.remote(state, data_server = data_server))
                next_state, reward, terminated, truncated , info = self.env.step(action)
                self.ep_reward += reward
                self.ep_step += 1
                learner.add_transition.remote((state, action, reward, next_state, terminated,info))
                self.update_policy(data_server = data_server, learner = learner)
                state = next_state
                if terminated:
                    break
            print(f"Worker {self.id} finished episode {self.episode} with reward {self.ep_reward} in {self.ep_step} steps")
            ray.get(data_server.increase_episode.remote())
            self.add_interact_summary(stats_recorder)
    def get_action(self,state, data_server = None):
        ray.get(data_server.increase_sample_count.remote())
        sample_count = ray.get(data_server.get_sample_count.remote())
        # print(f"Worker {self.id} is getting action {sample_count}")
        return self.local_policy.get_action(state,sample_count=sample_count)
    def load_policy(self,policy_params,optimizer_params):
        self.local_policy.load_policy_params(policy_params)
        self.local_policy.load_optimizer_params(optimizer_params)
    def update_policy(self,data_server = None, learner = None):
        training_data = ray.get(learner.get_training_data.remote())
        if training_data is not None:
            # policy_params, optimizer_params = ray.get(learner.get_policy.remote()) # get policy params from learner
            # self.load_policy(policy_params, optimizer_params) # load policy params to local policy
            ray.get(data_server.increase_update_step.remote())
            self.update_step = ray.get(data_server.get_update_step.remote())
            self.local_policy.update(**training_data,update_step=self.update_step)
            policy_params, optimizer_params = self.local_policy.get_policy_params(), self.local_policy.get_optimizer_params()
            learner.set_policy.remote(policy_params, optimizer_params) # set policy params to learner
    def add_interact_summary(self,stats_recorder):
        summary = {
            'reward': self.ep_reward,
            'step': self.ep_step
        }
        stats_recorder.add_interact_summary.remote((self.episode,summary))
    