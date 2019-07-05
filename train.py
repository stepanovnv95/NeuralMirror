import argparse
import logging
from os import path
import os
import configparser
import shutil
import hashlib
import cv2
import time


config = configparser.ConfigParser()
config.read('config.ini')
tmp_dir = config['default']['tmp_dir']


def log(msg):
    logging.info(msg)
    print(msg)


def clear_tmp():
    try:
        shutil.rmtree(tmp_dir)
    except FileNotFoundError:
        pass
    os.mkdir(tmp_dir)


def get_directory_labels(directory_path: str) -> dict:
    labels_dict = {}
    labels_file = path.join(directory_path, 'labels.txt')
    if not path.exists(labels_file) or not path.isfile(labels_file):
        return labels_dict
    with open(labels_file) as file:
        labels = list(filter(lambda x: x != '', file.read().split('\n')))
        for l in labels:
            key, value = l.split(':')
            if 'true' in value:
                labels_dict[key] = 'true'
            elif 'false' in value:
                labels_dict[key] = 'false'
    return labels_dict


def get_raw_dataset_info(data_dir: str) -> dict:

    with open(path.join(data_dir, 'labels.txt')) as labels_file:
        labels = labels_file.read()
    labels = list(filter(lambda x: x != '', labels.split('\n')))
    log(f'In {data_dir} found {len(labels)} labels: {", ".join(labels)}')
    labels = dict.fromkeys(labels)
    for l in labels:
        labels[l] = {'true': [], 'false': []}
    labels_dirs = [path.join(data_dir, x) for x in os.listdir(data_dir)]
    labels_dirs = list(filter(lambda x: path.isdir(x), labels_dirs))
    for d in labels_dirs:
        directory_labels = get_directory_labels(d)
        for l in directory_labels.keys():
            if l in labels.keys():
                labels[l][directory_labels[l]].append(d)
            else:
                log(f'Invalid label "{l}" in directory {d}')
    return labels


def remove_incomplete_labels(labels_dict: dict) -> dict:
    labels_to_remove = []
    for label in labels_dict.keys():
        if len(labels_dict[label]['true']) == 0 or len(labels_dict[label]['false']) == 0:
            labels_to_remove.append(label)
    for label in labels_to_remove:
        labels_dict.pop(label)
        log(f'Label {label} is incomplete, removed')
    log(f'{len(labels_dict.keys())} labels left: {", ".join(labels_dict.keys())}')
    return labels_dict


def expand_files_list(dirs: list) -> list:
    formats = ['png', 'jpeg', 'jpg']
    files_list = []
    for d in dirs:
        files = os.listdir(d)
        for f in files:
            if f == 'labels.txt':
                continue
            file_path = path.join(d, f)
            if file_path.split('.')[-1].lower() in formats and path.isfile(file_path):
                files_list.append(file_path)
            else:
                log(f'Not familiar image format: {file_path}')
    return files_list


def format_label(label_name, label_dict: dict) -> str or None:
    label_dict['true'] = expand_files_list(label_dict['true'])
    log(f'True: {len(label_dict["true"])}')
    label_dict['false'] = expand_files_list(label_dict['false'])
    log(f'False: {len(label_dict["false"])}')

    min_limit = 20
    if len(label_dict["true"]) < min_limit or len(label_dict["false"]) < min_limit:
        log(f'Too small dataset, need more than {min_limit} for true and false, skipped')
        return

    dir_hash_name = hashlib.sha1(label_name.encode()).hexdigest()
    os.mkdir(path.join(tmp_dir, dir_hash_name))
    dirs_to_create = [path.join(tmp_dir, dir_hash_name, x) for x in ['training', 'validation', 'testing']]
    for d in dirs_to_create:
        os.mkdir(d)
        os.mkdir(path.join(d, 'true'))
        os.mkdir(path.join(d, 'false'))

    for true_or_false_key in label_dict.keys():
        for image_path in label_dict[true_or_false_key]:
            image_hash_name = hashlib.sha1((label_name + image_path).encode()).hexdigest()
            percentage_hash = int(image_hash_name, 16) % 100
            if percentage_hash < 10:
                subdir = 'testing'
            elif percentage_hash < 20:
                subdir = 'validation'
            else:
                subdir = 'training'
            new_image_path = path.join(tmp_dir, dir_hash_name, subdir, true_or_false_key,
                                       image_hash_name + '.' + image_path.split('.')[-1].lower())
            shutil.copyfile(image_path, new_image_path)
    return path.join(tmp_dir, dir_hash_name)


def format_dataset(data_dir: str) -> list:
    raw_dataset_info = get_raw_dataset_info(data_dir)
    raw_dataset_info = remove_incomplete_labels(raw_dataset_info)
    result = []
    for key in raw_dataset_info.keys():
        log(f'Formatting dataset for {key} model')
        formatted_label_dataset = format_label(key, raw_dataset_info[key])
        if formatted_label_dataset is not None:
            result.append({
                'label': key,
                'dataset': formatted_label_dataset
            })
    log(f'{len(result)} labels left: {", ".join([x["label"] for x in result])}')
    return result


# noinspection PyUnresolvedReferences
def prepare_image(image_path: str):
    image = cv2.imread(image_path)
    height, weight, _ = image.shape
    square_size = min(height, weight)
    if weight >= height:
        offset = int((weight - height) / 2)
        image = image[:, offset:offset+square_size]
    else:
        offset = int((height - weight) / 2)
        image = image[:square_size, :]
    image = cv2.resize(image, (299, 299))
    cv2.imwrite(image_path, image)


def prepare_images(images_dir: str):
    for root, _, files in os.walk(images_dir):
        for file in files:
            image_path = path.join(root, file)
            prepare_image(image_path)


def main(data_dir: str):
    clear_tmp()
    logging.basicConfig(filename='log.log', level=logging.INFO, filemode='w')
    format_dataset(data_dir)
    log('Preparing images')
    prepare_images(tmp_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir', type=str)
    args, _ = parser.parse_known_args()
    main(args.data_dir)
