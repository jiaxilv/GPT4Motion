import os
import numpy as np
from PIL import Image


def get_freestyle_images(path):
    img_name = os.listdir(path)
    img_name.sort()
    img = [Image.open(path + "/" + i).split()[-1] for i in img_name if '.png' in i]
    return img


def get_images(path):
    img_name = os.listdir(path)
    img_name.sort()
    img = [Image.open(path + "/" + i).convert("L") for i in img_name if '.png' in i]
    return img


def get_images_nothing(path):
    img_name = os.listdir(path)
    img_name.sort()
    img = [Image.open(path + "/" + i) for i in img_name if '.png' in i]
    return img


def get_depth_images(path):
    img_name = os.listdir(path)
    img_name.sort()
    img = [Image.open(path + "/" + i).convert("L") for i in img_name if '.png' in i]
    img = [Image.fromarray(255 - np.array(dep), mode='L') for dep in img]
    return img


def get_canny(images):
    canny_images = []
    for image in tqdm(images):
        image = np.array(image.convert("L"))
        image[image > 150] = 255
        image = 255 - image
        image = Image.fromarray(image)
        canny_images.append(image)
    return canny_images


def register_attention_control(model, controller):
    attn_procs = {}
    cross_att_count = 0
    for name in model.unet.attn_processors.keys():
        if name.endswith("attn1.processor"):
            attn_procs[name] = controller(forever_keep=False)
        else:
            attn_procs[name] = controller(forever_keep=True)


    model.unet.set_attn_processor(attn_procs)


def move_index_to_zero(model):
    attn_dict = model.attn_processors
    key = list(attn_dict.keys())
    for k in key:
        attn_dict[k].index = 0
    model.set_attn_processor(attn_dict)


def set_kv_to_none(model):
    attn_dict = model.attn_processors
    key = list(attn_dict.keys())
    for k in key:
        attn_dict[k].k = []
        attn_dict[k].v = []
    model.set_attn_processor(attn_dict)
