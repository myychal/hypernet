import numpy as np
from random import shuffle
from keras.utils import to_categorical
from scipy.ndimage.filters import gaussian_filter


def get_samples_per_class_indices(ground_truth):
    y = np.argmax(ground_truth, axis=1)
    labels = np.unique(y)
    samples_per_class = dict.fromkeys(labels)
    for label in labels:
        samples_per_class[label] = np.where(y == label)[0]
    return samples_per_class


def get_most_numerous_class(samples_per_class):
    max_ = -np.inf
    for label in samples_per_class:
        if len(samples_per_class[label]) > max_:
            max_ = samples_per_class[label]
    return max_


def gaussian_filter_augmentation(x_train, y_train, classes_count=None, sigma=2):
    if classes_count is None:
        classes_count = len(np.unique(np.argmax(y_train, axis=1)))
    augmented_x = []
    augmented_y = []
    samples_per_class = get_samples_per_class_indices(y_train)
    most_numerous_class = get_most_numerous_class(samples_per_class)

    for label in samples_per_class:
        to_augment = calculate_how_many_to_augment(label, most_numerous_class, samples_per_class)
        shuffle(samples_per_class[label])
        augment_with_gaussian(augmented_x, augmented_y, classes_count, label, samples_per_class,
                              sigma, to_augment, x_train)

    augmented_x = np.array(augmented_x)
    augmented_y = np.array(augmented_y)
    x_train = np.concatenate([x_train, augmented_x], axis=0)
    y_train = np.concatenate([y_train, augmented_y], axis=0)
    return x_train, y_train


def augment_with_gaussian(augmented_x, augmented_y, classes_count, label, samples_per_class, sigma,
                          to_augment, x_train):
    for augmented_sample in range(to_augment):
        original_sample = x_train[samples_per_class[label][augmented_sample], ...]
        augmented = gaussian_filter(original_sample, sigma)
        augmented_x.append(augmented)
        augmented_y.append(to_categorical([label], classes_count))


def calculate_stds_of_bands_per_class(x_train, samples_per_class):
    band_stds = dict.fromkeys(samples_per_class.keys())
    for label in samples_per_class:
        band_stds[label] = np.std(x_train[samples_per_class[label]], axis=0)
    return band_stds


def band_noise_augmentation(x_train, y_train, classes_count=None, alpha=0.25):
    if classes_count is None:
        classes_count = len(np.unique(np.argmax(y_train, axis=1)))
    augmented_x = []
    augmented_y = []
    samples_per_class = get_samples_per_class_indices(y_train)
    most_numerous_class = get_most_numerous_class(samples_per_class)
    bands_stds = calculate_stds_of_bands_per_class(x_train, samples_per_class)

    for label in samples_per_class:
        to_augment = calculate_how_many_to_augment(label, most_numerous_class, samples_per_class)
        shuffle(samples_per_class[label])
        augment_with_noise(alpha, augmented_x, augmented_y, bands_stds, classes_count, label,
                           samples_per_class, to_augment, x_train)

    augmented_x = np.array(augmented_x)
    augmented_y = np.array(augmented_y)
    x_train = np.concatenate([x_train, augmented_x], axis=0)
    y_train = np.concatenate([y_train, augmented_y], axis=0)
    return x_train, y_train


def augment_with_noise(alpha, augmented_x, augmented_y, bands_stds, classes_count, label,
                       samples_per_class, to_augment, x_train):
    for sample in range(to_augment):
        augmented = np.empty(x_train.shape[1:])
        for band in range(x_train.shape[-1]):
            noise = alpha * np.random.normal(loc=0, scale=bands_stds[label][band])
            augmented[band] = x_train[samples_per_class[label][sample]][band] + noise
        augmented_x.append(augmented)
        augmented_y.append(to_categorical([label], classes_count))


def calculate_how_many_to_augment(label, most_numerous_class, samples_per_class):
    class_count = len(samples_per_class[label])
    if class_count * 2 >= most_numerous_class:
        to_augment = most_numerous_class - class_count
    else:
        to_augment = class_count
    return to_augment
