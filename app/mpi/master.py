from mpi4py import MPI
import numpy as np
import pandas as pd

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

def distribute(data):

    res = []
    print(f"Proceso {rank} recibió {len(data)} elementos")
  
    miny = 13.667338
    minx = -118.608398
    maxy = 33.063924 - miny
    maxx = -84.682617 - minx

    for item in data:
        lat = item.get("lat")
        lon = item.get("lng")
        dir = item.get("dir")


        x = (lon - minx) * 100 / maxx
        y = (lat - miny) * 100 / maxy

        res.append({
            "x": x,
            "y": y,
            "direccion": dir 
        })
        # print( (lat - miny) * 100 / maxy , (lon - minx) * 100 / maxx, dir)
    return res  

def collect(data):
    result = comm.gather(data, root=0)


# solo rank 0 tendrá todos los resultados
    if rank == 0:

        # flatten
        final = []

        for part in result:
            final.extend(part)

        print("Resultado total:", len(final))
        df = pd.DataFrame(final)

        df.to_csv("dashboard/datos.csv", index=False)


        return df 
