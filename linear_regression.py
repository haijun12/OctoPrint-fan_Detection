from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pandas as pd
from sklearn import metrics


def run_LR(data):
    """
            Linear Regression Model with sklearn

            Conducts Training and Testing of the Linear Regression Model for
            predicting Surface Roughness

            x contain columns: infill density, layer height, and fan speed
            y contain column: surface roughness
    """
    x = data.iloc[:, 0:3]
    y = data.iloc[:, 3:4]

    x_train, x_test, y_train, y_true = train_test_split(x, y, test_size=0.20, random_state=100)

    model_lr = LinearRegression().fit(x_train, y_train)
    print(model_lr.coef_)
    print(model_lr.intercept_)

    y_pred = model_lr.predict(x_test)

    print('Error Analysis of Linear Regression')
    print('*******************************************************')
    print('Mean Absolute Error:', metrics.mean_absolute_error(y_pred, y_true))
    print('Mean Squared Error:', metrics.mean_squared_error(y_pred, y_true))

    print('Mean Squared Error:', metrics.mean_squared_error(y_pred, y_true))


def main():
    print("TOP/BOTTOM CALCULATIONS")
    print('*******************************************************')
    df = pd.read_csv('3d_printer_data_top.csv')
    run_LR(df)
    print("SIDE CALCULATIONS")
    print('*******************************************************')
    df = pd.read_csv('3d_printer_data_side.csv')
    run_LR(df)


if __name__ == "__main__":
    main()
