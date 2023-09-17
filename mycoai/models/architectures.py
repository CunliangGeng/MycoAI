'''Several architectures that handle ITS data. Must output a flat tensor.'''

import torch
from .transformer import Transformer

class SimpleCNN(torch.nn.Module):
    
    def __init__(self, first_kernel, conv_layers, pool_size=3):
        '''A simple CNN architecture with conv, batchnorm and maxpool layers'''
        super().__init__()

        conv = []
        in_channels = 4
        for i in range(len(conv_layers)):
            kernel = 3 if i > 0 else first_kernel
            out_channels = conv_layers[i]
            conv.append(torch.nn.Conv1d(in_channels, out_channels, kernel, 
                                        padding='same'))
            conv.append(torch.nn.ReLU())
            conv.append(torch.nn.BatchNorm1d(out_channels))
            conv.append(torch.nn.MaxPool1d(3, 1))
            in_channels = out_channels
        self.conv = torch.nn.ModuleList(conv)
    
    def forward(self, x):
        for layer in self.conv:
            x = layer(x)
        x = torch.flatten(x, 1)
        return x

class ResNet(torch.nn.Module):
    '''Adapted from: 
    https://blog.paperspace.com/writing-resnet-from-scratch-in-pytorch/'''
    
    def __init__(self, layers):
        super().__init__()
        self.inplanes = 64
        self.conv1 = torch.nn.Sequential(
            torch.nn.Conv1d(4, 64, kernel_size=7, stride=2, padding=3),
            torch.nn.BatchNorm1d(64), torch.nn.ReLU())
        self.maxpool = torch.nn.MaxPool1d(kernel_size=3, stride=2, padding=1)
        block = ResidualBlock
        self.layer0 = self._make_layer(block, 64, layers[0], stride=1)
        self.layer1 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer2 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer3 = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool = torch.nn.AvgPool1d(7, stride=1)
        
    def _make_layer(self, block, planes, blocks, stride=1):

        downsample = None
        if stride != 1 or self.inplanes != planes:
            downsample = torch.nn.Sequential(
                torch.nn.Conv1d(self.inplanes, planes, kernel_size=1, 
                                stride=stride),
                torch.nn.BatchNorm1d(planes))
        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return torch.nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.maxpool(x)
        x = self.layer0(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        return x

class ResidualBlock(torch.nn.Module):
  '''Adapted from: 
  https://blog.paperspace.com/writing-resnet-from-scratch-in-pytorch/'''

  def __init__(self, in_channels, out_channels, stride=1, downsample = None):
    super(ResidualBlock, self).__init__()
    self.conv1 = torch.nn.Sequential(
        torch.nn.Conv1d(in_channels, out_channels, kernel_size=3, stride=stride, 
                        padding=1),
        torch.nn.BatchNorm1d(out_channels), torch.nn.ReLU())
    self.conv2 = torch.nn.Sequential(
        torch.nn.Conv1d(out_channels, out_channels, kernel_size=3, stride=1, 
                        padding=1),
        torch.nn.BatchNorm1d(out_channels))
    self.downsample = downsample
    self.relu = torch.nn.ReLU()
    self.out_channels = out_channels
        
  def forward(self, x):
    residual = x
    out = self.conv1(x)
    out = self.conv2(out)
    if self.downsample:
        residual = self.downsample(x)
    out += residual
    out = self.relu(out)
    return out