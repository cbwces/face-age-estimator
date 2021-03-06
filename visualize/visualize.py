'''
@author: cbwces
@github: https://github.com/cbwces
@contact: sknyqbcbw@gmail.com
'''
import os
import sys
import copy
import json
import yaml
import cv2
import torch
from torch import nn as nn
from torch.nn import functional as F
import numpy as np

from grad import GuidedBackpropSmoothGrad, save_as_gray_image, save_as_colormap_image, SmoothGrad
sys.path.append('..')
from network_utils import StnModule, MainModel
from image_utils import *
from image_croper import ImageCropper

f = open(sys.argv[1], 'r')
args = yaml.safe_load(f.read())
f.close()

if args['cuda'] == True:
    DEVICE = 'cuda'
else:
    DEVICE = 'cpu'

f = open(args['data_file_info'], 'r')
img_info_dict = json.load(f)
img_name_list = list(img_info_dict.keys())
f.close()

img = cv2.imread(sys.argv[2])
cropper = ImageCropper(args['data_file_info'], args['margin'], [sys.argv[2]], args['affine'], args['img_size'])
if args['affine'] == False:
    img = cropper.crop_image(img, 0)
else:
    img = cropper.affine_image(img, 0)
ori_img = copy.deepcopy(img)
if args['test_preprocess'] != None:
    for func in args['test_preprocess'].keys():
        img = augmentation_dict[func](img, args['test_preprocess'][func])
img = cv2.resize(img, (args['img_size'], args['img_size']))
img = torch.from_numpy(np.transpose(img, (2, 0, 1)) / 255.0)
img = torch.unsqueeze(img, dim=0)

if args['stn'] == True:
    stem_model = MainModel(args['backbone'], args['num_classes'])
    model = nn.Sequential(StnModule(img_size=args['img_size']), stem_model)
else:
    model = MainModel(args['backbone'], args['num_classes'])

model = model.to(DEVICE)
model.load_state_dict(torch.load(args['model_path']))
model.eval()
# sm = SmoothGrad(model, cuda=args['cuda'])
sm = GuidedBackpropSmoothGrad(model, cuda=args['cuda'])
img = img.to(DEVICE).float()
G = sm(img)
save_as_gray_image(G, ori_img, os.path.join(args['visualize_path'], "vis_"+sys.argv[2].split('/')[-1]))
# save_as_colormap_image(G, ori_img, os.path.join(args['visualize_path'], "vis_"+sys.argv[2].split('/')[-1]))
