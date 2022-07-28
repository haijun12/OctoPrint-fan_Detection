from sklearn.cluster import KMeans
import pandas as pd
from matplotlib import pyplot as plt

global lowest_mean


def smaller_cluster(curr_mean, curr_cluster, cluster, surface):
    """
        Returns: Smaller Cluster
    """
    global lowest_mean
    cluster_mean = cluster[surface].mean()
    if curr_mean > cluster_mean:
        lowest_mean = cluster_mean
        return cluster
    else:
        return curr_cluster


def specific_size(cluster, param, param_type):
    """
        Returns: Number of specific param setting variables in a cluster
    """
    return len(cluster[cluster[param_type] == param])


def print_percentage(num, den, phrase):
    """
        numerator / denominator -> percentage
    """
    percentage = round(num / den * 100, 2)
    print(phrase + " : " + str(percentage) + " %")


def run_Clustering(surface, df):
    """
            KMeans Clustering given 4 clusters

            Analyzes for the best cluster with lowest surface roughness,
            Prints the percentage of each printing parameter in the best cluster
            (Tells us if fan speed has an effect on best printing quality and
            which printing parameters are best)
    """
    global lowest_mean
    km = KMeans(n_clusters=4)

    y_predicted = km.fit_predict(df[[surface]])

    df['cluster'] = y_predicted
    df0 = df[df.cluster == 0]
    df1 = df[df.cluster == 1]
    df2 = df[df.cluster == 2]
    df3 = df[df.cluster == 3]

    min_cluster = df[df.cluster == 0]
    lowest_mean = df0[surface].mean()

    min_cluster = smaller_cluster(lowest_mean, min_cluster, df1, surface)
    min_cluster = smaller_cluster(lowest_mean, min_cluster, df2, surface)
    min_cluster = smaller_cluster(lowest_mean, min_cluster, df3, surface)
    print("Lowest mean is : ", lowest_mean)

    size = len(min_cluster)

    min_cluster.to_csv("top_min_cluster.csv", index=False)
    one_LH = specific_size(min_cluster, .1, 'lt')
    two_LH = specific_size(min_cluster, .2, 'lt')
    three_LH = specific_size(min_cluster, .3, 'lt')

    TWENTY_INFILL = specific_size(min_cluster, 20, 'rf')
    FIFTY_INFILL = specific_size(min_cluster, 50, 'rf')
    EIGHTY_INFILL = specific_size(min_cluster, 80, 'rf')

    ZERO_FS = specific_size(min_cluster, 0, 'fs')
    TWENTYFIVE_FS = specific_size(min_cluster, 25, 'fs')
    FIFTY_FS = specific_size(min_cluster, 50, 'fs')
    SEVENTYFIVE_FS = specific_size(min_cluster, 75, 'fs')
    HUNDRED_FS = specific_size(min_cluster, 100, 'fs')

    # PRINTING ALL THE PERCENTAGES
    print("LAYER_HEIGHT")
    print('*******************************************************')
    print_percentage(one_LH, size, "Amount for 0.1 LH")
    print_percentage(two_LH, size, "Amount for 0.2 LH")
    print_percentage(three_LH, size, "Amount for 0.3 LH")
    print("INFILL PERCENTAGE")
    print('*******************************************************')
    print_percentage(TWENTY_INFILL, size, "Amount for 20% INFILL")
    print_percentage(FIFTY_INFILL, size, "Amount for 50% INFILL")
    print_percentage(EIGHTY_INFILL, size, "Amount for 80% INFILL")
    print("FAN SPEED")
    print('*******************************************************')
    print_percentage(ZERO_FS, size, "Amount for 0% FS")
    print_percentage(TWENTYFIVE_FS, size, "Amount for 25% FS")
    print_percentage(FIFTY_FS, size, "Amount for 50% FS")
    print_percentage(SEVENTYFIVE_FS, size, "Amount for 75% FS")
    print_percentage(HUNDRED_FS, size, "Amount for 100% FS")
    # Plots Clusters in a 2D graph
    plt.plot(df0[surface], len(df0) * [0.1], "x", color='green')
    plt.plot(df1[surface], len(df1) * [0.1], "x", color='red')
    plt.plot(df2[surface], len(df2) * [0.1], "x", color='black')
    plt.plot(df3[surface], len(df3) * [0.1], "x", color='blue')
    plt.ylabel(surface)
    plt.xlabel('SR')
    plt.show()


def main():
    # Running both data's
    print("TOP/BOTTOM CALCULATIONS")
    print('*******************************************************')
    df = pd.read_csv('3d_printer_data_top.csv')
    run_Clustering("top/bottom", df)
    print("SIDE CALCULATIONS")
    print('*******************************************************')
    df = pd.read_csv('3d_printer_data_side.csv')
    run_Clustering("side", df)


if __name__ == "__main__":
    main()
