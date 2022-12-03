
def semplice_risposta(testo):
    messaggio = str(testo).lower()

    if messaggio in ("ciao",):
        return "salve"
    if messaggio in ("buonsera",):
        return "sera"

    return "non ho capito"
