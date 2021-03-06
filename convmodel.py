# -*- coding: utf-8 -*-

# Sample code to use string producer.
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

def one_hot(x, n):
    """
    :param x: label (int)
    :param n: number of bits
    :return: one hot code
    """
    if type(x) == list:
        x = np.array(x)
    x = x.flatten()
    o_h = np.zeros((len(x), n))
    o_h[np.arange(len(x)), x] = 1
    return o_h

num_classes = 3
batch_size = 5

# --------------------------------------------------
#
#       DATA SOURCE
#
# --------------------------------------------------

def dataSource(paths, batch_size):

    min_after_dequeue = 10
    capacity = min_after_dequeue + 3 * batch_size

    example_batch_list = []
    label_batch_list = []

    for i, p in enumerate(paths):
        filename = tf.train.match_filenames_once(p)
        filename_queue = tf.train.string_input_producer(filename, shuffle=False)
        reader = tf.WholeFileReader()
        _, file_image = reader.read(filename_queue)
        if i == 0:
            image, label = tf.image.decode_jpeg(file_image), [1., 0., 0.]# one_hot(int(i), 3) # [float(i)]
        elif i == 1:
            image, label = tf.image.decode_jpeg(file_image), [0., 1., 0.]
        else:
            image, label = tf.image.decode_jpeg(file_image), [0., 0., 1.]
        image = tf.image.resize_image_with_crop_or_pad(image, 80, 140)
        image = tf.reshape(image, [80, 140, 1])
        image = tf.to_float(image) / 255. - 0.5
        example_batch, label_batch = tf.train.shuffle_batch([image, label], batch_size=batch_size, capacity=capacity,
                                                            min_after_dequeue=min_after_dequeue)
        example_batch_list.append(example_batch)
        label_batch_list.append(label_batch)

    example_batch = tf.concat(values=example_batch_list, axis=0)
    label_batch = tf.concat(values=label_batch_list, axis=0)

    return example_batch, label_batch

# --------------------------------------------------
#
#       MODEL
#
# --------------------------------------------------


def myModel(X, reuse=False):
    with tf.variable_scope('ConvNet', reuse=reuse):
        o1 = tf.layers.conv2d(inputs=X, filters=32, kernel_size=3, activation=tf.nn.relu)
        o2 = tf.layers.max_pooling2d(inputs=o1, pool_size=2, strides=2)
        o3 = tf.layers.conv2d(inputs=o2, filters=64, kernel_size=3, activation=tf.nn.relu)
        o4 = tf.layers.max_pooling2d(inputs=o3, pool_size=2, strides=2)

        h = tf.layers.dense(inputs=tf.reshape(o4, [batch_size * 3, 18 * 33 * 64]), units=5, activation=tf.nn.relu)
        # y = tf.layers.dense(inputs=h, units=3, activation=tf.nn.sigmoid)
        y = tf.layers.dense(inputs=h, units=3, activation=tf.nn.softmax)
    return y

example_batch_train, label_batch_train = dataSource(["DATA/Avion/train/*.jpg", "DATA/Cara/train/*.jpg", "DATA/Moto/train/*.jpg"], batch_size=batch_size)
example_batch_valid, label_batch_valid = dataSource(["DATA/Avion/valid/*.jpg", "DATA/Cara/valid/*.jpg", "DATA/Moto/valid/*.jpg"], batch_size=batch_size)
#example_batch_test, label_batch_test = dataSource(["IMGR/boligrafo/test/*.jpg", "IMGR/frutosSecos/test/*.jpg", "IMGR/spiner/test/*.jpg"], batch_size=batch_size)


example_batch_train_mymodel = myModel(example_batch_train, reuse=False)
example_batch_valid_mymodel = myModel(example_batch_valid , reuse=True)
#example_batch_test_mymodel = myModel(example_batch_test , reuse=True)

cost = tf.reduce_sum(tf.square(example_batch_train_mymodel - label_batch_train))
cost_valid = tf.reduce_sum(tf.square(example_batch_valid_mymodel - label_batch_valid))
#cost_test = tf.reduce_sum(tf.square(example_batch_test_mymodel - label_batch_test))
"""
cost = tf.reduce_sum(tf.square(example_batch_train_mymodel - tf.cast(label_batch_train , dtype=tf.float32)))
cost_valid = tf.reduce_sum(tf.square(example_batch_valid_mymodel - tf.cast(label_batch_valid, dtype=tf.float32)))
cost_test = tf.reduce_sum(tf.square(example_batch_test_mymodel - tf.cast(label_batch_test, dtype=tf.float32)))
"""
optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.01).minimize(cost)

# --------------------------------------------------
#
#       TRAINING
#
# --------------------------------------------------

# Add ops to save and restore all the variables.

saver = tf.train.Saver()

with tf.Session() as sess:

    file_writer = tf.summary.FileWriter('./logs', sess.graph)

    sess.run(tf.local_variables_initializer())
    sess.run(tf.global_variables_initializer())

    # Start populating the filename queue.
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(coord=coord, sess=sess)

    error_trains = []
    error_valids = []

    for _ in range(80):
        sess.run(optimizer)
        if _ % 20 == 0:
            print ("Iteracion: ", _)
            # print(sess.run(label_batch_valid)) #Etiquetas
            # print(sess.run(example_batch_valid_mymodel))
            error_train = sess.run(cost)
            #error_valid = sess.run(cost_valid)
            print("Error train:", error_train)
            #print("Error validacion: ", error_valid)
            #error_trains.append(error_train)
            #error_valids.append(error_valid)

    #print("Error test: ", sess.run(cost_test))
    aciertos = 0

    for i in range(10):
        resultado = sess.run(example_batch_valid_mymodel)
        etiqueta = sess.run(label_batch_valid)
        # print(resultado[0])

        for res, eti in zip(resultado, etiqueta):
            # print(eti)
            # print(res)
            if np.argmax(res) == np.argmax(eti):
                aciertos += 1
        # print(aciertos)
        # print(len(etiqueta))

    print("Porcentaje de acierto: ", (aciertos/float(len(etiqueta)*10))*100)

    save_path = saver.save(sess, "./tmp/model.ckpt")
    print("Model saved in file: %s" % save_path)

    coord.request_stop()
    coord.join(threads)
"""
    plt_train, = plt.plot(error_trains, label='Error entrenamiento')
    plt_valid, = plt.plot(error_valids, label='Error validacion')
    plt.legend(handles=[plt_train,plt_valid])
    plt.xlabel("epoch")
    plt.ylabel("error")
    plt.show()
"""