class Utente:
    def __init__(self,id_telegram, nome, punti, livello, esperienza):
        self.id_telegram = id_telegram
        self.nome = nome
        self.punti = punti
        self.livello = livello
        self.esperienza = esperienza

    def set_punti(self, punti):
        self.punti = punti

    def get_punti(self):
        return self.punti

    def get_nome(self):
        return self.nome

    def __str__(self):
        return self.nome + " " + str(self.punti) + " " + str(self.livello) + " " + str(self.esperienza)