import numpy as np
import matplotlib.pyplot as plt
import json

def read_json_file(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
        return data

def read_json_variables(data):
    connections = np.array(data.get("connections", []))
    T = np.array(data.get("T", []))
    return connections, T

def solve_heat_equation(connections, T):
    n_points = len(connections)
    A = np.zeros((n_points, n_points))
    b = np.zeros(n_points)

    for i in range(n_points):
        A[i, i] = -4
        for j in range(4):
            neighbor = connections[i][j]
            if neighbor != 0:
                A[i, neighbor-1] = 1
        b[i] = -T[i][1]

    for i in range(n_points):
        if T[i][0] == 1:
            A[i, :] = 0
            A[i, i] = 1
            b[i] = T[i][1]

    temperature = np.linalg.solve(A, b)
    return temperature

def plot_temperature(temperature, connections):
    x = np.arange(1, len(temperature) + 1)
    y = np.zeros_like(x)

    for i in range(len(connections)):
        y[i] = temperature[i]

    plt.plot(x, y, marker='o', linestyle='-', color='r')
    plt.xlabel('Ponto')
    plt.ylabel('Temperatura')
    plt.title('Temperatura por ponto')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    input_data = read_json_file("input.json")
    connections = input_data['connections']
    T = input_data['T']

    temperature = solve_heat_equation(connections, T)
    print("Temperature distribution:", temperature)

    plot_temperature(temperature, connections)