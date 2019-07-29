import os
from os import path
import shutil
import argparse
import hashlib
import random
import cv2
import numpy as np
from model.model import ClassificationModel


tmp_dir = '../tmp/'
result_dir = '../result/'
allow_formats = ['png', 'jpg', 'jpeg', 'webp']


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
        images = filter(lambda x: path.isfile(path.join(label_path, x)) and x.split('.')[-1].lower() in allow_formats,
                        images)
        raw_dataset_info[l] = {
            'images': list(images),
            'path': label_path
        }
    return raw_dataset_info


def format_label(label_name: str, label_data: dict):
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


def format_dataset(data_dir: str) -> list:
    raw_dataset_info = get_raw_dataset_info(data_dir)
    for label, images_list in raw_dataset_info.items():
        print(f'Format {label}')
        format_label(label, images_list)
    return list(raw_dataset_info.keys())


def prepare_image(image_path: str, image_size: tuple):
    image = cv2.imread(image_path)
    height, weight, _ = image.shape
    square_size = min(height, weight)
    if weight >= height:
        offset = int((weight - height) / 2)
        image = image[:, offset:offset+square_size]
    else:
        image = image[:square_size, :]
    image = cv2.resize(image, image_size)
    cv2.imwrite(image_path, image)


def prepare_images(images_dir: str, image_size: tuple):
    for root, _, files in os.walk(images_dir):
        for file in files:
            image_path = path.join(root, file)
            prepare_image(image_path, image_size)


def load_image(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image


def inf_random_generator_from_dir(images_dir: str):
    files = os.listdir(images_dir)
    while True:
        file = files[random.randint(0, len(files) - 1)]
        file = path.join(images_dir, file)
        yield load_image(file)


def limited_generator_from_dir(images_dir: str):
    files = os.listdir(images_dir)
    for file in files:
        file = path.join(images_dir, file)
        yield load_image(file)


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


def create_inf_mixer_generator(gen_list: list):
    while True:
        for gen in gen_list:
            yield gen.__next__()


def create_limited_mixer_generator(gen_list: list):
    for gen in gen_list:
        for value in gen:
            yield value


def create_data_generators(data_path: str, labels: list):
    gens = [add_label(
        add_normalization(add_distorts_generator(inf_random_generator_from_dir(
            path.join(data_path, l, 'training')
        ))),
        labels.index(l)
    ) for l in labels]
    training_generator = create_inf_mixer_generator(gens)

    gens = [add_label(
        add_normalization(limited_generator_from_dir(
            path.join(data_path, l, 'validation')
        )),
        labels.index(l)
    ) for l in labels]
    validation_generator = create_limited_mixer_generator(gens)

    gens = [add_label(
        add_normalization(limited_generator_from_dir(
            path.join(data_path, l, 'testing')
        )),
        labels.index(l)
    ) for l in labels]
    testing_generator = create_limited_mixer_generator(gens)

    return training_generator, validation_generator, testing_generator


def main(data_dir: str, model: str):
    clear_tmp()
    labels = format_dataset(data_dir)
    model = ClassificationModel(model, len(labels), True)
    print('Preparing dataset')
    prepare_images(tmp_dir, tuple(model.image_size))
    training_generator, validation_generator, testing_generator = create_data_generators(tmp_dir, labels)
    tmp_result = path.join(tmp_dir, '__result/')
    os.mkdir(tmp_result)
    model.train(training_generator, validation_generator, testing_generator, tmp_result)
    files = ['last_weights.h5', 'best_weights.h5']
    for f in files:
        shutil.copy(path.join(tmp_result, f), result_dir)
    with open(path.join(result_dir, 'labels.txt'), 'w') as labels_file:
        labels_file.write('\n'.join(labels))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir', type=str)
    parser.add_argument('--model', type=str, default='mobilenet',
                        help='The pretrained model, "mobilenet" or "inception"')
    args, _ = parser.parse_known_args()
    main(args.data_dir, args.model)
