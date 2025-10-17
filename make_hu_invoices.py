import os, random, csv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from faker import Faker
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT_DIR = "invoices_hu"
N_FILES = 12
random.seed(42)
fake = Faker("hu_HU")

FONT = "DejaVu"; FONT_BOLD = "DejaVu-Bold"
pdfmetrics.registerFont(TTFont(FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont(FONT_BOLD, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

os.makedirs(OUT_DIR, exist_ok=True)
VAT_RATES = [27, 5, 0]

def rnd_items():
    n = random.randint(1, 4)
    items = []
    for _ in range(n):
        qty = random.choice([1,2,3,5,10])
        unit = random.choice([2500,4500,9900,12500,19900,34900])
        name = random.choice([
            "Tanácsadás óradíj","Rendszerkarbantartás","Szoftver modul licenc",
            "Adatrögzítés","Helyszíni kiszállás","Oktatás (fél nap)"
        ])
        items.append((name, qty, unit))
    return items

def HUF(x): return f"{int(round(x)):,.0f}".replace(",", " ") + " Ft"

def company():
    return {
        "nev": fake.company(),
        "adoszam": f"{random.randint(10000000,99999999)}-{random.randint(1,9)}-{random.randint(10,99)}",
        "cim": f"{fake.postcode()} {fake.city()}, {fake.street_address()}",
        "iban": f"HU{random.randint(10,99)}{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}"
    }

def watermark(c, w, h):
    c.saveState(); c.setFont(FONT_BOLD, 80); c.setFillGray(0.9)
    c.translate(w/2, h/2); c.rotate(30); c.drawCentredString(0,0,"MINTA / SAMPLE"); c.restoreState()

def table(c, x, y, items, vat):
    c.setFont(FONT_BOLD, 10)
    c.drawString(x, y, "Tétel megnevezése"); c.drawString(x+90*mm, y, "Menny.")
    c.drawString(x+110*mm, y, "Egységár (nettó)"); c.drawString(x+155*mm, y, "Nettó összeg")
    c.setFont(FONT, 10); y -= 6*mm
    netto = 0
    for name, qty, unit in items:
        n = qty*unit; netto += n
        c.drawString(x, y, name)
        c.drawRightString(x+104*mm, y, f"{qty} db")
        c.drawRightString(x+150*mm, y, HUF(unit))
        c.drawRightString(x+190*mm, y, HUF(n))
        y -= 6*mm
    afa = round(netto*vat/100.0); brutto = netto + afa
    y -= 4*mm; c.setFont(FONT_BOLD, 10)
    c.drawRightString(x+190*mm, y, f"Nettó: {HUF(netto)}"); y -= 6*mm
    c.drawRightString(x+190*mm, y, f"ÁFA ({vat}%): {HUF(afa)}"); y -= 6*mm
    c.drawRightString(x+190*mm, y, f"Végösszeg (bruttó): {HUF(brutto)}")
    return int(netto), int(afa), int(brutto)

def page_A(path, H, S, B, items, vat):
    c = canvas.Canvas(path, pagesize=A4); w,h = A4; watermark(c,w,h)
    c.setFont(FONT_BOLD, 18); c.drawString(20*mm, 270*mm, "SZÁMLA")
    c.setFont(FONT, 10)
    c.drawString(20*mm,262*mm,f"Számlaszám: {H['szamla']}"); c.drawString(20*mm,256*mm,f"Kibocsátás dátuma: {H['kibocs']}")
    c.drawString(20*mm,250*mm,f"Teljesítés dátuma: {H['telj']}"); c.drawString(20*mm,244*mm,f"Fizetési határidő: {H['hatar']}")
    c.drawString(20*mm,238*mm,f"Fizetési mód: {H['fizmod']}")
    c.setFont(FONT_BOLD,12); c.drawString(20*mm,226*mm,"Eladó (Kibocsátó)")
    c.setFont(FONT,10); c.drawString(20*mm,221*mm,S["nev"]); c.drawString(20*mm,216*mm,f"Adószám: {S['adoszam']}")
    c.drawString(20*mm,211*mm,S["cim"]); c.drawString(20*mm,206*mm,f"Bankszámla (IBAN): {S['iban']}")
    c.setFont(FONT_BOLD,12); c.drawString(120*mm,226*mm,"Vevő")
    c.setFont(FONT,10); c.drawString(120*mm,221*mm,B["nev"]); c.drawString(120*mm,216*mm,f"Adószám: {B['adoszam']}")
    c.drawString(120*mm,211*mm,B["cim"]); c.setFont(FONT,10)
    c.drawString(20*mm,198*mm,f"ÁFA kulcs: {vat}%")
    netto, afa, brutto = table(c,20*mm,190*mm,items,vat)
    c.setFont(FONT,9); c.drawString(20*mm,20*mm,"Megjegyzés: Minta számla bemutató célokra.")
    c.showPage(); c.save(); return netto, afa, brutto

def page_B(path, H, S, B, items, vat):
    c = canvas.Canvas(path, pagesize=landscape(A4)); w,h = landscape(A4); watermark(c,w,h)
    c.setFont(FONT_BOLD, 18); c.drawString(15*mm, h-20*mm, "SZÁMLA"); c.setFont(FONT, 10)
    c.drawString(15*mm, h-28*mm, f"Számlaszám: {H['szamla']}  |  Kelt: {H['kibocs']}  |  Teljesítés: {H['telj']}  |  Határidő: {H['hatar']}  |  {H['fizmod']}")
    c.setFont(FONT_BOLD,12); c.drawString(15*mm,h-40*mm,"Eladó"); c.setFont(FONT,10)
    c.drawString(15*mm,h-46*mm,f"{S['nev']}  •  Adószám: {S['adoszam']}  •  {S['cim']}  •  IBAN: {S['iban']}")
    c.setFont(FONT_BOLD,12); c.drawString(15*mm,h-58*mm,"Vevő"); c.setFont(FONT,10)
    c.drawString(15*mm,h-64*mm,f"{B['nev']}  •  Adószám: {B['adoszam']}  •  {B['cim']}")
    c.setFont(FONT,10); c.drawString(15*mm,h-76*mm,f"ÁFA kulcs: {vat}%")
    netto, afa, brutto = table(c,15*mm,h-86*mm,items,vat)
    c.setFont(FONT,9); c.drawString(15*mm,10*mm,"Megjegyzés: Minta számla bemutató célokra.")
    c.showPage(); c.save(); return netto, afa, brutto

def main():
    truth=[]
    base = datetime(2024,11,5)
    for i in range(1,N_FILES+1):
        S, B = company(), company()
        items = rnd_items()
        vat = random.choice(VAT_RATES)
        issue = base + relativedelta(days=random.randint(0,120))
        perf  = issue - timedelta(days=random.randint(0,5))
        due   = issue + timedelta(days=random.choice([8,14,30]))
        H = {
            "szamla": f"ALG-{1000+i}",
            "kibocs": issue.strftime("%Y-%m-%d"),
            "telj":   perf.strftime("%Y-%m-%d"),
            "hatar":  due.strftime("%Y-%m-%d"),
            "fizmod": random.choice(["Átutalás","Készpénz","Bankkártya"])
        }
        path = os.path.join(OUT_DIR, f"szamla_{i:02d}.pdf")
        netto, afa, brutto = (page_B if i%2 else page_A)(path, H, S, B, items, vat)
        truth.append({
            "file": os.path.basename(path),
            "szamlaszam": H["szamla"],
            "kibocsatas_datum": H["kibocs"],
            "teljesites_datum": H["telj"],
            "hatarido": H["hatar"],
            "fizmod": H["fizmod"],
            "elado_nev": S["nev"],
            "elado_adoszam": S["adoszam"],
            "vevo_nev": B["nev"],
            "vevo_adoszam": B["adoszam"],
            "afa_kulcs": vat,
            "netto_osszeg": netto,
            "afa_osszeg": afa,
            "brutto_osszeg": brutto,
            "valuta": "HUF",
            "tetelszam": len(items)
        })
    with open(os.path.join(OUT_DIR,"ground_truth.csv"),"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(truth[0].keys()))
        w.writeheader(); w.writerows(truth)
    print(f"Generated {N_FILES} invoices -> {OUT_DIR}")
    print(f"Ground truth -> {os.path.join(OUT_DIR,'ground_truth.csv')}")

if __name__ == "__main__":
    main()

