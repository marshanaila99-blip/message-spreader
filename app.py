import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
st.set_page_config(page_title="Message Spreader", page_icon="🌌", layout="wide")
st.markdown("""
<style>
h1 {
    background: linear-gradient(90deg, #7C5CFF, #00F5D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}
div.stButton > button {
    border: 1px solid #7C5CFF;
    border-radius: 12px;
    box-shadow: 0 0 12px rgba(124, 92, 255, 0.45);
}
</style>
""", unsafe_allow_html=True)
st.title("Message Spreader")
st.caption("Dataset: Padgett Florentine Families (Netzschleuder), "
           "layer pernikahan")

LAYER = 1   # 1 = pernikahan, 2 = bisnis (lihat gprops.csv)

# ---------- 1. Baca data ----------
def muat_data(layer):
    nodes = pd.read_csv("nodes.csv", skiprows=1, header=None,
                        usecols=[0, 1], names=["index", "name"])
    edges = pd.read_csv("edges.csv", skiprows=1, header=None,
                        names=["source", "target", "weight", "layer"])
    peta = dict(zip(nodes["index"], nodes["name"].str.strip().str.title()))
    e = edges[edges["layer"] == layer]
    G = nx.Graph()
    G.add_nodes_from(peta.values())
    G.add_edges_from(zip(e["source"].map(peta), e["target"].map(peta)))
    return G, nodes, edges

G, nodes, edges = muat_data(LAYER)

with st.expander("Cek data"):
    st.write(f"Titik (keluarga): **{G.number_of_nodes()}**, "
             f"sisi (pernikahan): **{G.number_of_edges()}**")
    st.write("Hubungan di file per layer:",
             edges["layer"].value_counts().sort_index().to_dict())
    st.dataframe(pd.DataFrame(sorted(tuple(sorted(x)) for x in G.edges),
                              columns=["Keluarga 1", "Keluarga 2"]),
                 hide_index=True)

# ---------- 2. BFS per lapisan ----------
def bfs_layers(G, source):
    """layers[k] = keluarga yang menerima kabar di putaran k."""
    visited = {source}
    layers = [[source]]
    while True:
        next_layer = []
        for u in layers[-1]:
            for v in G.neighbors(u):
                if v not in visited:      # mencegah dihitung dua kali
                    visited.add(v)
                    next_layer.append(v)
        if not next_layer:
            break
        layers.append(sorted(next_layer))
    unreached = sorted(set(G.nodes) - visited)
    return layers, unreached

# ---------- 3. Tampilan ----------
pengirim = st.selectbox("Pilih pengirim awal", sorted(G.nodes))
layers, unreached = bfs_layers(G, pengirim)

total = 0
baris = []
for k, layer in enumerate(layers):
    total += len(layer)
    baris.append({
        "Putaran": k,
        "Penerima baru": ", ".join(layer),
        "Jumlah baru": len(layer),
        "Total penerima": total,
    })
st.dataframe(pd.DataFrame(baris), hide_index=True)

st.write(f"**Tidak terjangkau ({len(unreached)}):** "
         + (", ".join(unreached) if unreached else "-"))

# ---------- 4. Validasi ----------
semua = [n for L in layers for n in L]
ok1 = len(semua) == len(set(semua))
ok2 = all(
    any(G.has_edge(u, v) for u in layers[k - 1])
    for k in range(1, len(layers)) for v in layers[k]
)
jarak = nx.single_source_shortest_path_length(G, pengirim)
ok3 = all(jarak[v] == k for k, L in enumerate(layers) for v in L)

st.subheader("Validasi")
st.write("Tidak ada keluarga dihitung dua kali:", "✅" if ok1 else "❌")
st.write("Tiap penerima terhubung dari putaran sebelumnya:", "✅" if ok2 else "❌")
st.write("Nomor putaran sama dengan jarak terpendek:", "✅" if ok3 else "❌")
# ---------- 5. Gambar graf (posisi tetap) ----------
@st.cache_data
def hitung_posisi(daftar_sisi, daftar_titik):
    H = nx.Graph()
    H.add_nodes_from(daftar_titik)
    H.add_edges_from(daftar_sisi)
    utama = H.subgraph(max(nx.connected_components(H), key=len))
    p = nx.spring_layout(utama, seed=7, k=1.6, iterations=300)
    xs = [v[0] for v in p.values()]
    ys = [v[1] for v in p.values()]
    for n in H.nodes:
        if n not in p:                      # keluarga tanpa hubungan (Pucci)
            p[n] = (min(xs) - 0.25, max(ys))  # taruh di pojok, dekat graf
    return p

pos = hitung_posisi(tuple(G.edges), tuple(G.nodes))

WARNA = ["#FF4D6D", "#FFB703", "#2EE59D", "#38BDF8", "#B388FF", "#00F5D4"]
ABU = "#4A5078"

def gambar_graf(G, pos, layers, putaran):
    import random
    putaran_node = {n: k for k, L in enumerate(layers) for n in L}

    aktif = set()
    for k in range(1, min(putaran, len(layers) - 1) + 1):
        for v in layers[k]:
            for u in layers[k - 1]:
                if G.has_edge(u, v):
                    aktif.add(frozenset((u, v)))
                    break

    bx, by, jx, jy = [], [], [], []
    for u, v in G.edges:
        if frozenset((u, v)) in aktif:
            jx += [pos[u][0], pos[v][0], None]
            jy += [pos[u][1], pos[v][1], None]
        else:
            bx += [pos[u][0], pos[v][0], None]
            by += [pos[u][1], pos[v][1], None]

    # bintang latar (posisi tetap karena seed tetap)
    rnd = random.Random(3)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    sx = [rnd.uniform(min(xs) - 0.4, max(xs) + 0.4) for _ in range(80)]
    sy = [rnd.uniform(min(ys) - 0.4, max(ys) + 0.4) for _ in range(80)]

    fig = go.Figure([
        go.Scatter(x=sx, y=sy, mode="markers", hoverinfo="none",
                   showlegend=False,
                   marker=dict(size=[rnd.choice([2, 3, 4]) for _ in sx],
                               color="white", opacity=0.45)),
        go.Scatter(x=bx, y=by, mode="lines", hoverinfo="none",
                   line=dict(width=1.2, color="rgba(160,170,220,0.30)"),
                   showlegend=False),
        go.Scatter(x=jx, y=jy, mode="lines", hoverinfo="none",
                   line=dict(width=12, color="rgba(0,245,212,0.18)"),
                   showlegend=False),
        go.Scatter(x=jx, y=jy, mode="lines", hoverinfo="none",
                   line=dict(width=3.5, color="#00F5D4"),
                   showlegend=False),
    ])

    def tambah(isi, warna, nama):
        ukuran = [18 + 3 * G.degree(n) for n in isi]
        # lapisan cahaya (glow)
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in isi], y=[pos[n][1] for n in isi],
            mode="markers", hoverinfo="none", showlegend=False,
            marker=dict(size=[s * 1.9 for s in ukuran],
                        color=warna, opacity=0.22)))
        # bulatan utama
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in isi], y=[pos[n][1] for n in isi],
            mode="markers+text", text=isi, textposition="bottom center",
            textfont=dict(size=13, color="#E8EAFF"),
            marker=dict(size=ukuran, color=warna,
                        line=dict(width=2, color="rgba(255,255,255,0.85)")),
            hovertext=[f"{n}<br>Hubungan: {G.degree(n)}" for n in isi],
            hoverinfo="text", name=nama))

    for k in range(min(putaran, len(layers) - 1) + 1):
        tambah(layers[k], WARNA[k % len(WARNA)],
               "Pengirim awal" if k == 0 else f"Putaran {k}")

    sisa = [n for n in G.nodes
            if n not in putaran_node or putaran_node[n] > putaran]
    tambah(sisa, ABU, "Belum menerima")

    fig.update_layout(
        height=680, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        plot_bgcolor="#0E1330", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, Arial", color="#E8EAFF"),
        legend=dict(orientation="h", y=-0.02),
    )
    return fig

st.subheader("Simulasi penyebaran")

maks = len(layers) - 1
if "putaran" not in st.session_state:
    st.session_state.putaran = 0
if st.session_state.get("pengirim_lama") != pengirim:
    st.session_state.putaran = 0            # ganti pengirim -> mulai dari awal
    st.session_state.pengirim_lama = pengirim

k1, k2, k3 = st.columns([1, 1, 3])
if k1.button("Langkah berikutnya", disabled=st.session_state.putaran >= maks):
    st.session_state.putaran += 1
    st.rerun()
if k2.button("Reset"):
    st.session_state.putaran = 0
    st.rerun()

p = st.session_state.putaran
tahu = sum(len(layers[i]) for i in range(p + 1))
k3.write(f"**Putaran {p} dari {maks}** | sudah menerima: {tahu} dari {G.number_of_nodes()} keluarga")

st.plotly_chart(gambar_graf(G, pos, layers, p), use_container_width=True)
# ---------- 6. Skenario 2: hapus satu hubungan ----------
st.subheader("Skenario 2: hapus satu hubungan")

daftar = sorted(tuple(sorted(x)) for x in G.edges)
pilihan = st.selectbox("Hubungan yang dihapus", daftar,
                       index=daftar.index(("Medici", "Salviati"))
                       if ("Medici", "Salviati") in daftar else 0,
                       format_func=lambda x: f"{x[0]} - {x[1]}")

G2 = G.copy()
G2.remove_edge(*pilihan)
layers2, unreached2 = bfs_layers(G2, pengirim)

def ringkas(L, tak):
    return {
        "Jumlah putaran": len(L) - 1,
        "Keluarga terjangkau": sum(len(x) for x in L),
        "Tidak terjangkau": len(tak),
    }

a, b = ringkas(layers, unreached), ringkas(layers2, unreached2)
st.write(f"Pengirim: **{pengirim}**, hubungan dihapus: "
         f"**{pilihan[0]} - {pilihan[1]}**")
st.dataframe(pd.DataFrame({
    "Ukuran": list(a.keys()),
    "Sebelum": list(a.values()),
    "Sesudah": list(b.values()),
}), hide_index=True)

baru = sorted(set(unreached2) - set(unreached))
st.write("**Keluarga yang jadi tidak terjangkau karena hubungan ini dihapus:** "
         + (", ".join(baru) if baru else "tidak ada"))

# tabel putaran sesudah
total2, baris2 = 0, []
for k, L in enumerate(layers2):
    total2 += len(L)
    baris2.append({"Putaran": k, "Penerima baru": ", ".join(L),
                   "Jumlah baru": len(L), "Total penerima": total2})
st.dataframe(pd.DataFrame(baris2), hide_index=True)