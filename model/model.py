import tensorflow as tf
import tensorflow_hub as hub
import os


class ClassificationModel:

    def __init__(self, label_count: int, trainable: bool):
        self.label_count = label_count
        self.trainable = trainable
        self.module_path = './imagenet_mobilenet_v2_140_224_classification_3'

        self.graph = tf.Graph()
        with self.graph.as_default():
            self.session = tf.Session()
            with self.session.as_default():

                classifier_module = hub.Module(self.module_path)
                self.image_size = hub.get_expected_image_size(classifier_module)
                image_channels = hub.get_num_image_channels(classifier_module)
                input_shape = self.image_size + [image_channels]
                classifier_layer = tf.keras.layers.Lambda(classifier_module, input_shape=input_shape, name='pretrained')

                self.model = tf.keras.Sequential()
                self.model.add(classifier_layer)
                self.model.add(tf.keras.layers.Dense(512, activation=tf.nn.relu, name='hidden1'))
                self.model.add(tf.keras.layers.Dense(64, activation=tf.nn.relu, name='hidden2'))
                if self.trainable:
                    self.model.add(tf.keras.layers.Dropout(0.2, name='dropout'))
                self.model.add(tf.keras.layers.Dense(self.label_count, activation=tf.nn.softmax, name='output'))

                self.model.compile(optimizer=tf.train.AdamOptimizer(10 ** -4),
                                   loss=tf.keras.losses.sparse_categorical_crossentropy,
                                   metrics=['accuracy'])

                self.session.run(tf.global_variables_initializer())

    def train(self, training_dataset, validation_dataset, testing_dataset, result_dir: str):
        """
        :param training_dataset: Infinite generator
        :param validation_dataset: Limited generator or list
        :param testing_dataset: Limited generator or list
        :param result_dir: Directory to save weights as best_weights.h5 and last_weights.h5 files
        """
        validation_dataset, testing_dataset = list(validation_dataset), list(testing_dataset)
        training_epochs = 1000
        training_steps_per_epochs = 50 * self.label_count
        validation_steps = len(validation_dataset)
        testing_steps = len(testing_dataset)

        monitor = tf.keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0.01, patience=20)
        checkpointer = tf.keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(result_dir, 'best_weights.h5'),
            save_best_only=True, save_weights_only=True
        )

        with self.graph.as_default():
            with self.session.as_default():
                self.model.fit_generator(training_dataset,
                                         epochs=training_epochs, steps_per_epoch=training_steps_per_epochs,
                                         callbacks=[monitor, checkpointer],
                                         validation_data=validation_dataset, validation_steps=validation_steps)
                self.model.save_weights(os.path.join(result_dir, 'last_weights.h5'))

                loss, accuracy = self.model.evaluate_generator(testing_dataset, steps=testing_steps)
                print(f'Last weights. Loss: {loss}, Accuracy: {accuracy}')
                self.model.load_weights(os.path.join(result_dir, 'best_weights.h5'))
                loss, accuracy = self.model.evaluate_generator(testing_dataset, steps=testing_steps)
                print(f'Best weights. Loss: {loss}, Accuracy: {accuracy}')

    def load(self, weights_file):
        with self.graph.as_default():
            with self.session.as_default():
                self.model.load_weights(weights_file)

    def predict(self, image):
        with self.graph.as_default():
            with self.session.as_default():
                result = self.model.predict(image, batch_size=1)
        return result
