#!/usr/bin/env python
# coding=utf-8
'''
Author: JiangJi
Email: johnjim0816@gmail.com
Date: 2023-04-13 00:10:26
LastEditor: JiangJi
LastEditTime: 2023-05-17 12:41:08
Discription: 
'''
from config.config import DefaultConfig

class EnvConfig(DefaultConfig):
    def __init__(self) -> None:
        super().__init__()
        self.id = "CartPole-v1" # 环境名称
        self.render_mode = None # render mode: None, rgb_array, human
        self.wrapper = None # 
        self.ignore_params = ["wrapper", "ignore_params"]