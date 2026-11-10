"""Genera los CSV limpios ampliados en datasets/enriched/.

Parte de los CSV limpios (nombres de columna y valores ya corregidos) y les
anade, cruzando con los *_original.csv, los atributos que se habian perdido.
No modifica ningun fichero existente.

Uso:  python build_clean.py
"""
import csv
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "enriched"


def read(path, delim, enc):
    with open(path, encoding=enc, newline="") as f:
        rows = list(csv.reader(f, delimiter=delim))
    return rows[0], rows[1:]


def write(name, header, rows):
    OUT.mkdir(exist_ok=True)
    with open(OUT / name, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"{name}: {len(rows)} filas, {len(header)} columnas")


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip().lower()


def dec(s):
    """Coma decimal -> punto."""
    return (s or "").strip().replace(",", ".")


def title_if_upper(s):
    s = (s or "").strip()
    return s.title() if s.isupper() else s


def article_first(s):
    """'Barraco (El)' -> 'El Barraco'."""
    m = re.match(r"^(.*?)\s*\((El|La|Los|Las|L'|Els|Les)\)$", s.strip(), re.I)
    return f"{m.group(2)} {m.group(1)}" if m else s


# ---------------------------------------------------------------- municipios
mh, mrows = read(BASE / "municipios/municipios.csv", ",", "utf-8")
_, morig = read(BASE / "municipios/municipios_original.csv", ";", "latin1")
assert len(mrows) == len(morig)
for a, b in zip(mrows, morig):
    assert norm(a[1]) == norm(b[0]), (a[1], b[0])

muni_out = []
by_name = {}  # nombre normalizado -> (cod_ine, nombre limpio)
for a, b in zip(mrows, morig):
    cod_ine = b[4]
    muni_out.append(a + [cod_ine, b[1], b[3], b[7], b[6], b[8],
                         dec(b[9]), dec(b[10]), dec(b[11]), dec(b[12])])
    by_name.setdefault(norm(a[1]).replace(' -', '-').replace('- ', '-'), cod_ine)
write("municipios.csv",
      mh + ["cod_ine", "cod_municipio", "cod_provincia", "entidades_locales_menores",
            "mancomunidades", "comarca", "longitud", "latitud", "coordenada_x", "coordenada_y"],
      muni_out)


# Equivalencias manuales de nombres que no coinciden con el listado de municipios
OVERRIDES = {
    "san ildefonso": "Real Sitio de San Ildefonso",
    "san ildefonso o la granja (san ildefonso)": "Real Sitio de San Ildefonso",
}


def cod_ine_for(*names):
    """Intenta resolver el cod_ine por nombre de municipio (varias variantes)."""
    for n in names:
        if not n:
            continue
        n = OVERRIDES.get(norm(n), n)
        inside = re.search(r"\((.*?)\)", n)
        cands = [n, article_first(n), re.sub(r"\s*\(.*?\)\s*", " ", n).strip()]
        if inside:  # 'Sedano (Valle de Sedano)': el municipio va entre parentesis
            cands.append(inside.group(1))
        for cand in cands:
            k = norm(cand).replace(" -", "-").replace("- ", "-")
            if k in by_name:
                return by_name[k]
    return ""


# ------------------------------------------------------------------- hoteles
hh, hrows = read(BASE / "hoteles/hoteles.csv", ",", "utf-8")
_, horig = read(BASE / "hoteles/hoteles_original.csv", ";", "latin1")
assert len(hrows) == len(horig)
hot_out = []
for a, b in zip(hrows, horig):
    assert a[0] == str(int(b[0].replace("/", ""))), (a[0], b[0])
    hot_out.append(a + [
        b[1].strip(), b[2].strip(), b[3].strip(), b[6].strip(), title_if_upper(b[7]),
        title_if_upper(b[9]), b[11 + 1].strip(), b[13].strip(), b[14].strip(), b[15].strip(),
        b[16].strip(), b[17].strip(), dec(b[19]), dec(b[20]), b[21].strip(),
        cod_ine_for(a[6], b[8]),
    ])
write("hoteles.csv",
      hh + ["tipo", "categoria", "especialidades", "codigo_postal", "provincia", "localidad",
            "telefono_2", "telefono_3", "email", "web", "q_calidad", "central_reservas",
            "longitud", "latitud", "accesible", "cod_ine"],
      hot_out)

# --------------------------------------------------------------- monumentos
gh, grows = read(BASE / "monumentos/monumentos.csv", ",", "utf-8")
_, gorig = read(BASE / "monumentos/monumentos_original.csv", ";", "utf-8-sig")
orig_by_id = {}
for b in gorig:
    orig_by_id.setdefault(b[0], b)  # primera aparicion; las repetidas son identicas
mon_out = []
for a in grows:
    b = orig_by_id[a[0]]
    cp = b[7].strip()
    cp = cp.zfill(5) if cp.isdigit() else cp
    mon_out.append(a + [
        b[3].strip(), b[4].strip(), b[5].strip(), b[6].strip(), cp, b[9].strip(),
        dec(b[11]), dec(b[10]), title_if_upper(b[12]), title_if_upper(b[14]),
        cod_ine_for(a[6], article_first(b[13]), b[13]),
    ])
write("monumentos.csv",
      gh + ["id_bien_interes_cultural", "calle", "clasificacion", "tipo_construccion",
            "codigo_postal", "periodo_historico", "longitud", "latitud", "provincia",
            "localidad", "cod_ine"],
      mon_out)

# ------------------------------------------------------------------ oficinas
oh, orows = read(BASE / "oficinas_turismo/oficinas.csv", ",", "utf-8")
_, oorig = read(BASE / "oficinas_turismo/oficinas_original.csv", ";", "utf-8-sig")
assert len(orows) == len(oorig)
ofi_out = []
for a, b in zip(orows, oorig):
    assert a[1] == b[3], (a[1], b[3])
    ofi_out.append(a + [b[0].strip(), b[2].strip(), b[5].strip(), cod_ine_for(a[6], b[1])])
write("oficinas.csv",
      oh + ["provincia", "tipo_recurso", "ambito", "cod_ine"],
      ofi_out)

# ------------------------------------------------------------------- resumen
for nombre, rows, idx in (("hoteles", hot_out, -1), ("monumentos", mon_out, -1),
                          ("oficinas", ofi_out, -1)):
    sin = sum(1 for r in rows if not r[idx])
    print(f"{nombre}: {sin} filas sin cod_ine de {len(rows)}")
