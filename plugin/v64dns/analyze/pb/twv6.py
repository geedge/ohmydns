import pandas as pd
from rich.progress import Progress

from analyzer import node

data = []
with Progress() as p:
    inputdata = "./53openIPv6.txt"
    outpath = "./53openIPv6dnsTW.csv"
    # inputdata = "./TW_v6resolver.txt"
    # outpath = "./TW_v6resolver.csv"
    print(len(open(inputdata).readlines()))
    task = p.add_task("[blue]Working...", total=sum(1 for _ in open(inputdata)))
    with open(inputdata, "r") as f:
        while True:
            l = f.readline()
            if l == "":
                break
            ip6 = l.splitlines()[0]
            n = node(ip6)
            p.update(task, advance=1, refresh=True)
            if n.prov == "Taiwan":
                data.append({"ip": n.ip,
                             "owner": n.owner,
                             "isp": n.isp,
                             "area": n.prov,
                             "asn": n.AS,
                             "lat": n.lat,
                             "lng": n.lng,
                             "type": "开放解析器"})
d = pd.DataFrame(data)
d.to_csv(outpath, index=False)
