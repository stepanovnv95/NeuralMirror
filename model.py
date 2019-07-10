import tensorflow as tf
import tensorflow_hub as hub
import os
from log import log


class InceptionBinaryModel:
    def __init__(self, label: str, trainable):
        if trainable:
            self.training_epochs = 1000
            self.training_steps_per_epochs = 100
            self.validation_steps = 50
            self.testing_steps = 50

        self.label = label.replace(' ', '_')
        self.trainable = trainable
        self.module_path = 'https://tfhub.dev/google/imagenet/inception_v3/feature_vector/3'

        my_graph = tf.Graph()
        with my_graph.as_default():
            my_session = tf.Session()
            with my_session.as_default():
                tfhub_module_url = self.module_path
                classifier_module = hub.Module(tfhub_module_url)
                image_size = hub.get_expected_image_size(classifier_module)
                image_channels = hub.get_num_image_channels(classifier_module)
                input_shape = image_size + [image_channels]
                classifier_layer = tf.keras.layers.Lambda(classifier_module, input_shape=input_shape, name='v3')

                self.model = tf.keras.Sequential()
                self.model.add(classifier_layer)
                self.model.add(tf.keras.layers.Dense(512, activation=tf.nn.relu, name='hidden1'))
                self.model.add(tf.keras.layers.Dense(64, activation=tf.nn.relu, name='hidden2'))
                if self.trainable:
                    self.model.add(tf.keras.layers.Dropout(0.2, name='dropout'))
                    self.model.add(tf.keras.layers.Dense(1, activation=tf.nn.sigmoid, name='output'))

                self.model.compile(optimizer=tf.train.AdamOptimizer(10 ** -4),
                                   loss=tf.keras.losses.binary_crossentropy,
                                   metrics=['accuracy'])

                my_session.run(tf.global_variables_initializer())

        self.graph = my_graph
        self.session = my_session

    def train(self, dataset, result_dir):
        monitor = tf.keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0.01, patience=20)
        checkpointer = tf.keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(result_dir, self.label + '_best_weights.h5'),
            save_best_only=True, save_weights_only=True
        )

        with self.graph.as_default():
            with self.session.as_default():
                self.model.fit_generator(dataset['training'],
                                         epochs=self.training_epochs, steps_per_epoch=self.training_steps_per_epochs,
                                         callbacks=[monitor, checkpointer],
                                         validation_data=dataset['validation'], validation_steps=self.validation_steps)
                self.model.save_weights(os.path.join(result_dir, self.label + '_last_weights.h5'))

                loss, accuracy = self.model.evaluate_generator(dataset['testing'], steps=self.testing_steps)
                log(f'Last weights. Loss: {loss}, Accuracy: {accuracy}')

                self.model.load_weights(os.path.join(result_dir, self.label + '_best_weights.h5'))
                loss, accuracy = self.model.evaluate_generator(dataset['testing'], steps=self.testing_steps)
                log(f'Best weights. Loss: {loss}, Accuracy: {accuracy}')
