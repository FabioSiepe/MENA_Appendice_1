class Domanda:
    def __init__(self, id, domanda, opz1, opz2, opz3, opz4, opzCorrect, difficolta, period):
        self.id = id;
        self.domanda = domanda;
        self.opz1 = opz1;
        self.opz2 = opz2;
        self.opz3 = opz3;
        self.opz4 = opz4;
        self.opzCorrect = opzCorrect;
        self.difficolta = difficolta
        self.period = period;