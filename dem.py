import json
import numpy as np
import matplotlib.pyplot as plt

def read_json_file(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
        return data

def read_json_variables(data):
    coords = np.array(data.get("coords", []))
    connections = np.array(data.get("connections", []))
    F = np.array(data.get("F", []))
    restrs = np.array(data.get("restraints", []))
    return coords, connections, F, restrs

def output_res(results, N):
    x = np.arange(1, N + 1)
    plt.plot(x, results)
    plt.xlabel("Passos")
    plt.ylabel("Deslocamento")
    plt.title("Deslocamento em função dos passos")
    plt.show()

def main(file_path):
    json_data = read_json_file(file_path)
    coords, connections, F, restrs = read_json_variables(json_data)

    N = 600
    h = 0.00004
    ne = len(coords)
    ndofs = 2 * ne
    raio = 1.5 
    mass = 7850.0
    kspr = 210000000000.0
    selected_particle = ne - 1

    F = F.reshape((ndofs, 1))
    restrs = restrs.reshape((ndofs, 1))

    x0 = list(map(lambda elem: elem[0], coords))
    y0 = list(map(lambda elem: elem[1], coords))

    u = np.zeros((ndofs, 1))
    v = np.zeros((ndofs, 1))
    a = np.zeros((ndofs, 1))
    res = np.zeros((N,))

    fi = np.zeros((ndofs, 1))
    a[:] = (F - fi) / mass
    for i in range(N):
        v += a * (0.5 * h)
        u += v * h
        fi[:] = 0.0
        for j in range(ne):
            if restrs[2 * j] == 1:
                u[2 * j] = 0.0
            if restrs[2 * j + 1] == 1:
                u[2 * j + 1] = 0.0
            xj = x0[j] + u[2 * j]
            yj = y0[j] + u[2 * j + 1]
            for index in range(int(connections[j, 0])):
                k = int(connections[j, index + 1]) - 1
                xk = x0[k] + u[2 * k]
                yk = y0[k] + u[2 * k + 1]
                dX = xj - xk
                dY = yj - yk
                di = np.sqrt(dX * dX + dY * dY)
                d2 = di - 2 * raio
                dx = d2 * dX / di
                dy = d2 * dY / di
                fi[2 * j] += kspr * dx
                fi[2 * j + 1] += kspr * dy
        a[:] = (F - fi) / mass
        v += a * (0.5 * h)
        res[i] = u[selected_particle]

    output_res(res, N)

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        main(sys.argv[1])
