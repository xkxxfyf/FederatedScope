import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.backends.cudnn as cudnn
import torchvision
import torchvision.transforms as T
import torchvision.transforms.functional as TF
from torch.utils.data import DataLoader, Dataset
from torchvision.datasets import CIFAR10, CIFAR100
import pickle as pkl
import numpy as np
from federatedscope.register import register_data
from federatedscope.core.auxiliaries.splitter_builder import get_splitter



class SimCLRTransform():
    def __init__(self, is_sup, image_size=32):
        self.transform = T.Compose([
            T.RandomResizedCrop(image_size, scale=(0.5, 1.0), interpolation=T.InterpolationMode.BICUBIC),
            T.RandomHorizontalFlip(p=0.5),
            T.RandomApply([T.ColorJitter(0.4,0.4,0.2,0.1)], p=0.8),
            T.RandomGrayscale(p=0.2),
            T.RandomApply([T.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0))], p=0.5),
            T.ToTensor(),
            T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])

        self.mode = is_sup

    def __call__(self, x):
        if(self.mode):
            return self.transform(x)
        else:
            x1 = self.transform(x)
            x2 = self.transform(x)
            return x1, x2 

def Cifar4CL(config):
    
    transform_train = SimCLRTransform(is_sup=False, image_size=32)

    path = config.data.root
    
    data_train = CIFAR10(path, train=True, download=True, transform=transform_train)
#     data_val = CIFAR10(path, train=True, download=True, transform=transform_train)
    data_test = CIFAR10(path, train=False, download=True, transform=transform_train)
    
    # Split data into dict
    data_dict = dict()

    # Splitter
    splitter = get_splitter(config)
    data_train = splitter(data_train)
    data_val = data_train
    data_test = splitter(data_test)


    client_num = min(len(data_train), config.federate.client_num
                     ) if config.federate.client_num > 0 else len(data_train)
    config.merge_from_list(['federate.client_num', client_num])

    
    for client_idx in range(1, client_num + 1):
        dataloader_dict = {
              'train':
              DataLoader(data_train[client_idx - 1],
                         config.data.batch_size,
                         shuffle=config.data.shuffle,
                         num_workers=config.data.num_workers),
              'val':
              DataLoader(data_val[client_idx - 1],
                         config.data.batch_size,
                         shuffle=False,
                         num_workers=config.data.num_workers),
              'test':
              DataLoader(data_test[client_idx - 1],
                         config.data.batch_size,
                         shuffle=False,
                         num_workers=config.data.num_workers),
          }
        data_dict[client_idx] = dataloader_dict

    config = config
    return data_dict, config

def Cifar4LP(config):
    
    transform_train = T.Compose([
            T.RandomResizedCrop(32, scale=(0.5, 1.0), interpolation=T.InterpolationMode.BICUBIC),
            T.RandomHorizontalFlip(p=0.5),
            T.ToTensor(),
            T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])
    transform_test = T.Compose([
        T.ToTensor(), 
        T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    )

    path = config.data.root
    
    data_train = CIFAR10(path, train=True, download=True, transform=transform_train)
    data_val = CIFAR10(path, train=True, download=True, transform=transform_test)
    data_test = CIFAR10(path, train=False, download=True, transform=transform_test)
    
          # Split data into dict
    data_dict = dict()

    # Splitter
    splitter = get_splitter(config)
    data_train = splitter(data_train)
    data_val = splitter(data_val)
    data_test = splitter(data_test)


    client_num = min(len(data_train), config.federate.client_num
                     ) if config.federate.client_num > 0 else len(data_train)
    config.merge_from_list(['federate.client_num', client_num])

    
    for client_idx in range(1, client_num + 1):
        dataloader_dict = {
              'train':
              DataLoader(data_train[client_idx - 1],
                         config.data.batch_size,
                         shuffle=config.data.shuffle,
                         num_workers=config.data.num_workers),
              'val':
              DataLoader(data_val[client_idx - 1],
                         config.data.batch_size,
                         shuffle=False,
                         num_workers=config.data.num_workers),
              'test':
              DataLoader(data_test[client_idx - 1],
                         config.data.batch_size,
                         shuffle=False,
                         num_workers=config.data.num_workers),
          }
        data_dict[client_idx] = dataloader_dict
        
    config = config
    return data_dict, config



def load_cifar_dataset(config):
    if config.data.type == "Cifar4CL":
        data, modified_config = Cifar4CL(config)
        return data, modified_config
    elif config.data.type == "Cifar4LP":
        data, modified_config = Cifar4LP(config)
        return data, modified_config


register_data("Cifar4CL", load_cifar_dataset)
register_data("Cifar4LP", load_cifar_dataset)
