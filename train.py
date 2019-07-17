import argparse
from os import path
import os
import configparser
import shutil
import hashlib
import cv2
import random
import numpy as np
from log import log
from model import InceptionModel
# from matplotlib import pyplot


config = configparser.ConfigParser()
config.read('config.ini')
tmp_dir = config['default']['tmp_dir']
allow_formats = ['png', 'jpeg', 'jpg']


min_limit = 30


def clear_tmp():
    try:
        shutil.rmtree(tmp_dir)
    except FileNotFoundError:
        pass
    os.mkdir(tmp_dir)


def get_raw_dataset_info(data_dir: str) -> dict:
    labels = os.listdir(data_dir)
    labels = filter(lambda x: path.isdir(path.join(data_dir, x)) and x[:2] != '__', labels)
    raw_dataset_info = {}
    for l in labels:
        label_path = path.join(data_dir, l)
        images = os.listdir(label_path)
        images = filter(lambda x: path.isfile(path.join(label_path, x))  and x.split('.')[-1] in allow_formats, images)
        raw_dataset_info[l] = {
            'images': list(images),
            'path': label_path
        }
    return raw_dataset_info


def format_label(label_name, label_data: dict):
    tmp_label_dir = path.join(tmp_dir, label_name)
    os.mkdir(tmp_label_dir)
    for d in ['training', 'validation', 'testing']:
        os.mkdir(path.join(tmp_label_dir, d))
    for image_name in label_data['images']:
        image_hash_name = hashlib.sha1((os.path.join(label_data['path'], image_name)).encode()).hexdigest()
        percentage_hash = int(image_hash_name, 16) % 100
        if percentage_hash < 10:
            subdir = 'testing'
        elif percentage_hash < 20:
            subdir = 'validation'
        else:
            subdir = 'training'
        new_image_path = path.join(tmp_label_dir, subdir, image_hash_name + '.' + image_name.split('.')[-1])
        shutil.copyfile(path.join(label_data['path'], image_name), new_image_path)

    # for true_or_false_key in label_dict.keys():
    #     for image_path in label_dict[true_or_false_key]:
    #         image_hash_name = hashlib.sha1((label_name + image_path).encode()).hexdigest()
    #         percentage_hash = int(image_hash_name, 16) % 100
    #         if percentage_hash < 10:
    #             subdir = 'testing'
    #         elif percentage_hash < 20:
    #             subdir = 'validation'
    #         else:
    #             subdir = 'training'
    #         new_image_path = path.join(tmp_dir, dir_hash_name, subdir, true_or_false_key,
    #                                    image_hash_name + '.' + image_path.split('.')[-1].lower())
    #         shutil.copyfile(image_path, new_image_path)
    # return path.join(tmp_dir, dir_hash_name)


def format_dataset(data_dir: str) -> list:
    raw_dataset_info = get_raw_dataset_info(data_dir)
    for label, images_list in raw_dataset_info.items():
        log(f'Format {label}')
        format_label(label, images_list)
    return list(raw_dataset_info.keys())


def prepare_image(image_path: str):
    image = cv2.imread(image_path)
    height, weight, _ = image.shape
    square_size = min(height, weight)
    if weight >= height:
        offset = int((weight - height) / 2)
        image = image[:, offset:offset+square_size]
    else:
        image = image[:square_size, :]
    # image = cv2.resize(image, (299, 299))
    image = cv2.resize(image, (224, 224))
    cv2.imwrite(image_path, image)


def prepare_images(images_dir: str):
    for root, _, files in os.walk(images_dir):
        for file in files:
            image_path = path.join(root, file)
            prepare_image(image_path)


def create_generator_from_dir(directory: str):
    files = list(filter(lambda x: x.split('.')[-1].lower() in allow_formats, os.listdir(directory)))
    while True:
        file = files[random.randint(0, len(files)-1)]
        file = path.join(directory, file)
        image = cv2.imread(file)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        yield image


def add_distorts_generator(gen):
    for image in gen:
        if random.random() < 0.5:
            image = cv2.flip(image, 1)
        if random.random() < 0.5:
            image = image * (0.5 + random.random())
            _, image = cv2.threshold(image, 255, 255, cv2.THRESH_TRUNC)
        yield image


def add_normalization(image_gen):
    for image in image_gen:
        image = image / 255.0
        yield np.expand_dims(image, axis=0)


def add_label(gen, label):
    for d in gen:
        yield d, np.expand_dims(label, axis=0)


def create_mixer_generator(gen_list: list):
    while True:
        for gen in gen_list:
            yield gen.__next__()


def create_data_generator(data_path: str, labels):
    generators = {}
    for key in ['training', 'validation', 'testing']:
        generators[key] = create_mixer_generator([
            add_label(add_normalization(add_distorts_generator(
                create_generator_from_dir(path.join(data_path, label, key))
            )), labels.index(label)) for label in labels
        ])
    return generators


def main(data_dir: str):
    clear_tmp()
    labels = format_dataset(data_dir)
    log('Preparing images')
    prepare_images(tmp_dir)
    dgens = create_data_generator(tmp_dir, labels)
    model = InceptionModel(len(labels), True)
    model.train(dgens, './result/')
    # clear_tmp()
    with open('./result/labels.txt', 'w') as labels_file:
        labels_file.write('\n'.join(labels))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir', type=str)
    args, _ = parser.parse_known_args()
    main(args.data_dir)
