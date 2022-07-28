from sklearn.model_selection import train_test_split
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.layers import Dense, LSTM, Bidirectional, Dropout, Add
from tensorflow.keras.regularizers import l2
from keras.models import Sequential

# global lowest_mse

def build_model():
    """
                    Builds an MLP Model with these parameters:
                    3 input layers, 6 hidden layers (128 neurons each), 1 output layer
                    Optimizer: Adam
                    Activation Function: Relu

    """
    # Build the model
    model = Sequential()
    model.add(Dense(128, input_dim=3, activation='relu', kernel_regularizer=l2(0.01), bias_regularizer=l2(0.01)))
    model.add(Dense(128, activation='relu'))
    model.add(Dense(128, activation='relu'))
    model.add(Dense(128, activation='relu'))
    model.add(Dense(128, activation='relu'))
    model.add(Dense(128, activation='relu'))
    model.add(Dense(1, activation='relu'))
    # Train the model
    model.compile(optimizer="adam", loss='mse')
    return model


# Load the data and build variables
def train_model(data, resModel):
    """
                Trains Given Model:
                x contain columns: infill density, layer height, and fan speed
                y contain column: surface roughness
    """
    x = data.iloc[:, 0:3]
    y = data.iloc[:, 3:4]
    # Set the train/test data
    x_train, x_test, y_train, y_true = train_test_split(x, y, test_size=0.2, random_state=100)
    # Conduct Training
    resModel.fit(x_train, y_train, batch_size=32, epochs=1300, verbose=0)
    # Conduct Testing
    # y_pred = resModel.predict(x_test)
    # Get the MAE for data
    # curr_mse = metrics.mean_absolute_error(y_pred, y_true)
    return resModel


# TESTING to obtain better NN Models
# def loop(surface, data, max_iter, file):
#     global lowest_mse
#     lowest_mse = 100
#     model = build_model()
#     best_model = train_model(surface, data, model)
#     for i in range(max_iter):
#         curr_model = train_model(surface, data, model)
#         if curr_model != 0:
#             best_model = curr_model
#
#     converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
#     tflite_model = converter.convert()
#     with open(file, 'wb') as f:
#         f.write(tflite_model)
#     # x = tf.lite.Interpreter(file)
#     # x.allocate_tensors()
#     # print(x.get_input_details())
#     # print(x.get_output_details())
#     print('Error Analysis of Neural Network Model')
#     print('*******************************************************')
#     print('Mean Absolute Error:', lowest_mse)

def runNN(filename, data, model):
    """
            Neural Network Prediction Model using Tensorflow

            Driver Function for creating and saving a prediction model
    """
    df = pd.read_csv(data)
    best_model = train_model(df, model)
    converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
    compressed_model = converter.convert()
    with open(filename, 'wb') as f:
        f.write(compressed_model)


def main():
    # Build the NN Model
    model = build_model()
    # Files Needed
    filename_side = 'models/nnside_model.tflite'
    filename_top = 'models/nntop_model.tflite'
    data_side = '3d_printer_data_side.csv'
    data_top = '3d_printer_data_top.csv'
    # Run to get both prediction models
    runNN(filename_side, data_side, model)
    runNN(filename_top, data_top, model)


if __name__ == "__main__":
    main()
